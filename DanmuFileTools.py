import xml.etree.ElementTree as et
from typing import List
import time
import html


# 弹幕格式[0 时间(秒),1 样式,字号,2 颜色,3 UNIX-time,4 弹幕池,5 用户,6 rowID, 7 弹幕内容]
class Danmu(object):
    """
    Danmu类存储了弹幕的基本信息, xml格式的弹幕信息排列方式如下
    <d p="0 时间(秒),1 样式,字号,2 颜色,3 UNIX-time,4 弹幕池,5 用户,6 rowID"> 7 弹幕内容</d>
    """
    def __init__(self, text: str, info: str):
        """
        使用xml格式字符串初始化Danmu类.

        形如 '<d p="...">弹幕text</d>'
        :param text: 弹幕内容
        :param info: 弹幕附属信息,也就是p的内容
        """
        self.text = text
        try:
            [self.index, self.style, self.fontsize, self.color,
             self.unix_time, self.pooltype, self.user, self.rowid] = info.split(',')
        except Exception as e:
            print('error reading information of danmu:', e)

    def to_str(self):
        """
        输出为xml格式的弹幕字符串
        :return: 字符串
        """
        text = '<d p="' \
               + self.index + ',' \
               + self.style + ',' \
               + self.fontsize + ',' \
               + self.color + ',' \
               + self.unix_time + ',' \
               + self.pooltype + ',' \
               + self.user + ',' \
               + self.rowid + '">' \
               + html.escape(self.text) + '</d>'
        return text




class DanmuFile(object):
    def __init__(self, root: et.Element = None, summary: bool = False):
        """
        使用python内置的etree.ElementTree.Element来初始化, 一般不作为外部调用使用
        :param root:
        :param summary: 打印统计信息
        """
        try:
            assert root
        except AssertionError:
            print("elementTree对象根节点为None, 请使用 init_from_file() 或 init_from_str()方法初始化")
            exit(1)
        self.xml_root: et.Element = root

        # 弹幕文件头部信息, 不读取<source>标签是因为有的文件没有.
        self.chat_server: str = self.xml_root.find('chatserver').text
        self.chat_id: str = self.xml_root.find('chatid').text
        self.mission: str = self.xml_root.find('mission').text
        self.max_limit: str = self.xml_root.find('maxlimit').text
        self.state: str = self.xml_root.find('state').text
        self.real_name: str = self.xml_root.find('real_name').text

        # 字典形势存储的弹幕, K: rowID, V: Danmu类
        self._danmu_dict = {}
        # 弹幕总数
        self.count = 0
        # 弹幕位置统计
        self.style = {str(i): 0 for i in range(1, 9)}  # 1-3滚动, 4底端, 5顶端, 6逆向, 7定位, 8高级
        # 弹幕池分类统计
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
    def init_from_file(path: str = None, summary: bool = False):
        """
        从xml文件生成DanmuFile类.
        :param path: 路径
        :param summary: 是否打印统计信息
        :return: DanmuFile类
        """
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
    def init_from_str(xml_str: str, summary: bool = False):
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

    def combine(self, danmu_ext):
        """
        从 DanmuFile 中合并弹幕
        :param danmu_ext: 需要合并的弹幕文件
        :return: None
        """
        dict_ext = danmu_ext.get_dic()
        for rowid in dict_ext:
            if self._danmu_dict.get(rowid):
                continue
            else:
                danmu = dict_ext[rowid]
                self._danmu_dict[rowid] = danmu
                self.count += 1
                self.style[danmu.style] += 1
                self.pool[danmu.pooltype] += 1

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
        """
        输出为xml文件, 不检查文件存在, 直接写覆盖.
        :param path: 文件路径
        :return: 文件写入是否成功
        """
        try:
            f = open(path, "w")
            f.write(self.to_str())
        except Exception as e:
            print("写入xml文件错误", e)
            return False
        return True

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
    def diff(dm1: DanmuFile, dm2: DanmuFile, is_print: bool = False) -> (dict, dict, dict):
        """
        比较两个弹幕文件的相同和不同
        :param dm1: DanmuFile类
        :param dm2: DanmuFile类
        :param is_print: 是否在函数中直接打印比对结果
        :return: (文件1独有, 文件2独有, 共有)
        """
        dic1, dic2, common = DanmuCombinator._xor(dm1.get_dic(), dm2.get_dic())
        len1 = len(dic1)
        len2 = len(dic2)
        len_common = len(common)
        if is_print:
            print("文件1独有", len1, end=' ')
            print("文件2独有", len2, end=' ')
            print("二者共有", len_common)
        return dic1, dic2, common

    @staticmethod
    def combine(dm_list: List[DanmuFile]) -> dict:
        comb = {}
        for item in dm_list:
            comb.update(item.get_dic())
        return comb

    @staticmethod
    def _xor(dic1: dict, dic2: dict) -> (dict, dict, dict):
        common = {}
        d1 = dic1.copy()
        d2 = dic2.copy()
        for item in dic1:
            if item in dic2:
                d2.pop(item)
                common[item] = d1[item]
                d1.pop(item)

        return d1, d2, common
