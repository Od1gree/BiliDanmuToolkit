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
    def __init__(self):
        self._bangumi_map: dict = {}  # K为番剧ssid, v为已经纳入队列的列表
        self._next_update: dict = {}
        self._cookie_path: str = ''
        self._queue: TaskQueue = TaskQueue()

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
        content = ""
        try:
            f = open(path, 'rt')
            content = f.readlines()
            f.close()
        except Exception as e:
            print("读取番剧列表文件失败")

        pattern = re.compile(r'^(ss\d+)\s+(\d+)$')
        for line in content:
            if line[0] is '#':
                continue
            result = pattern.match(line)
            ss_id = result.group(1)
            priority = int(result.group(2))
            url = 'https://www.bilibili.com/bangumi/play/' + ss_id
            html = Spider.get_html(url)
            ep_json = DanmuMaster.get_epinfo_in_html(html)
            bangumi_list = []
            for ep in ep_json['epList']:
                ep_int = ep['id']
                task = DanmuMaster()
                task.init_from_ep_json(ep_json, ep_int)
                self._queue.add_task(task, int(time.time()), priority)
                bangumi_list.append(task)
            self._bangumi_map[ss_id] = bangumi_list


    def _resolve_json(self):
        bangumi_json = json.loads(Spider.get_bangumi_timeline().decode('utf-8'))

        index = 0
        today_str = Listener._utime_to_date()

        # 跳过已经发布的日期
        for days in bangumi_json['result']:
            if days['date'] is today_str:
                break
            else:
                index += 1

        try:
            assert self._bangumi_map
        except AssertionError:
            print("番剧列表为空")
            exit(1)

        for single_day in bangumi_json['result'][index:index+8]:
            for bangumi in single_day['seasons']:
                url = bangumi['url']
                ss_id = url.split('/')[-1]
                if ss_id in self._bangumi_map:
                    if self._bangumi_map[ss_id] is None and bangumi['is_published'] is 0:
                        self._bangumi_map[ss_id] = DanmuMaster().init_from_url(url, self._cookie_path)
                        self._next_update[ss_id] = bangumi['pub_ts']

    @staticmethod
    def _utime_to_date(unix_time: int = time.time()) -> str:
        """
        将unix时间戳变为 m-d 格式, 个位日期和月份前面没有0
        :param unix_time: int型unix时间戳, 按秒计.
        :return: 时间字符串
        """
        dt = datetime.fromtimestamp(unix_time, timezone(timedelta(hours=8)))
        return str(dt.month) + '-' + str(dt.day)
