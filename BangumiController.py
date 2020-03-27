import json
import time
from datetime import datetime, timedelta, timezone

from DanmuSpider import *
from DanmuMaster import *


class Listener(object):
    """
    实时获取指定番剧系列的弹幕.
    """
    def __init__(self):
        self._bangumi_list: dict = {}
        self._next_update: dict = {}
        self._cookie_path: str = ''
        self._resolve_json()

    def init_from_list(self, ss_list: list, cookie_path: str = 'cookie.cfg'):
        """
        收集将要获取的番剧的信息
        :param ss_list: 番剧字符串列表, 每个元素格式为: "ss1234"
        :param cookie_path:
        :return:
        """
        self._cookie_path = cookie_path
        for item in ss_list:
            self._bangumi_list[item] = None

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
            assert self._bangumi_list
        except AssertionError:
            print("番剧列表为空")
            exit(1)

        for single_day in bangumi_json['result'][index:index+8]:
            for bangumi in single_day['seasons']:
                url = bangumi['url']
                ss_id = url.split('/')[-1]
                if ss_id in self._bangumi_list:
                    if self._bangumi_list[ss_id] is None and bangumi['is_published'] is 0:
                        self._bangumi_list[ss_id] = DanmuMaster().init_from_url(url, self._cookie_path)
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
