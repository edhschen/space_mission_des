# Case03_TankThenMoon
import logging
from copy import deepcopy
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle
from objects.predicates import Predicate, vehicle_in_activity

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

# (1) EOI MCPS
# - Predicates
hab_arrival = Predicate("Hab Arrived", vehicle_in_activity("HAB", "rendezvous"))
# - ConOps
conops_toLDRO_EOI_MCPS = deepcopy(conops_toLDRO).update({
    insertion.name: PredicatedActivity("lunar_loiter", insertion, ready, predicate=hab_arrival),
    ready.name: Activity("pre-transfer", ready, DONE, duration=0)
})

# (2) HAB
# - Predicates
predeploy_EOIMPCS = Predicate("EOIMCPS In LDRO", vehicle_in_activity("MCPS-EOI", "lunar_loiter"))
# - ConOps
conops_toLDRO_HAB = ConOps({
    INIT.name: PredicatedActivity("Countdown", INIT, launch, predicate = predeploy_EOIMPCS),
    launch.name: Activity("Ascent", launch, tli, duration = 1),
    tli.name: Activity("lunar_transit", tli, insertion, duration = 6), # Burn to insert into LDRO
    insertion.name: Activity("lunar_loiter", insertion, rendezvous, duration = 1),
    rendezvous.name: Activity("rendezvous", rendezvous, DONE, duration=0)
})

# (3) MOI MCPS
# - Predicates
# hab_arrival = Predicate("Hab Arrived", vehicle_in_activity("HAB", "rendezvous"))  #TODO: add predicates for stacking
# - ConOps
conops_toLDRO_MOI_MCPS = deepcopy(conops_toLDRO).update({
    insertion.name: Activity("lunar_loiter", insertion, ready, duration=10),
    ready.name: Activity("pre-transfer", ready, DONE, duration=0)
})

# (4) TMI MCPS
# - Predicates
# hab_arrival = Predicate("Hab Arrived", vehicle_in_activity("HAB", "rendezvous"))  #TODO: add predicates for stacking
# - ConOps
conops_toLDRO_TMI_MCPS = deepcopy(conops_toLDRO).update({
    insertion.name: Activity("lunar_loiter", insertion, ready, duration=10),
    ready.name: Activity("pre-transfer", ready, DONE, duration=0)
})

# Start Vehicles
initial_vehicles += [
    (3000.0, Vehicle("MCPS-EOI", conops_toLDRO_EOI_MCPS, 100)),
    (3100.0, Vehicle("HAB",      conops_toLDRO_HAB, 0)),
    (3200.0, Vehicle("MCPS-MOI", conops_toLDRO_MOI_MCPS, 100)),
    (3300.0, Vehicle("MCPS-TMI", conops_toLDRO_TMI_MCPS, 100)),
]

# ************************************************************************************
## Transfer burn: [TMI MCPS + MOI MCPS + HAB + EOI MCPS] LDRO to LD-HEO via TMI MCPS
# ************************************************************************************

# -----------------------------------------------------------------------------------------------------------------
# Crew Mission
# - Events
docked = Event("docked")
tmi_burn = Event("tmi_burn")
moi_burn = Event("moi_burn")
meet_crew_mls = Event("meet_crew_mls")
crew_transfer = Event("crew_transfer")
# Basic LD-HEO Launch
conops_crew = ConOps({
    INIT.name: Activity("Countdown", INIT, launch, duration = 3), #TODO: add predicate to wait transfer vehicle being in LD-HEO
    launch.name: Activity("Ascent", launch, tli, duration = 1),
    tli.name: Activity("lunar_transit", tli, insertion, duration = 6), # Burn to insert into LD-HEO
    insertion.name: Activity("rendezvous with transfer vehicle", insertion, rendezvous, duration=10),
    rendezvous.name: Activity("Docking to transfer vehicle", rendezvous, docked, duration = 1),  #TODO: add vehicle operation
    docked.name: Activity("Pre-TMI Checkout", docked, tmi_burn, duration = 2),                   #TODO: stage MCPS-MOI
    tmi_burn.name: Activity("Crew Mars Transit", tmi_burn, moi_burn, duration = 250),            #TODO: stage MCPS-MOI, check duration
    moi_burn.name: Activity("Rendezvous with MLS", moi_burn, meet_crew_mls, duration = 1),
    meet_crew_mls.name: Activity("Crew Transfer to MLS", meet_crew_mls, crew_transfer,  duration = 1),
    crew_transfer.name: Activity("Surface Mission Loiter", crew_transfer, DONE, duration = 300)   # TODO: add predicate to wait for crew to return
})

initial_vehicles += [
    (4000, Vehicle("Crew", conops_crew, 0))
]

# -----------------------------------------------------------------------------------------------------------------
# Earth Return

# -----------------------------------------------------------------------------------------------------------------
