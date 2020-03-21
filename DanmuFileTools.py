import xml.etree.ElementTree as et
import time


# 弹幕格式[0 时间(秒),1 样式,字号,2 颜色,3 UNIX-time,4 弹幕池,5 用户,6 rowID, 7 弹幕内容]
class Danmu(object):
    def __init__(self, text: str, info: str):
        self.text = text
        try:
            [self.index, self.style, self.fontsize, self.color,
             self.unix_time, self.pooltype, self.user, self.rowid] = info.split(',')
        except Exception as e:
            print('error reading information of danmu:', e)

    def to_str(self):
        text = '<d p="' \
               + self.index + ',' \
               + self.style + ',' \
               + self.fontsize + ',' \
               + self.color + ',' \
               + self.unix_time + ',' \
               + self.pooltype + ',' \
               + self.user + ',' \
               + self.rowid + '">' \
               + self.text + '</d>'
        return text




class DanmuFile(object):
    def __init__(self, root: et.Element = None, summary: bool = False):
        try:
            assert root
        except AssertionError:
            print("elementTree对象根节点为None")
            exit(1)
        self.xml_root: et.Element = root
        head_info = []
        for item in self.xml_root:
            head_info.append(item.text)
        self.chat_server: str = self.xml_root.find('chatserver').text
        self.chat_id: str = self.xml_root.find('chatid').text
        self.mission: str = self.xml_root.find('mission').text
        self.max_limit: str = self.xml_root.find('maxlimit').text
        self.state: str = self.xml_root.find('state').text
        self.real_name: str = self.xml_root.find('real_name').text

        self._danmu_dict = {}
        self.count = 0
        self.style = {str(i): 0 for i in range(1, 9)}  # 1-3滚动, 4底端, 5顶端, 6逆向, 7定位, 8高级
        self.pool = {str(i): 0 for i in range(0, 3)}  # 0普通, 1字幕, 2高级

        for item in self.xml_root.findall('d'):
            danmu: Danmu = Danmu(item.text, item.attrib['p'])
            self._danmu_dict[danmu.rowid] = danmu
            self.count += 1
            self.style[danmu.style] += 1
            self.pool[danmu.pooltype] += 1
        if summary:
            self.summary()

    def get_dic(self):
        return self._danmu_dict.copy()

    @staticmethod
    def from_file(path: str = None, summary: bool = False):
        xml_obj = None
        try:
            xml_file = open(path, 'rt', encoding='utf-8')
            xml_obj = et.parse(xml_file)
            xml_file.close()
        except Exception as e:
            print("读取本地弹幕文件失败, 信息如下\n", e)
            exit(1)
        xml_root = xml_obj.getroot()
        return DanmuFile(root=xml_root, summary=summary)

    @staticmethod
    def from_str(xml_str: str, summary: bool = False):
        """
        从xml格式的字符串生成DanmuFile类.
        注意str需要为unicode.
        :param xml_str: unicode格式字符串
        :param summary: 是否打印弹幕文件统计信息
        :return: DanmuFile类
        """
        root = None
        try:
            root = et.fromstring(xml_str)
        except Exception as e:
            print("xml字符串有误:", e, "\nxml内容如下:", xml_str)
            exit(1)
        return DanmuFile(root=root, summary=summary)

    def to_str(self):
        head = u'<?xml version="1.0" encoding="UTF-8"?>' \
               u'<i><chatserver>' + self.chat_server + \
               u'</chatserver><chatid>' + self.chat_id + \
               u'</chatid><mission>' + self.mission + \
               u'</mission><maxlimit>' + self.max_limit + \
               u'</maxlimit><state>' + self.state + \
               u'</state><real_name>' + self.real_name + \
               u'</real_name>'
        body = ""
        for item in self._danmu_dict:
            body += self._danmu_dict[item].to_str()
        tail = "</i>"
        return head + body + tail

    def get_time_range(self, check_type: str = 'normal') -> (int, int):
        """
        获取弹幕日期范围.
        :param check_type: 'normal'表示普通弹幕, 'all'表示所有弹幕
        :return: unix时间戳 (earliest: int, latest: int)
        """
        latest = 0
        earliest = time.time()
        check_level = 5
        if check_type is 'all':
            check_level = 8
        for item in self._danmu_dict:
            danmu = self._danmu_dict[item]
            danmu_time = int(danmu.unix_time)
            danmu_style = int(danmu.style)
            if danmu_style <= check_level:
                if latest < danmu_time:
                    latest = danmu_time
                if earliest > danmu_time:
                    earliest = danmu_time

        return earliest, latest

    def export(self, path: str):
        f = open(path, "w")
        f.write(self.to_str())

    def summary(self):
        print("弹幕池最大容量", self.max_limit)
        print('共有', self.count, '条弹幕')
        self._print_pool()
        self._print_stype()

    def _print_pool(self):
        print("\n弹幕池统计如下:")
        print('普通弹幕', self.pool['0'], "条")
        print('字幕弹幕', self.pool['1'], "条")
        print('高级弹幕', self.pool['2'], "条")

    def _print_stype(self):
        print("\n弹幕类型统计如下:")
        print("滚动弹幕", self.style['1'] + self.style['2'] + self.style['3'], "条")
        print("底端弹幕", self.style['4'], "条")
        print("顶端弹幕", self.style['5'], "条")
        print("逆向弹幕", self.style['6'], "条")
        print("高级弹幕", self.style['7'], "条")
        print("代码弹幕", self.style['8'], "条")


class DanmuCombinator(object):

    @staticmethod
    def diff(dm1: DanmuFile, dm2: DanmuFile):
        dic1, dic2, common = DanmuCombinator._xor(dm1.get_dic(), dm2.get_dic())
        len1 = len(dic1)
        len2 = len(dic2)
        len_common = len(common)
        print("文件1独有", len1)
        print("文件2独有", len2)
        print("二者共有", len_common)
        return len1, len2, len_common

    @staticmethod
    def combine(dm1: dict, dm2: dict, force: bool = False):
        comb = {}
        comb.update(dm1)
        comb.update(dm2)
        return comb

    @staticmethod
    def _xor(dic1: dict, dic2: dict):
        common = {}
        d1 = dic1.copy()
        d2 = dic2.copy()
        for item in dic1:
            if item in dic2:
                d2.pop(item)
                common[item] = d1[item]
                d1.pop(item)

        return d1, d2, common
