# predicates.py
import asyncio
from dataclasses import dataclass, field
# from objects.events import Event, Failure
from typing import Callable

@dataclass
class Predicate:
    name: str
    check: Callable
    # next_event: Event
    # event: asyncio.Event = asyncio.Event()


def check_conditions(p, sim):

    # Check if moonship in place
    moonship = sim.entities['MoonShip']

    if moonship.activity.name == "WaitForProp":
        print(f"Predictate <{p.name}> Satisfied")
        return True
    else:
        return False


# p = Predicate("test", check_conditions)

# print("Test Stuff")