class Node:
    def __init__(self, value, next=None):
        self._next = next
        self._value = value

    @property
    def value(self):
        return self._value

    @property
    def next(self):
        return self._next


class Stack:
    def __init__(self):
        self.top = None

    def push(self, value):
        node = Node(value, self.top)
        self.top = node

    def pop(self):
        if self.top is not None:
            ret = self.top
            self.top = ret.next
            return ret.value
        return None
