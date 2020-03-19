import xml.etree.ElementTree as et
import sys


class Danmu(object):
    def __init__(self, text: str, info: str):
        self.text = text
        try:
            [self.index, self.style, self.fontsize, self.color,
             self.unix_time, self.pooltype, self.user, self.rowid] = info.split(',')
        except Exception as e:
            print('error reading information of danmu:', e)




class DanmuFileReader(object):
    def __init__(self, path: str = None, summary: bool = True):
        self.path = path
        try:
            xml_file = open(self.path, 'rt', encoding='utf-8')
            self.xmlObj = et.parse(xml_file)
            xml_file.close()
        except Exception as e:
            print("读取本地弹幕文件失败, 信息如下\n", e)
        self.xmlRoot = self.xmlObj.getroot()
        self.maxLimit = int(self.xmlRoot.find('maxlimit').text)

        # danmuSet每一项 K:V 格式如下
        # rowID: [0 时间(秒),1 样式,字号,2 颜色,3 UNIX-time,4 弹幕池,5 用户,6 rowID, 7 弹幕内容]
        self.danmuSet = {}
        self.count = 0
        self.style = {str(i): 0 for i in range(1, 9)}  # 1-3滚动, 4底端, 5顶端, 6逆向, 7定位, 8高级
        self.pool = {str(i): 0 for i in range(0, 3)}  # 0普通, 1字幕, 2高级

        for danmu in self.xmlRoot.findall('d'):
            danmu_info = danmu.attrib['p'].split(',')
            danmu_info.append(danmu.text)
            self.danmuSet[danmu_info[6]] = danmu_info
            self.count += 1
            self.style[danmu_info[1]] += 1
            self.pool[danmu_info[5]] += 1
        if summary:
            self.summary()

    def summary(self):
        print("弹幕池最大容量", self.maxLimit)
        print('共有', self.count, '条弹幕')
        self.print_pool()
        self.print_stype()

    def print_pool(self):
        print("\n弹幕池统计如下:")
        print('普通弹幕', self.pool['0'], "条")
        print('字幕弹幕', self.pool['1'], "条")
        print('高级弹幕', self.pool['2'], "条")

    def print_stype(self):
        print("\n弹幕类型统计如下:")
        print("滚动弹幕", self.style['1'] + self.style['2'] + self.style['3'], "条")
        print("底端弹幕", self.style['4'], "条")
        print("顶端弹幕", self.style['5'], "条")
        print("逆向弹幕", self.style['6'], "条")
        print("高级弹幕", self.style['7'], "条")
        print("代码弹幕", self.style['8'], "条")


class DanmuCombinator(object):

    @staticmethod
    def diff(dm1: dict, dm2: dict):
        dic1, dic2, common = DanmuCombinator._xor(dm1, dm2)

        print("文件1独有", len(dic1))
        print("文件2独有", len(dic2))
        print("二者共有", len(common))

    @staticmethod
    def combine(dm1: dict, dm2: dict):
        comb = {}
        comb.update(dm1)
        comb.update(dm2)
        return comb

    @staticmethod
    def _xor(dic1: dict, dic2: dict):
        common = {}
        for item in dic1:
            if item in dic2:
                dic2.pop(item)
                dic1.pop(item)
                common[item] = dic1[item]

        return dic1, dic2, common
