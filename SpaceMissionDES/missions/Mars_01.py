# Case03_TankThenMoon
import logging
from copy import deepcopy
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle

initial_vehicles = []

# -----------------------------------------------------------------------------------------------------------------
# SEP1_TEI

# Events
INIT = Event("INIT")
launch = Event("launch")
transfer = Event("transfer")
capture = Event("capture")
wait = Event("wait")
DONE = Completor("DONE")


# ConOps
conops_SEP1_TEI = ConOps({
    INIT.name: Activity("Countdown", INIT, launch, duration = 3),
    launch.name: Activity("Ascent", launch, transfer, duration = 1),
    transfer.name: Activity("Mars_Transit", transfer, capture, duration = 1457),
    capture.name: Activity("Mars_Loiter", capture, DONE, duration = 10)  #TODO: Add next event a crew arrival predicate
})

initial_vehicles += [
    (0.0,    Vehicle("SEP-1_MCPS-TEI", conops_SEP1_TEI, 100))
]

# -----------------------------------------------------------------------------------------------------------------
# Mars Predeploy

stage = Event("stage")

# Same ConOps for 5 separate predeployments
# ConOps
conops_predeploy = ConOps({
    INIT.name: Activity("Countdown", INIT, launch, duration = 3),
    launch.name: Activity("Ascent", launch, transfer, duration = 1),
    transfer.name: Activity("Mars_Transit", transfer, stage, duration = 1457),
    stage.name: Activity("Aerocapture", stage, capture, duration = 1),  #TODO: add separation of SEP and such
    capture.name: Activity("Mars_Loiter", capture, DONE, duration = 5)  #TODO: Add next event a crew arrival predicate
})

initial_vehicles += [
    (1500.0, Vehicle("SEP-2_MLS-1", deepcopy(conops_predeploy), 100)),
    (1500.0, Vehicle("SEP-3_MLS-2", deepcopy(conops_predeploy), 100)),
    (1500.0, Vehicle("SEP-4_MLS-3", deepcopy(conops_predeploy), 100)),
    (1500.0, Vehicle("SEP-5_MLS-4", deepcopy(conops_predeploy), 100)),
    (1500.0, Vehicle("SEP-6_MLS-5", deepcopy(conops_predeploy), 100)),
]

# -----------------------------------------------------------------------------------------------------------------
# LDRO Aggergation
# - 4 launches: EOI MCPS (1), HAB (2), MOI MCPS (3), TMI MCPS (4)
# - First 4 go to LDRO for aggergation

tli = Event("tli")
insertion = Event("insertion")
ready = Event("ready")
rendezvous = Event("rendezvous")

# Basic LDRO Launch
conops_toLDRO = ConOps({
    INIT.name: Activity("Countdown", INIT, launch, duration = 3),
    launch.name: Activity("Ascent", launch, tli, duration = 1),  #TODO: add predicate to wait on other pre-deployments
    tli.name: Activity("lunar_transit", tli, insertion, duration = 6), # Burn to insert into LDRO
})

# Predicate
def wait_for_hab(p, sim):
    hab = sim.entities["HAB"]
    if hab.activity.name == "rendezvous":
        logging.info(f"Predictate <{p.predicate.name}> Satisfied")
        return True
    else:
        return False

hab_arrival = Predicate("Hab Arrived", wait_for_hab)

# (1) EOI MCPS
# - Predicate
def wait_for_hab(p, sim):
    hab = sim.entities["HAB"]
    if hab.activity.name == "rendezvous":
        logging.info(f"Predictate <{p.predicate.name}> Satisfied")
        return True
    else:
        return False
hab_arrival = Predicate("Hab Arrived", wait_for_hab)
# - conops
conops_toLDRO_EOI_MCPS = deepcopy(conops_toLDRO).update({
    insertion.name: PredicatedActivity("lunar_loiter", insertion, ready, predicate=hab_arrival),
    ready.name: Activity("pre-transfer", ready, DONE, duration=0)
})

# (2) HAB
# - Predicate
def wait_for_EOIMPCS(p, sim):
    hab = sim.entities["MCPS-EOI"]
    if hab.activity.name == "lunar_loiter":
        logging.info(f"Predictate <{p.predicate.name}> Satisfied")
        return True
    else:
        return False

predeploy_EOIMPCS = Predicate("EOIMCPS In LDRO", wait_for_EOIMPCS)

conops_toLDRO_HAB = ConOps({
    INIT.name: PredicatedActivity("Countdown", INIT, launch, predicate = predeploy_EOIMPCS),
    launch.name: Activity("Ascent", launch, tli, duration = 1),
    tli.name: Activity("lunar_transit", tli, insertion, duration = 6), # Burn to insert into LDRO
    insertion.name: Activity("lunar_loiter", insertion, rendezvous, duration = 1),
    rendezvous.name: Activity("rendezvous", rendezvous, DONE, duration=0)
})








initial_vehicles += [
    (3000.0, Vehicle("MCPS-EOI", deepcopy(conops_toLDRO_EOI_MCPS), 100)),
    (3505.0, Vehicle("HAB", deepcopy(conops_toLDRO_HAB), 0)),
]






# -----------------------------------------------------------------------------------------------------------------
