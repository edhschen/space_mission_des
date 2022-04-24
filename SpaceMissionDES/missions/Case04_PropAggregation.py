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

# -----------------------------------------------------------------------------------------------------------------
# Problem Settings
# -----------------------------------------------------------------------------------------------------------------

# Probabilistic Inputs
pra = {
    "scrub": 1/4,
    "ascent": 1/100,
    "RPO": 1/500,
    "mps_burn": 1/200,
    "dock": 1/200,
    "checkout": 1/1000
}

# Fleet Management and Requirements
N_tankers_available = 4
N_transfers_required = 10

# -----------------------------------------------------------------------------------------------------------------
# Vehicle and ConOps Settings
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

# Predicates
def check_transers(p, sim):
    # Check on the tanker
    tanker = sim.entities["Tanker"]
    if tanker.state["transfers"] < N_transfers_required:
        return False
    else:
        logging.info(f"Predictate <{p.predicate.name}> Satisfied")
        return True

until_N_transfers = Predicate(f"Wait until {N_transfers_required} propellant transfers are completed", check_transers)

# ConOps
conops_MTV = ConOps({

    # Nominal
    INIT.name:     Activity("Countdown", INIT, launch, duration=3, p_fail=pra["scrub"], failure=scrub),
    launch.name:   Activity("Ascent", launch, burnout, duration=1, p_fail=pra["ascent"]),
    burnout.name:  Activity("Orbit Insertion", burnout, capture, duration=2, p_fail=pra["mps_burn"]),
    # capture.name:  Activity("Propellant Aggregation", capture, filled, duration = 100),
    capture.name:  PredicatedActivity("Propellant Aggregation", capture, filled, predicate=until_N_transfers),
    filled.name:   Activity("Final Checkout", filled, tmi_burn, duration=2, delay=weibull_min(c=0.5, loc=0, scale=0.1), p_fail=pra["checkout"]),  #TODO: add check to see if clock is < critical value
    tmi_burn.name: Activity("Begin Mars Transit", tmi_burn, DONE, duration=0, p_fail=pra["mps_burn"]),

    # Contigencies
    scrub.name: Activity("Recycle", scrub, INIT, duration=0, delay=weibull_min(c=1, loc=0, scale=4)),
})

initial_vehicles += [
    (0.0, Vehicle("MTV", conops_MTV))
]

# -----------------------------------------------------------------------------------------------------------------
# Tanker

# Events
begin = Event("begin")
approach = Event("approach")
dock = Event("dock")
undock = Event("undock")
land = Event("land")

spare = Event("spare")
no_more_spares = Event("no_more_spares")

# Predicates
after_MTV_deploy = Predicate("Wait for MTV", vehicle_in_activity("MTV", "Propellant Aggregation"))

# Branching Events
def limit_spares(sim, vehicle):          # branching logic functions always take (sim, vehicle)
    if vehicle.state["fleet"] > 0:
        return begin
    else:
        return no_more_spares

limit_tanker_spares = Branch(f"Limit to {N_tankers_available-1} Spares", logic=limit_spares)


def count_transfers(sim, vehicle):          # branching logic functions always take (sim, vehicle)
    if vehicle.state["transfers"] < N_transfers_required:
        return begin
    else:
        return land

until_n_tankers = Branch(f"Until {N_transfers_required} Transfers", logic=count_transfers)

# ConOps
conops_Tanker = ConOps({

    # Nominal
    INIT.name:     PredicatedActivity("Wait for MTV Deploy", INIT, limit_tanker_spares, predicate=after_MTV_deploy),

    begin.name:    Activity("Countdown", begin, launch, duration=0, p_fail=pra["scrub"], failure=scrub),

    launch.name:   Activity("Ascent", launch, burnout, duration=1, p_fail=pra["ascent"], failure=spare, update={'flights': 1}),
    burnout.name:  Activity("Orbit Insertion", burnout, capture, duration=2, p_fail=pra["mps_burn"], failure=spare),
    capture.name:  Activity("Redezvous", capture, approach, duration = 1, p_fail=pra["RPO"]),
    approach.name: Activity("RPOD", approach, dock, duration = 1, p_fail=pra["dock"]),
    dock.name:     Activity("Prop Transfer", dock, undock, duration=0.5, update={'transfers': 1}),  # TODO: add delay
    
    undock.name:   Activity("Return to Base", undock, until_n_tankers, duration = 1, p_fail=pra["dock"]), # TODO: add restart conditions
    
    land.name:     Activity("End Tanker Mission", land, DONE, duration=0),

    # Contigencies
    scrub.name:    Activity("Recycle", scrub, INIT, duration=0, delay=weibull_min(c=1, loc=0, scale=4)),
    spare.name:    Activity("Prepare Spare", spare, INIT, duration=10, delay=weibull_min(c=0.8, loc=0, scale=5), update={'fleet': -1}),
    no_more_spares.name: Activity("Out of Spare Tankers", no_more_spares, Failure(), duration=0)
})

initial_vehicles += [
    (0.0, Vehicle("Tanker", conops_Tanker, state={'flights':0, 'transfers':0, 'failures':0, 'fleet': N_tankers_available}))
]


# -----------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------
