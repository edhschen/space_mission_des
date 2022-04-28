@dataclass(order=True)
class ScheduledEvent:
    name: str=field(compare=False)
    template: Event=field(compare=False)
    vehicle: Vehicle=field(compare=False)
    time: float

# Implement the FutureEventList from Prof. Vuduc's example
class FutureEventList:
    def __init__(self):
        self.events = []
        
    def __iter__(self):
        return self
    
    def __next__(self) -> Event:
        from heapq import heappop
        if self.events:
            return heappop(self.events)
        raise StopIteration
    
    def __repr__(self) -> str:
        from pprint import pformat
        return pformat(self.events)

    def get_next(self):
        return heappop(self.events)