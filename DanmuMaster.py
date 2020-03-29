import requests
import os
import re
import time
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as et
import json
import sys
from bs4 import BeautifulSoup

from DanmuSpider import Spider
from DanmuFileTools import *

'''
弹幕格式如下
<时间(秒),样式,字号,颜色,UNIX-time,弹幕池,用户,rowID>
'''


class DanmuMaster(object):
    """
    用于控制弹幕获取的类, 包括历史弹幕和最新弹幕.
    """
    def __init__(self):
        self.no: str = ''  # av/bv/ep 号字符串带前缀.
        self.page: int = 0
        self.url: str = ''
        self.cid: str = "0"
        self.ssid: str = "ss0"
        self.title: str = ''
        self.timeUnix = 0  # 在av/bv号下表示视频上传时间; 在ss/ep号下用于记录爬虫初始化的时间, 为0则还未初始化(此ep还未公布).
        self.timeProgress = 0  # 表示上次成功获取弹幕的unix时间戳
        self.danmu_set = None  # 在av/bv号下表示合并的弹幕集合(暂时), 在ss/ep号下用于记录上一次爬取的弹幕内容,用xml_str来表示.
        self.xmlObj = None
        self.xmlRoot = None
        self.fileName: str = ''
        self.cookie_path: str = ''
        self.ep_series = []

    def init_from_url(self, url: str, cookie_path: str = 'cookie.cfg'):
        """
        使用url初始化分析类
        :param url: 后缀为 "av/bv/ep/ss" + "数字" 的url
        :param cookie_path: 本地保存cookie的目录
        :return: None
        """
        self.url = url
        self.cookie_path = cookie_path
        temp_lst = url.split('/')
        self.danmu_set = []
        if temp_lst[-1][0] in 'aAbB':
            av_info = temp_lst[-1].split('?')
            self.no, self.page = av_info[0], av_info[1] if len(av_info) > 1 else 1
            self._get_info_av(url)
        else:
            self._get_info_ep(url)

    def init_from_av(self, av: str, p: str = '1', cookie_path: str = 'cookie.cfg'):
        """
        使用av号或bv号初始化类
        :param av: av号, 形如 "av314"; bv号, 形如 "BV1aaa411ee1"
        :param p: 分p视频的p号, 默认为1
        :param cookie_path: 本地保存cookie的目录
        :return: None
        """
        ptn_av = re.compile(r'(((av)|(AV))\d+)|(((bv)|(BV))[A-Za-z0-9]+)')
        ptn_p = re.compile(r'[1-9]\d*')
        self.danmu_set = []
        if ptn_av.fullmatch(av) is None:
            print("av号格式错误. 例: 'av1234'")
            exit(1)
        if ptn_p.fullmatch(p) is None:
            print("分p号格式错误,应为纯数字 例: '2'")
            exit(1)
        self.url = "https://www.bilibili.com/" + av
        self.no, self.page, self.cookie_path = av, p, cookie_path
        self._get_info_av(self.url)

    def init_from_ep(self, ep: str, cookie_path: str = 'cookie.cfg'):
        """
        使用ep号或ss号初始化类
        :param ep: ep或ss号 形如 "ep123"或"ss123"
        :param cookie_path: 本地保存cookie的目录
        :return: None
        """
        ptn_ep = re.compile(r'(ss|ep)\d+', re.IGNORECASE)
        self.danmu_set = []
        if ptn_ep.fullmatch(ep) is None:
            print("ep号格式有误, 例: 'ep1234'")
            exit(1)
        self.url = "https://www.bilibili.com/bangumi/play/" + ep
        self._get_info_ep(self.url)
        self.cookie_path = cookie_path

    def init_from_ep_json(self, ep_json: dict, ep_int: int = -1, cookie_path: str = 'cookie.cfg'):
        """
        使用网页返回的json信息初始化类.
        :param ep_json: 番剧的信息, dict类型
        :param cookie_path: 本地保存cookie的目录
        :param ep_int: ep号, 整数型.
        :return: None
        """
        self._resolve_ep_json(ep_json=ep_json, ep_int=ep_int)
        self.cookie_path = cookie_path
        self.danmu_set = None

    def listen_ss(self, p: str, time_str: str, interval_sec: int = 60):
        """
        此函数独立计算等待时间,不与BangumiController.py使用.
        预定时间来滚动获取新番的最新弹幕.
        在初始化时使用同一季的任意一集的url即可.
        如果是已经发布的集数, time_str填写当前时间即可.
        填写时间的目的是为了减少不必要的检查"目标集数是否可用"的次数, 减少被ban的概率.
        对于未来的集数, 脚本会在到时间之后启动, 即使番剧推迟几分钟公开也不会报错.

        在检测到相应的剧集可以观看时开始获取弹幕.
        通过计算相邻两次获取的弹幕增量, 动态调整获取弹幕的时间间隔.
        :param p: 视频分p,即集数,未发布也可(只要在初始化时是处于同一个系列的就可以"
        :param time_str: 视频更新时间,格式为 "yyyy-mm-ddThh:mm",例如 "2020-01-02T03:04"
        :param interval_sec: 每次获取间隔的初始时间, 时间 > 10秒
        :return:
        """
        input_time = None
        interval_sec = max(interval_sec, 11)
        try:
            input_time = datetime.fromisoformat(time_str)
        except Exception as e:
            print("输入的时间字符串有问题:", e)
            exit(1)
        target_time = datetime(input_time.year, input_time.month, input_time.day,
                               hour=input_time.hour, minute=input_time.minute,
                               tzinfo=timezone(timedelta(hours=8)))
        sec_wait = max(11, int(target_time.timestamp()) - int(time.time()))
        print("wait:", sec_wait, "seconds")
        time.sleep(sec_wait - 10)

        # 循环监测视频是否可用
        while True:
            url = "https://www.bilibili.com/bangumi/play/" + self.ssid
            response = Spider.get_html(url)
            ep_json = self.get_epinfo_in_html(response)
            new_series = ep_json['epList']
            if len(new_series) >= int(p):
                print("符合条件开始获取")
                time.sleep(5)
                target_ep = new_series[int(p)-1]["id"]
                new_url = "https://www.bilibili.com/bangumi/play/ep" + str(target_ep)
                self._get_info_ep(new_url)
                break
            print("未找到相应剧集,等待", interval_sec, "秒")
            time.sleep(interval_sec)

        previous_danmu = None
        while True:
            content_bytes = Spider.get_current_danmu(self.cid, self.url)
            now = datetime.fromtimestamp(time.time(), timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
            print(now, "获取了弹幕")
            with open(self.fileName + '_latest_' + str(int(time.time())) + '.xml', 'wb') as f:
                f.write(content_bytes)
            danmu = DanmuFile.init_from_str(content_bytes.decode('utf-8'))
            if previous_danmu is not None:
                _, inc, _ = DanmuCombinator.diff(previous_danmu, danmu)
                ratio = len(inc) / int(danmu.max_limit)
                print("时间比例:", ratio, )
                if ratio > 0.5:
                    interval_sec = int(interval_sec / 5)
                    print("时间间隔修改为:", interval_sec)
                if ratio < 0.3:
                    interval_sec = min(int(interval_sec * 1.5), 1800)
                    print("时间间隔修改为:", interval_sec)
            previous_danmu = danmu
            time.sleep(int(interval_sec))

    def listen_ss_once(self):
        content_bytes = Spider.get_current_danmu(self.cid, self.url)
        now = datetime.fromtimestamp(time.time(), timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
        print(now, self.title, "获取了弹幕:",)
        with open(self.fileName + '_latest_' + str(int(time.time())) + '.xml', 'wb') as f:
            f.write(content_bytes)
        danmu = DanmuFile.init_from_str(content_bytes.decode('utf-8'))
        ratio = -1
        if self.danmu_set is not None:
            _, inc, _ = DanmuCombinator.diff(self.danmu_set, danmu)
            ratio = len(inc) / int(danmu.max_limit)
            print("\t时间比例:", ratio, )
        else:
            print("首次获取",)
        self.danmu_set = danmu
        self.timeProgress = int(time.time())
        return ratio


    def pre_init_from_ep_json(self, ep: dict, ss_id: str):
        """
        从新番列表的信息中预先初始化爬虫.
        :param ep: 新番列表中 "session" 的某一项.
        :param ss_id: 番剧的系列的id
        :return: None
        """
        self.no = 'ep' + str(ep['ep_id'])
        self.url = "https://www.bilibili.com/bangumi/play/" + self.no
        self.ssid = ss_id

    def check_ep_exist(self):
        response = Spider.get_html(self.url)
        if response is None:
            print("未获取到:", self.title,)
            return False
        ep_json = self.get_epinfo_in_html(response)
        ep_int = int(self.no[2:])
        new_series = ep_json['epList']
        for ep in new_series:
            if ep['ep_id'] == ep_int:
                self.init_from_ep_json(ep_json, ep_int, self.cookie_path)
                return True
        return False


    def all_danmu(self):
        """
        获取当前弹幕和历史弹幕
        :return:
        """
        # get cid, time, title
        overall = 0
        self._get_current_danmu()

        try:
            xml_file = open(self.fileName+'.xml', 'rt', encoding='utf-8')
            self.xmlObj = et.parse(xml_file)
            xml_file.close()
        except Exception as e:
            print("读取本地弹幕文件失败, 信息如下\n", e)
        self.xmlRoot = self.xmlObj.getroot()

        for danmu in self.xmlRoot.findall('d'):
            danmu_info = danmu.attrib['p'].split(',')
            self.danmu_set.append(danmu_info[7])
            overall += 1

        print("实时弹幕共有", overall, "个, 开始抓取历史弹幕")
        self.timeProgress = int(time.time())
        progress_time_bj = datetime.fromtimestamp(self.timeProgress, timezone(timedelta(hours=8)))
        progress_date_str = datetime.strftime(progress_time_bj, "%Y-%m-%d")

        req_date_str = datetime.strftime(
            datetime.fromtimestamp(int(time.time()), timezone(timedelta(hours=8))),
            "%Y-%m-%d"
        )
        pub_time_bj = datetime.fromtimestamp(self.timeUnix, timezone(timedelta(hours=8)))
        pub_date_str = datetime.strftime(pub_time_bj, "%Y-%m-%d")

        history_month_info = None
        history_month_list = []

        current_danmu = []
        flag_zero = 0
        while progress_time_bj > pub_time_bj:
            count = 0  # 统计本次返回的与已有弹幕 rowID 不重复的弹幕数量
            amount = 0  # 统计本次返回的弹幕总数量, 若小于弹幕池限制则可以判定抓取完毕
            req_date_str = progress_date_str
            xml_str = self._get_history_danmu(req_date_str)
            root = DanmuFile.init_from_str(xml_str).xml_root
            # 如果cookie失效会在这里报错

            earliest = self.timeProgress
            for danmu in root.findall('d'):
                amount += 1
                danmu_info = danmu.attrib['p'].split(',')
                if danmu_info[7] not in self.danmu_set:
                    self.xmlRoot.append(danmu)
                    current_danmu.append(danmu_info[7])
                    count += 1
                danmu_time = int(danmu_info[4])
                if danmu_time < earliest:
                    earliest = danmu_time

            self.danmu_set = current_danmu
            current_danmu = []
            print('本次插入', count, '条弹幕')
            overall += count
            progress_time_bj = datetime.fromtimestamp(earliest, timezone(timedelta(hours=8)))
            progress_date_str = datetime.strftime(progress_time_bj, "%Y-%m-%d")

            # 如果当天弹幕量超过弹幕池上限,则最早的弹幕的发布时间还是当天,
            # 因此需要查找上一天是否有弹幕(若无弹幕请求,会出错)
            if progress_date_str == req_date_str:
                oneday = timedelta(days=1)
                test_datetime = progress_time_bj - oneday
                test_date_str = datetime.strftime(test_datetime, "%Y-%m-%d")

                # TODO: bug fix "status_code=500"
                # while test_datetime>pub_time_bj:
                #     if test_date_str[:-3] != history_month_info:
                #         history_month_info = test_date_str[:-3]
                #         json_str = self._get_history_month(history_month_info)
                #         if json.loads(json_str)['code'] != 0:
                #             self.xmlObj.write(self.fileName + '.xml', encoding='utf-8')
                #         history_month_list = json.loads(json_str)['data']
                #
                #     if test_date_str in history_month_list:
                #         break
                #     else:
                #         test_datetime = test_datetime - oneday
                progress_time_bj = test_datetime
                progress_date_str = test_date_str
            req_date_str = progress_date_str
            self.timeProgress = self._write_record(datetime.timestamp(progress_time_bj))

            # 获取到的弹幕数量小于弹幕池上限说明到头了
            if int(root.find('maxlimit').text) > amount > 0:
                print("弹幕数", amount, "少于上限且不为零, 可结束获取.")
                break

            if flag_zero > 5:
                print("连续五天无获得弹幕,终止获取.")
                break

            if amount == 0:
                flag_zero += 1

        self.xmlObj.write(self.fileName+'.xml', encoding='utf-8')

        # 由于XMLElementTree.write()的xml_declaration参数在弹幕播放器无法识别 (它多了一个回车符合,并且字符串是单引号)
        # 因此手动添加 (不添加则弹幕播放器无法识别)
        with open(self.fileName + '.xml', 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write('<?xml version="1.0" encoding="UTF-8"?>' + content)
        print("一共存储了", overall, "条弹幕")


    def _write_record(self, progress_time):
        # TODO: bug fix "require bytes not str"
        # record = {
        #     'av': self.no,
        #     'page': self.page,
        #     'url': self.url,
        #     'cid': self.cid,
        #     'title': self.title,
        #     'timeUnix': self.timeUnix,
        #     'timeProgress': progress_time,
        #     'fileName': self.fileName
        # }
        # with open(self.fileName+'.json', 'wb') as dump_file:
        #     json.dump(record, dump_file)
        # print("record saved:", record)
        return progress_time

    def resume_record(self, path: str):
        with open(path, 'rb') as load_file:
            record = json.load(load_file)
            self.no = record['av']
            self.page = record['page']
            self.url = record['url']
            self.cid = record['cid']
            self.title = record['title']
            self.timeUnix = record['timeUnix']
            self.timeProgress = record['timeProgress']
            self.fileName = record['fileName']

    def _get_current_danmu(self):
        content_bytes = Spider.get_current_danmu(self.cid, self.url)

        # 将要与历史弹幕整合的弹幕文件
        with open(self.fileName+'.xml', 'wb') as f:
            f.write(content_bytes)
        # 当前弹幕池(上限数量)的弹幕
        with open(self.fileName+'_latest.xml', 'wb') as f:
            f.write(content_bytes)

    def _get_history_danmu(self, date: str):
        """
        send history danmu request in specific date_str, return xml_str
        :param date: date string in 'YYYY-MM-DD' format
        :return: xml string in UTF-8 encoding
        """
        content_bytes = Spider.get_history_danmu(self.cid, self.url, date, self.cookie_path)
        xml_str = content_bytes.decode('utf-8')
        with open(self.fileName + '_' + date + '.xml', 'wb') as f:
            f.write(content_bytes)
        print('data length', len(xml_str))
        return xml_str

    def _get_history_month(self, month: str):
        content_bytes = Spider.get_history_month(self.cid, self.url, month, self.cookie_path)
        json_str = content_bytes.decode('utf-8')
        return json_str

    def _get_info_av(self, url: str):
        html = Spider.get_html(url)
        pattern = re.compile(r'"cid":(\d+),"page":%s' % self.page)
        pattern1 = re.compile(r'"title":"(.*?)","pubdate":(\d+)')
        self.cid = re.search(pattern, html).group(1)
        self.title, timeUnix_str = re.search(pattern1, html).groups()
        self.timeUnix = int(timeUnix_str)
        folder = "harvest/" + self.no + '_' + self.title + "/"
        if not os.path.exists(folder):
            os.mkdir(folder)
        self.fileName = folder + self.no + '_' + self.title + '_p' + str(self.page)

    # 番剧没有视频发布时间,需要通过获取 历史弹幕月 来确定历史弹幕停止时间
    def _get_info_ep(self, url: str,):
        html = Spider.get_html(url)

        ep_json = self.get_epinfo_in_html(html)
        self._resolve_ep_json(ep_json)


    def _resolve_ep_json(self, ep_json: dict, ep_int:int = -1):
        bangumi = ep_json['epInfo']
        self.ep_series = ep_json['epList']

        # url后缀为ss番号时, epInfo为空,需要去列表里面找第一项(网页端自动显示第一项)
        if ep_json['epInfo']['loaded'] is False:
            if ep_int < 0:
                bangumi = ep_json['epList'][0]
            else:
                for item in ep_json['epList']:
                    if item['id'] == ep_int:
                        bangumi = item
                        break
        # print(ep_json)
        self.cid = str(bangumi['cid'])
        self.no = 'ep' + str(bangumi['id'])
        self.title = ep_json['mediaInfo']['title'] + ':' + bangumi['titleFormat'] + ' ' + bangumi['longTitle']
        self.timeUnix = time.time()
        self.ssid = "ss" + str(ep_json['mediaInfo']['ssId'])
        self.page = bangumi['title']
        folder = "harvest/" + self.ssid + '_' + ep_json['mediaInfo']['title'] + "/"
        if not os.path.exists(folder):
            os.mkdir(folder)
        self.fileName = folder + self.no + '_' + self.title + '_p' + self.page

    @staticmethod
    def get_epinfo_in_html(html):
        soup = BeautifulSoup(html, features="html.parser")
        tag_list = soup.find_all("script")
        ep_json_str = None
        for item in tag_list:
            if r"__INITIAL_STATE__" in item.text:
                index_start = item.text.find('=')
                index_end = item.text.find(';')
                ep_json_str = item.text[index_start + 1:index_end]
                break
        ep_json = json.loads(ep_json_str)
        return ep_json


if __name__ == '__main__':
    target = ''
    if len(sys.argv) < 2:
        target = 'https://www.bilibili.com/video/av10429'  # 将你的网址粘贴在这里
    else:
        target = sys.argv[1]
    print('开始分析', target)
    dm = DanmuMaster()
    dm.init_from_url(target)
    dm.all_danmu()

