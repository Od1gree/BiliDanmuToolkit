import requests
import time


class Spider(object):
    def __init__(self, cookie_path="cookie.cfg"):
        self.cookie_path = cookie_path

    @staticmethod
    def get_html(url: str):
        """
        get web page
        no cookie required
        :param url: string
        :return: html text in utf-8 encoding
        """
        headers = {
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Host": "www.bilibili.com",
            "Referer": "https://search.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36",
        }
        response = None
        try:
            response = requests.get(url=url, headers=headers)
            assert response.status_code == 200
            return response.text

        except Exception:
            print('请求网页异常', response.url)
            return None

    @staticmethod
    def get_current_danmu(cid: str, url: str):
        """
        Get current danmu pool in bytes
        no cookie required
        This method has 5 seconds pause before send request.

        Tip: use bytes_str.decode('utf-8') to decode
        :param cid: string cid
        :param url: string url of the web page
        :return: response content in bytes
        """
        req = 'https://api.bilibili.com/x/v1/dm/list.so?oid=%s' % cid
        time.sleep(5)
        headers = {
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Host": "api.bilibili.com",
            "Origin": "https://www.bilibili.com",
            "Referer": url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36",
        }
        response = None
        try:
            response = requests.get(url=req, headers=headers)
            assert response.status_code == 200

            return response.content
        except Exception as e:
            if response is not None:
                print('获取弹幕出错', response.url, '\nErrcode:', response.status_code)
            print('获取弹幕异常或文件读写异常', e)

    @staticmethod
    def get_history_danmu(cid: str, url: str, date_str: str, cookie_path: str = 'cookie.cfg'):
        """
        Send history danmu request in specific date_str, return xml_str
        require user cookie
        This method has 5 seconds pause before send request.

        Tip: use bytes_str.decode('utf-8') to decode
        :param cid: cid in string
        :param url: url of the web page in string
        :param date_str: date string in 'YYYY-MM-DD' format
        :param cookie_path: path to cookie file in string format
        :return: xml bytes
        """
        req = 'https://api.bilibili.com/x/v2/dm/history?type=1&oid=' + cid + '&date=' + date_str
        time.sleep(5)
        print('request history danmu:', req)

        response = None
        try:
            response = Spider._history_request(url, req, cookie_path)
            assert response.status_code == 200
            return response.content
        except AssertionError:
            print("状态码错误:", response.status_code)
        except Exception as e:
            if response is not None:
                print("状态码:", response.status_code)
            print("请求历史弹幕失败\n", e)

    # 测试中
    @staticmethod
    def get_history_month(cid: str, url: str, month_str: str, cookie_path: str = 'cookie.cfg'):
        req = 'https://api.bilibili.com/x/v2/dm/history/index?type=1&oid=' + str(cid) + '&month=' + month_str
        time.sleep(5)
        print('request history month', req)

        response = None
        try:
            response = Spider._history_request(url, req, cookie_path)
            assert response.status_code == 200
            return response.content
        except AssertionError:
            print("状态码错误:", response.status_code)
        except Exception as e:
            if response is not None:
                print("状态码:", response.status_code)
            print("请求月份弹幕信息失败\n", e)

    @staticmethod
    def _history_request(ref: str, req_url: str, cookie_path: str):
        cookie = ''
        try:
            config = open(cookie_path, 'rt')
            cookie = config.read()
            config.close()
        except Exception as e:
            print('读取cookie配置文件错误', '\ncontent:', e)

        header = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cookie': cookie,
            'Host': 'api.bilibili.com',
            'Origin': 'https://www.bilibili.com',
            'Referer': ref,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
        }
        response = None
        try:
            response = requests.get(req_url, headers=header)
            return response
        except Exception as e:
            if response is not None:
                print("状态码:", response.status_code)
            print("请求服务器失败\n", e)