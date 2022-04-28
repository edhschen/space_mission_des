@dataclass
class Event:
    name: str

@dataclass
class Activity:
    name: str
    start: Event
    end: Event
    duration: float

@dataclass
class ConOps:
    sequence: dict

    def first(self):
        return self.sequence["INIT"]

    def after(self, current_event):
        # Get the activity which starts with a particular event
        return self.sequence[current_event.name]