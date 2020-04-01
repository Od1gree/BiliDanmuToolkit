from DanmuMaster import *
from datetime import datetime, timedelta, timezone

class TaskNode(object):
    def __init__(self, data, utime: int, priority=1, node_type: int = 0):
        self.next = None
        self.content = data
        self.priority = priority
        self.utime = utime
        self.node_type = node_type


class TaskQueue(object):
    def __init__(self):
        self._root = TaskNode(None, 0)

    def add_task(self, data, utime: int, priority=1, node_type: int = 0):
        new_node = TaskNode(data, utime, priority, node_type)
        self._add(new_node)
        return new_node

    def return_task(self, exist_node: TaskNode):
        if exist_node is None:
            return
        self._add(exist_node)

    def pop_task(self):
        if self._root.next is None:
            print("无任务, 退出.")
            exit(1)

        ret_task = self._root.next
        self._root.next = ret_task.next
        return ret_task

    def _add(self, node: TaskNode):
        current_node = self._root
        while current_node.next is not None and current_node.next.utime < node.utime:
            current_node = current_node.next

        while current_node.next is not None \
                and current_node.next.utime == node.utime \
                and current_node.next.priority <= node.priority:
            current_node = current_node.next

        if current_node.next is None:
            current_node.next = node
        else:
            node.next = current_node.next
            current_node.next = node


class Converter(object):
    @staticmethod
    def ep_to_ss(ep_str: str):
        """
        ep号转ss号
        :param ep_str: epxxxx的字符串
        :return: ssyyyy的字符串
        """
        dm = DanmuMaster()
        dm.init_from_ep(ep_str)
        return dm.ssid

    @staticmethod
    def str_to_timestamp(time_str: str) -> int:
        """
        将北京时间的时间字符串转化为unix时间戳.
        :param time_str: 视频更新时间,格式为 "yyyy-mm-ddThh:mm",例如 "2020-01-02T03:04"
        :return: int型unix时间戳
        """
        time_int = -1
        try:
            time_int = datetime.fromisoformat(time_str)
        except Exception as e:
            print("输入的时间字符串有问题:", e)
            exit(1)
        target_time = datetime(time_int.year, time_int.month, time_int.day,
                               hour=time_int.hour, minute=time_int.minute,
                               tzinfo=timezone(timedelta(hours=8)))
        return int(target_time.timestamp())
