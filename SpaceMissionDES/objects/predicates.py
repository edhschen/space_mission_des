# predicates.py
import logging
from dataclasses import dataclass, field
# from objects.events import Event, Failure
from typing import Callable

@dataclass
class Predicate:
    name: str
    check: Callable


def check_conditions(p, sim):

    # Check if moonship in place
    moonship = sim.entities['MoonShip']

    if moonship.activity.name == "WaitForProp":
        print(f"Predictate <{p.name}> Satisfied")
        return True
    else:
        return False


def vehicle_in_activity(vehicle: str, activity: str):

    def check_func(p, sim):
        veh = sim.entities[vehicle]
        if veh.activity.name == activity:
            logging.info(f"Predictate <{p.predicate.name}> Satisfied")
            return True
        else:
            return False
    
    return check_func


# p = Predicate("test", check_conditions)

# print("Test Stuff")