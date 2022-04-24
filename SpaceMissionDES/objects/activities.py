# activities.py
from dataclasses import dataclass, field
from objects.events import Event, Failure, Predicate
from scipy import stats

#######################################################################################################################
# Activities

@dataclass
class Activity:
    name: str
    start: Event
    end: Event
    duration: float
    delay: stats._distn_infrastructure.rv_frozen = None
    p_fail: float = 0    # probability that the activity will fail to be completed (i.e. failed launch)
    failure: Event = Failure()
    update: dict = field(default_factory = lambda: {})


@dataclass
class PredicatedActivity:
    name: str
    start: Event
    end: Event
    predicate: Predicate
    # duration: float
    p_fail: float = 0    # probability that the activity will fail to be completed (i.e. failed launch)
    failure: Event = Failure()
    update: dict = field(default_factory = lambda: {})

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

    def update(self, additions:dict):
        self.sequence.update(additions)
        return self

#######################################################################################################################
# Utility Functions

def sample(delay):
    if delay is None:
        return 0.0
    else:
        return delay.rvs()

