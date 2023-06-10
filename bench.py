from collections import namedtuple
from dataclasses import dataclass
import timeit

@dataclass
class SquareDataclass:
    attribute1: int
    attribute2: str
    attribute3: bool

SquareNamedTuple = namedtuple('SquareNamedTuple', ['attribute1', 'attribute2', 'attribute3'])

class SquareClassWithInit:
    def __init__(self, attribute1, attribute2, attribute3):
        self.attribute1 = attribute1
        self.attribute2 = attribute2
        self.attribute3 = attribute3

class SquareClassWithoutInit:
    pass

def time_creation():
    setup_code = '''
from __main__ import SquareDataclass, SquareNamedTuple, SquareClassWithInit, SquareClassWithoutInit
'''
    dataclass_code = '''
a = SquareDataclass(1, 'A', True)
'''
    namedtuple_code = '''
a = SquareNamedTuple(1, 'A', True)
'''
    class_with_init_code = '''
a = SquareClassWithInit(1, 'A', True)
'''
    class_without_init_code = '''
a = SquareClassWithoutInit()
a.attribute1 = 1
a.attribute2 = 'A'
a.attribute3 = True
'''
    dataclass_time = timeit.timeit(dataclass_code, setup=setup_code, number=1000000)
    namedtuple_time = timeit.timeit(namedtuple_code, setup=setup_code, number=1000000)
    class_with_init_time = timeit.timeit(class_with_init_code, setup=setup_code, number=1000000)
    class_without_init_time = timeit.timeit(class_without_init_code, setup=setup_code, number=1000000)

    print("Dataclass creation time:", dataclass_time)
    print("Namedtuple creation time:", namedtuple_time)
    print("Class with __init__ creation time:", class_with_init_time)
    print("Class without __init__ creation time:", class_without_init_time)

time_creation()
