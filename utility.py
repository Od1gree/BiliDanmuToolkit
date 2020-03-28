class TaskNode(object):
    def __init__(self, data, utime: int, priority=1):
        self.next = None
        self.content = data
        self.priority = priority
        self.utime = utime


class TaskQueue(object):
    def __init__(self):
        self._root = TaskNode(None, 0)

    def add_task(self, data, utime: int, priority=1):
        new_node = TaskNode(data, utime, priority)
        self._add(new_node)

    def get_task(self):
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

