import requests
import os
import re
import time
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as et
import json
import sys

from DanmuSpider import Spider

'''
弹幕格式如下
<时间(秒),样式,字号,颜色,UNIX-time,弹幕池,用户,rowID>
'''

class Danmu(object):
    def __init__(self):
        self.av = ''
        self.page = 0
        self.url = ''
        self.cid = "0"
        self.title = ''
        self.timeUnix = 0
        self.timeProgress = 0
        self.danmuSet = []
        self.xmlObj = None
        self.xmlRoot = None
        self.fileName = ''
        self.cookie_path = ''

    def from_url(self, url: str, cookie_path: str = 'cookie.cfg'):
        self.url = url
        self.cookie_path = cookie_path
        temp_lst = url.split('/')[-1].split('?')
        self.av = temp_lst[0]
        if len(temp_lst) is 1:
            self.page = 1
        else:
            self.page = int(temp_lst[1][2:])

        self._get_info(url)

        self._all_danmu()

    def _all_danmu(self):
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
            self.danmuSet.append(danmu_info[7])
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
        while progress_time_bj > pub_time_bj:
            count = 0  # 统计本次返回的与已有弹幕 rowID 不重复的弹幕数量
            amount = 0  # 统计本次返回的弹幕总数量, 若小于弹幕池限制则可以判定抓取完毕
            req_date_str = progress_date_str
            xml_str = self._get_history_danmu(req_date_str)
            root = et.fromstring(xml_str)
            earliest = self.timeProgress
            for danmu in root.findall('d'):
                amount += 1
                danmu_info = danmu.attrib['p'].split(',')
                if danmu_info[7] not in self.danmuSet:
                    self.xmlRoot.append(danmu)
                    current_danmu.append(danmu_info[7])
                    count += 1
                danmu_time = int(danmu_info[4])
                if danmu_time < earliest:
                    earliest = danmu_time

            self.danmuSet = current_danmu
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
            if amount < int(root.find('maxlimit').text) and amount > 0:
                print("弹幕数", amount, "少于上限且不为零, 可结束获取.")
                break

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
        #     'av': self.av,
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
            self.av = record['av']
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



    def _get_info(self, url: str):
        html = Spider.get_html(url)
        pattern = re.compile(r'"cid":(\d+),"page":%s' % self.page)
        pattern1 = re.compile(r'"title":"(.*?)","pubdate":(\d+)')
        self.cid = re.search(pattern, html).group(1)
        self.title, timeUnix_str = re.search(pattern1, html).groups()
        self.timeUnix = int(timeUnix_str)
        folder = "harvest/" + self.av + '_' + self.title + "/"
        if not os.path.exists(folder):
            os.mkdir(folder)
        self.fileName = folder + self.av + '_' + self.title + '_p' + str(self.page)



if __name__=='__main__':
    target = ''
    if len(sys.argv)<2:
        target = 'https://www.bilibili.com/video/av314'  # 将你的网址粘贴在这里
    else:
        target = sys.argv[1]
    print('开始分析', target)
    dm = Danmu()
    dm.from_url(target)

