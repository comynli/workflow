from copy import deepcopy
from .stack import Stack


class Vertex:
    def __init__(self, state):
        self._value = state

    @property
    def value(self):
        return self._value.id

    def __hash__(self):
        return hash(self._value.id)


class Edge:
    def __init__(self, transform):
        self.transform = transform

    @property
    def perv(self):
        return self.transform.prev

    @property
    def next(self):
        return self.transform.next

    def __hash__(self):
        return hash(self.transform.id)


class Digraph:
    def __init__(self, vertex=None, edges=None):
        if vertex is None:
            vertex = set()
        if edges is None:
            edges = set()
        self.vertex = vertex
        self.edges = edges

    def add_vertex(self, vertex):
        self.vertex.add(vertex)

    def add_edge(self, edge):
        if edge.perv in self.vertex and edge.next in self.vertex:
            self.edges.add(edge)
        raise Exception('perv or next not in vertex set')

    def has_isolated_vertex(self):
        vertex = set()
        for edge in self.edges:
            vertex.add(edge.perv)
            vertex.add(edge.next)
        return len(self.vertex.intersection(vertex)) > 0

    def find_start(self):
        vertex = set()
        for edge in self.edges:
            vertex.add(edge.next)
        return self.vertex.intersection(vertex)

    def find_end(self):
        vertex = set()
        for edge in self.edges:
            vertex.add(edge.perv)
        return self.vertex.intersection(vertex)

    def copy(self):
        return Digraph(self.vertex, self.edges)

    def remove_vertex(self, v):
        vertex = deepcopy(self.vertex).remove(v)
        edges = set()
        for edge in self.edges:
            if edge.perv != v and edge.next != v:
                edges.add(edge)
        return Digraph(vertex, edges)

    def has_ring(self):
        g = self.copy()
        stack = Stack()
        for v in g.find_start():
            stack.push(v)
        while stack.top is not None:
            v = stack.pop()
            g = g.remove_vertex(v)
            for v in g.find_start():
                stack.push(v)
        return len(g.vertex) > 0
