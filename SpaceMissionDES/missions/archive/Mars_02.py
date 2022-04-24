# Case03_TankThenMoon
import logging
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle
from objects.predicates import Predicate, vehicle_in_activity

initial_vehicles = []

pra = {
    "scrub":    1/2,
    "ascent":   1/20,
    "RPO":      1/4,
    "mps_burn": 0/2,  # issue
    "dock":     1/2,
    "checkout": 1/2
}

# -----------------------------------------------------------------------------------------------------------------
# SEP1_TEI

# Events
INIT = Event("INIT")
launch = Event("launch")
transfer = Event("transfer")
capture = Event("capture")
wait = Event("wait")
DONE = Completor("DONE")

# -----------------------------------------------------------------------------------------------------------------
# LDRO Aggergation
# - 4 launches: EOI MCPS (1), HAB (2), MOI MCPS (3), TMI MCPS (4)
# - First 4 go to LDRO for aggergation

tli = Event("tli")
insertion = Event("insertion")
ready = Event("ready")
rendezvous = Event("rendezvous")

# (1) EOI MCPS
# - Predicates
# hab_arrival = Predicate("Hab Arrived", vehicle_in_activity("HAB", "rendezvous"))
# - ConOps
conops_toLDRO_EOI_MCPS = ConOps({
    INIT.name: Activity("Countdown", INIT, launch, duration = 3),#, p_fail = pra["scrub"], failure=INIT),
    launch.name: Activity("Ascent", launch, tli, duration = 1, p_fail = pra["ascent"]),  #TODO: add predicate to wait on other pre-deployments
    tli.name: Activity("lunar_transit", tli, insertion, duration = 6),#, p_fail = pra["mps_burn"]), # Burn to insert into LDRO
    # insertion.name: PredicatedActivity("lunar_loiter", insertion, ready, predicate=hab_arrival),
    insertion.name: Activity("lunar_loiter", insertion, ready, duration =2),
    ready.name: Activity("pre-transfer", ready, DONE, duration=1)
})

# (2) HAB
# # - Predicates
# predeploy_EOIMPCS = Predicate("EOIMCPS In LDRO", vehicle_in_activity("MCPS-EOI", "lunar_loiter"))
# - ConOps
conops_toLDRO_HAB = ConOps({
    # INIT.name: PredicatedActivity("Countdown", INIT, launch, predicate = predeploy_EOIMPCS, p_fail = pra["scrub"], failure=INIT),
    INIT.name: Activity("Countdown", INIT, launch, duration = 1),
    launch.name: Activity("Ascent", launch, rendezvous, duration = 1),#, p_fail = pra["ascent"]),
    # tli.name: Activity("lunar_transit", tli, insertion, duration = 6, p_fail = pra["mps_burn"]), # Burn to insert into LDRO
    # insertion.name: Activity("lunar_insertion", insertion, rendezvous, duration = 1, p_fail = pra["mps_burn"]),
    rendezvous.name: Activity("rendezvous", rendezvous, DONE, duration=1)#, p_fail = pra["RPO"])
})

# Start Vehicles
initial_vehicles += [
    (3000.0, Vehicle("MCPS-EOI", conops_toLDRO_EOI_MCPS, 100)),
    (3500.0, Vehicle("HAB",      conops_toLDRO_HAB, 0)),
]
