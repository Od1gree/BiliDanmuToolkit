import argparse

from DanmuFileTools import *

description = '用于对弹幕文件进行进一步处理的工具'
epilog = ''

def combine(fileset: list, out_path: str):
    first_file = fileset[0]
    base_danmu_str = first_file.read()
    base_danmu = DanmuFile.init_from_str(base_danmu_str)
    for file in fileset[1:]:
        base_danmu.combine(DanmuFile.init_from_str(file.read()))
    base_danmu.export(out_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='BiliDanmuProcessor', description=description, epilog=epilog)

    parser.add_argument('--combine-file', nargs='*', type=argparse.FileType('r+'),
                        help='合并文件, 多个文件之间使用空格隔开')
    parser.add_argument('--combine-folder', type=str,
                        help='合并指定文件夹中的所有弹幕')
    parser.add_argument('--output', type=str, default='output.xml',
                        help='合并之后的文件路径')

    parser.add_argument('--diff', nargs=2, type=argparse.FileType('r+'),
                        help='比较两个弹幕文件')

    config = parser.parse_args()

    if config.combine_file:
        combine(config.combine_file, config.output)

    if config.diff:
        file1 = DanmuFile.init_from_str(config.diff[0].read())
        file2 = DanmuFile.init_from_str(config.diff[1].read())
        DanmuCombinator.diff(file1, file2, True)
