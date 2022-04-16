# activities.py
from dataclasses import dataclass, field
from objects.events import Event, Failure, Predicate

#######################################################################################################################
# Activities

@dataclass
class Activity:
    name: str
    start: Event
    end: Event
    duration: float
    p_fail: float = 0    # probability that the activity will fail to be completed (i.e. failed launch)
    failure: Event = Failure()


@dataclass
class PredicatedActivity:
    name: str
    start: Event
    end: Event
    predicate: Predicate
    # duration: float
    p_fail: float = 0    # probability that the activity will fail to be completed (i.e. failed launch)
    failure: Event = Failure()

#######################################################################################################################
# ConOps

@dataclass
class ConOps:
    sequence: dict

    def first(self):
        return self.sequence["INIT"]

    def after(self, current_event):
        # Get the activity which starts with a particular event
        return self.sequence[current_event.name]