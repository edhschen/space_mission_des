
from dataclasses import dataclass
import pandas as pd

#######################################################################################################################
# Events

@dataclass
class Event:
    name: str

@dataclass 
class EventInstance:
    name: str
    parent: Event
    time: float

#######################################################################################################################
# Activities

@dataclass
class Activity:
    name: str
    start: Event
    end: Event
    duration: float

#######################################################################################################################
# Vehicles

@dataclass
class Vehicle:
    name: str
    activity: Activity
    propload: float
    trace: pd.DataFrame = pd.DataFrame(columns=['CurrentEvent', 'NextEvent', 'Prop', 'Activity'])

def start_vehicle(name, conops, propload = 100):
    v = Vehicle(name, conops.first(), propload)
    v.trace = pd.concat([
        v.trace,
        pd.DataFrame({"CurrentEvent": v.activity.start, "NextEvent": v.activity.end, "Prop": v.propload, "Activity": v.activity}, index = [len(v.trace) + 1])
    ])
    return v

#######################################################################################################################
# ConOps

INIT = Event("INIT")
liftoff = Event("Liftoff")
stage = Event("Stage")
orbit = Event("Orbit")

# @dataclass
class ConOps:

    sequence = {
        INIT.name: Activity("waiting", INIT, liftoff, 0),
        liftoff.name: Activity("s1_ascent", liftoff, stage, 10),
        stage.name: Activity("s2_ascent", stage, orbit, 10)
    }

    def first(self):
        return self.sequence["INIT"]

    def after(self, current_event):
        # Get the activity which starts with a particular event
        return self.sequence[current_event.name]


def schedule(activity, future_events):
    end = activity.end
    future_events.append(
        EventInstance(end.name, end, CLOCK + v.activity.duration)
    )

#######################################################################################################################
# Demo
#######################################################################################################################

if __name__ == "__main__":
    CLOCK = 0
    future_events = []

    conops = ConOps()

    # Start with some intial state
    v = start_vehicle("LV1", conops)

    # Vehicle starts in some activity, which will end when that activities event is processed
    current_activity = v.activity
    schedule(v.activity, future_events)

    # Trigger the ending event
    current_event = future_events[0]
    future_events.remove(current_event)

    # Process the event
    # - Update the system state
    # - Update the vehicle state
    # v.propload -= 60  # some fancy code to handle this

    # Get the next activity
    next_activity = conops.after(current_event)

    print(f"The current activity is {current_activity}")
    print(f"The current event is {current_event}")
    print(f"The next activity is {next_activity}")

    # - Change the activity
    v.activity = next_activity

    # Schedule the next event
    schedule(v.activity, future_events)
    future_events

    assert current_event.parent == next_activity.start

    # - Update the vehicle trace
    v.trace = pd.concat([
        v.trace,
        pd.DataFrame({"CurrentEvent": v.activity.start, "NextEvent": v.activity.end, "Prop": v.propload, "Activity": v.activity}, index = [len(v.trace) + 1])
    ])

    v.trace

