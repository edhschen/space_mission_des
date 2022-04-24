# Case04_PropAggregation
# Standard Library
import logging
from copy import deepcopy
from turtle import undo
# Dependencies
from scipy.stats import *
# SpaceMissionDES
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle
from objects.predicates import Predicate, vehicle_in_activity

initial_vehicles = []

pra = {
    "scrub": 1/4,
    "ascent": 1/100,
    "RPO": 1/500,
    "mps_burn": 1/200,
    "dock": 1/200,
    "checkout": 1/1000
}

# -----------------------------------------------------------------------------------------------------------------
# MTV - Mars Transfer Vehicle
spares_MTV = 0

# Events
INIT = Event("INIT")
launch = Event("launch")
burnout = Event("burnout")
capture = Event("capture")
filled = Event("filled")
tmi_burn = Event("tmi_burn")
moi_burn = Event("moi_burn")
ARRIVE = Completor("ARRIVE")
DONE = Completor("DON")

scrub = Event("scrub")
spare = Event("spare")

# ConOps
conops_MTV = ConOps({

    # Nominal
    INIT.name:     Activity("Countdown", INIT, launch, duration=3, p_fail=pra["scrub"], failure=scrub),
    launch.name:   Activity("Ascent", launch, burnout, duration=1, p_fail=pra["ascent"], failure=spare),
    burnout.name:  Activity("Orbit Insertion", burnout, capture, duration=2, p_fail=pra["mps_burn"], failure=spare),
    capture.name:  Activity("Propellant Aggregation", capture, filled, duration = 100),
    filled.name:   Activity("Final Checkout", filled, DONE, duration=2, delay=weibull_min(c=0.5, loc=0, scale=0.1)),  #TODO: add check to see if clock is < critical value
    # filled.name:   Activity("Final Checkout", filled, tmi_burn, duration=2, delay=weibull_min(c=0.5, loc=0, scale=0.1)),  #TODO: add check to see if clock is < critical value
    # tmi_burn.name: Activity("Mars Transit", tmi_burn, moi_burn, duration=180, p_fail=pra["mps_burn"]),
    # moi_burn.name: Activity("Mars Checkout", moi_burn, ARRIVE, duration=2, p_fail=pra["mps_burn"]),

    # Contigencies
    scrub.name: Activity("Recycle", scrub, INIT, duration=0, delay=weibull_min(c=1, loc=0, scale=4)),
    spare.name: Activity("Prepare Spare", spare, INIT, duration=10, delay=weibull_min(c=0.8, loc=0, scale=5)),
})

initial_vehicles += [
    (0.0, Vehicle("MTV", conops_MTV))
]

# -----------------------------------------------------------------------------------------------------------------
# Tanker
spares_Tanker = 0

# Events
begin = Event("begin")
approach = Event("approach")
dock = Event("dock")
undock = Event("undock")
land = Event("land")
# Predicates
after_MTV_deploy = Predicate("Wait for MTV", vehicle_in_activity("MTV", "Propellant Aggregation"))
# ConOps
conops_Tanker = ConOps({

    # Nominal
    INIT.name:     PredicatedActivity("Wait for MTV Deploy", INIT, begin, predicate=after_MTV_deploy),
    begin.name:    Activity("Countdown", begin, launch, duration=0, p_fail=pra["scrub"], failure=scrub),
    launch.name:   Activity("Ascent", launch, burnout, duration=1, p_fail=pra["ascent"], failure=spare, update={'flights': 1}),
    burnout.name:  Activity("Orbit Insertion", burnout, capture, duration=2, p_fail=pra["mps_burn"], failure=spare),
    capture.name:  Activity("Redezvous", capture, approach, duration = 1),
    approach.name: Activity("RPOD", approach, dock, duration = 1),
    dock.name:     Activity("Prop Transfer", dock, undock, duration=0.5, update={'transfers': 1}),  # TODO: add delay
    undock.name:   Activity("Return to Base", undock, land, duration = 1), # TODO: add restart conditions
    land.name:     Activity("End Tanker Mission", land, DONE, duration=0),

    # Contigencies
    scrub.name:    Activity("Recycle", scrub, INIT, duration=0, delay=weibull_min(c=1, loc=0, scale=4)),
    spare.name:    Activity("Prepare Spare", spare, INIT, duration=10, delay=weibull_min(c=0.8, loc=0, scale=5)),
})

initial_vehicles += [
    (0.0, Vehicle("Tanker", conops_Tanker, state={'flights':0, 'transfers':0, 'failures':0}))
]

# -----------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------
