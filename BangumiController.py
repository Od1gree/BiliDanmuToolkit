import json
import time
from datetime import datetime, timedelta, timezone

from DanmuSpider import *
from DanmuMaster import *
from utility import *


class Listener(object):
    """
    实时获取指定番剧系列的弹幕.
    """
    TYPE_BANGUMI = 1
    TYPE_REFRESH = 2
    TYPE_GETLIST = 3

    def __init__(self, default_delay: int = 30, max_delay: int = 5400):
        self._bangumi_map: dict = {}  # K为番剧ssid, v为已经纳入队列的列表
        self._next_update: dict = {}
        self._cookie_path: str = ''
        self._config_path: str = ''
        self._queue: TaskQueue = TaskQueue()
        self._priority_dict: dict = {}
        self._default_delay = default_delay  # 初次获取后等待的时间
        self._max_delay = max_delay  # 延时最大值

    def init_from_list(self, ss_list: list, cookie_path: str = 'cookie.cfg'):
        """
        收集将要获取的番剧的信息
        :param ss_list: 番剧字符串列表, 每个元素格式为: "ss1234"
        :param cookie_path:
        :return:
        """
        self._cookie_path = cookie_path
        for item in ss_list:
            self._bangumi_map[item] = None

    def init_from_file(self, path: str = 'bangumi.cfg'):
        self._config_path = path
        self._read_config()
        for ss_id, priority in self._priority_dict.items():
            url = 'https://www.bilibili.com/bangumi/play/' + ss_id
            html = Spider.get_html(url)
            ep_json = DanmuMaster.get_epinfo_in_html(html)
            bangumi_list = []
            for ep in ep_json['epList']:
                ep_int = ep['id']
                task = DanmuMaster()
                task.init_from_ep_json(ep_json, ep_int)
                self._queue.add_task(task, int(time.time()), priority, Listener.TYPE_BANGUMI)
                bangumi_list.append(task)
            self._bangumi_map[ss_id] = bangumi_list

        self._exec_getlist_task()

    def start(self):
        while True:
            current_task = self._queue.pop_task()
            now_int = int(time.time())
            distance = current_task.utime - now_int
            if distance < 1:
                print("\n立即开始下一个任务")
                pass
            else:
                print("\n休息", distance, "秒")
                time.sleep(distance)
            if current_task.node_type is Listener.TYPE_BANGUMI:
                current_task = self._exec_bangumi_task(current_task)
            elif current_task.node_type is Listener.TYPE_REFRESH:
                current_task = self._exec_refresh_task(current_task)
            self._queue.return_task(current_task)

    def _exec_bangumi_task(self, task: TaskNode):
        bangumi:DanmuMaster = task.content
        prev_time = bangumi.timeProgress
        ratio = bangumi.listen_ss_once()
        task.utime = self._calc_delay_sec(prev_time, ratio)
        return task

    def _exec_refresh_task(self, task: TaskNode):
        bangumi:DanmuMaster = task.content
        if bangumi.check_ep_exist():
            bangumi.listen_ss_once()
            task.node_type = Listener.TYPE_BANGUMI
            self._next_update.pop(bangumi.ssid)
        task.utime = int(time.time()) + self._default_delay
        return task

    def _exec_getlist_task(self):
        for timeline in ['timeline_global', 'timeline_cn']:
            bangumi_json = json.loads(Spider.get_bangumi_timeline(timeline).decode('utf-8'))
            self._resolve_json(bangumi_json)

    def _calc_delay_sec(self, prev_time: int, ratio: float):
        current_time = int(time.time())
        if prev_time == 0:
            return current_time + self._default_delay
        time_delta = current_time - prev_time

        # 避免因清晨到早上弹幕量暴涨而遗漏
        current_hour = self._utime_to_hour()
        if 1 < current_hour < 7:
            ratio *= (1 + current_hour*0.3)

        # 弹幕比例0.2时时间不变
        if ratio > 0.9:
            calc_delta = min(time_delta * 0.1, self._default_delay)
        elif 0.6 < ratio <= 0.9:
            calc_delta = time_delta / (ratio*5)
        elif 0.3 < ratio <= 0.6:
            calc_delta = time_delta / (ratio*1.5 + 1)
        elif 0.1 < ratio <= 0.3:
            calc_delta = time_delta / (ratio + 0.8)
        else:
            calc_delta = time_delta * 3 * (1-ratio*6)

        print(calc_delta, "秒之后再次获取")
        return current_time + int(calc_delta)

    def _resolve_json(self, bangumi_json: dict):
        index = 0
        today_str = Listener._utime_to_date()

        # 跳过已经发布的日期
        for days in bangumi_json['result']:
            if days['date'] == today_str:
                break
            else:
                index += 1

        try:
            assert self._bangumi_map
        except AssertionError:
            print("番剧列表为空")
            exit(1)
        now_int = int(time.time())
        for single_day in bangumi_json['result'][index:index+8]:
            for bangumi in single_day['seasons']:
                url = bangumi['url']
                ss_id = url.split('/')[-1]
                if ss_id in self._bangumi_map:
                    if ss_id not in self._next_update and bangumi['is_published'] is 0:
                        task = DanmuMaster()
                        task.pre_init_from_ep_json(bangumi, ss_id)
                        self._next_update[ss_id] = task
                        self._queue.add_task(task, bangumi['pub_ts'], self._priority_dict[ss_id], Listener.TYPE_REFRESH)

        self._queue.add_task(None, utime=now_int + 3600*24*6, priority=1, node_type=Listener.TYPE_GETLIST)

    def _read_config(self):
        content = ""
        try:
            f = open(self._config_path, 'rt')
            content = f.readlines()
            f.close()
        except Exception as e:
            print("读取番剧列表文件失败")

        pattern = re.compile(r'^(ss\d+)\s+(\d+)$')
        for line in content:
            if line[0] is '#':
                continue

            result = pattern.match(line)
            if result is None:
                continue
            ss_id = result.group(1)
            priority = int(result.group(2))
            self._priority_dict[ss_id] = priority


    @staticmethod
    def _utime_to_date(unix_time: int = time.time()) -> str:
        """
        将unix时间戳变为 m-d 格式, 个位日期和月份前面没有0
        :param unix_time: int型unix时间戳, 按秒计.
        :return: 时间字符串
        """
        dt = datetime.fromtimestamp(unix_time, timezone(timedelta(hours=8)))
        return str(dt.month) + '-' + str(dt.day)

    @staticmethod
    def _utime_to_hour(unix_time: int = time.time()) -> int:
        """
        获得unix时间的小时数字.
        :param unix_time: int型unix时间戳, 按秒计.
        :return: unix时间所在的小时数字.
        """
        dt = datetime.fromtimestamp(unix_time, timezone(timedelta(hours=8)))
        return dt.hour


