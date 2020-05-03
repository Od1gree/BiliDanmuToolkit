from BangumiController import *
import argparse

description = '一个下载弹幕的工具, 可实现历史弹幕下载, 以及实时获取新番弹幕的功能.' \
              '此工具还处于开发阶段, 各项功能还不完善, 欢迎提交各种issue.' \
              '注: 使用爬虫会有IP被ban以及账号无法正常使用等风险, 使用前请知晓.'
epilog = '获取一个视频的历史弹幕: ' \
         'python3 main_spider.py --history --cookie \'cookie_sample.cfg\' --video-num av314'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='BiliDanmuToolkit', description=description, epilog=epilog)

    parser.add_argument('--history', action='store_true', default=False,
                        help='获取视频的历史弹幕, 与 --listen 不共用')
    parser.add_argument('--listen', action='store_true', default=False,
                        help='监听视频的当前弹幕, 与 --history 不共用')

    parser.add_argument('--cookie', action='store', default='cookie.cfg', type=str,
                        help='cookie配置文件的路径, 使用 --history 时必须使用此参数')
    parser.add_argument('--url', action='store', type=str,
                        help='从url获取弹幕')
    parser.add_argument('--video-num', action='store', type=str,
                        help='从av/bv号获取弹幕')
    parser.add_argument('--bangumi-num', action='store', type=str,
                        help='从ep/ss号获取弹幕')
    parser.add_argument('--index', action='store', default='1', type=str,
                        help='分p视频的数字, 默认为1')
    parser.add_argument('--bangumi', action='store', type=str,
                        help='番剧列表文件路径, 与 --listen 同时使用')
    parser.add_argument('--min-listen-interval', action='store', default=30, type=int,
                        help='批量监听时,同一url相邻两次获取的最小时间间隔(单位:秒), 默认30,'
                             ' 不得小于10秒, 不大于 --max-listen-interval')
    parser.add_argument('--max-listen-interval', action='store', default=7200, type=int,
                        help='批量监听时,同一url相邻两次获取的最小时间间隔(单位:秒), 默认7200,'
                             ' 不小于 --min-listen-interval')

    config = parser.parse_args()

    if config.history:
        dm = DanmuMaster()
        if config.video_num:
            dm.init_from_av(av=config.video_num, p=config.index, cookie_path=config.cookie)
        elif config.url:
            dm.init_from_url(config.url, config.cookie)
        elif config.bangumi_num:
            dm.init_from_ep(ep=config.bangumi_num, cookie_path=config.cookie)
        else:
            print("需要添加av/bv/ep/ss号, 或者添加url")
            exit(1)
        dm.all_danmu()
    elif config.listen:
        listener = Listener(default_delay=config.min_listen_interval, max_delay=config.max_listen_interval)
        listener.init_from_file(path=config.bangumi)
        listener.start()
    else:
        print("--listen 与 --history 必须使用其中一项.")