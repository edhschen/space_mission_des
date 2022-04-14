# events.py

from dataclasses import dataclass, field
from heapq import heappop, heappush
import asyncio

#######################################################################################################################
# Event Templates

@dataclass
class Event:
    """Object used to template events in a mission ConOps"""
    name: str

@dataclass
class Terminator(Event):
    """Object used to indicate end of mission"""
    name: str

    def __post_init__(self):
        super().__init__(self.name)

#######################################################################################################################
# Events with Times

@dataclass(order=True)
class ScheduledEvent(asyncio.Event):
    name: str = field(compare=False)
    template: str = field(compare=False)
    time: float

    def __post_init__(self):
        super().__init__()  # Make sure we inherit all of the attributes of the asyncio.Event class

@dataclass(order=True)
class TerminalEvent(asyncio.Event):
    name: str = field(compare=False)
    template: str = field(compare=False)
    time: float

    def __post_init__(self):
        super().__init__()

#######################################################################################################################
# Future Event List

class FutureEventList:
    def __init__(self):
        self.events = []
        
    def __iter__(self):
        return self
    
    def __next__(self) -> ScheduledEvent:
        if self.events:
            return heappop(self.events)
        raise StopIteration

    def __repr__(self) -> str:
        from pprint import pformat
        return pformat(self.events)

    def get_next(self):
        return heappop(self.events)