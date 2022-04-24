# predicates.py
import logging
from functools import partial
from dataclasses import dataclass, field
# from objects.events import Event, Failure
from typing import Callable

@dataclass
class Predicate:
    name: str
    check: Callable


def check_func(p, sim, vehicle, activity):
    veh = sim.entities[vehicle]
    if veh.activity.name == activity:
        logging.info(f"Predictate <{p.predicate.name}> Satisfied")
        return True
    else:
        return False


def vehicle_in_activity(vehicle: str, activity: str):
    return partial(check_func, vehicle = vehicle, activity = activity)


# p = Predicate("test", check_conditions)

# print("Test Stuff")