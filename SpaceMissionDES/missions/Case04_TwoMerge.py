# Case03_TankThenMoon
import logging
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle
from objects.predicates import Predicate, vehicle_in_activity

together_conops = ConOps({})

# -----------------------------------------------------------------------------------------------------------------
# MoonShip

# Events
INIT         = Event("INIT")
liftoff      = Event("Liftoff")
meco         = Event("meco")
begin_loiter = Event("begin_loiter")
prop_full    = Event("prop_full")
tli_burn     = Event("tli_burn")
dock         = Event("dock")
stall = Event("stall")
almost_arrive = Event("almost_arriving")
finale = Event("finale")
ARRIVE       = Completor("ARRIVE")

# *********************************************************************
# Predicates
def check_tanker_prop_transfer(p, sim):

    # Check if moonship in place
    tanker = sim.entities['Tanker']

    if tanker.activity.name == "Disposal":
        logging.info(f"Predictate <{p.predicate.name}> Satisfied")
        return True
    else:
        return False

tanker_prop_transfered = Predicate("tanker_prop_transfered", check_tanker_prop_transfer)
# *********************************************************************

# ConOps
moonship_conops = ConOps({
    # Nominal
    INIT.name: Activity("Countdown", INIT, liftoff,  duration = 10),
    liftoff.name: Activity("Ascent", liftoff, meco, duration = 10),
    meco.name: Activity("Circularize", meco, begin_loiter, duration = 10),
    begin_loiter.name: PredicatedActivity("WaitForProp", begin_loiter, prop_full, predicate = tanker_prop_transfered),
    
    prop_full.name: Activity("Checkout", prop_full, tli_burn, duration = 110),
    tli_burn.name: Activity("TranslunarCoast", tli_burn, dock, duration = 10, p_fail=1/10),

    dock.name: Activity("Docking", dock, almost_arrive, duration = 10, p_fail = 1/10, type="join", params={"conops": together_conops, "vehicles": ["Tanker", "MoonShip"], "name": "together"}),
    almost_arrive.name: PredicatedActivity("spin", almost_arrive, finale, p_fail = 1/10, predicate = Predicate("together finished", vehicle_in_activity("together", "DoSomething"))),
    finale.name: Activity("Finale", finale, ARRIVE, duration = 2, p_fail = 1/100)


})


# -----------------------------------------------------------------------------------------------------------------
# Tanker

# Events
INIT            = Event("INIT")
begin_countdown = Event("begin_countdown")
liftoff         = Event("Liftoff")
meco            = Event("meco")
begin_docking   = Event("begin_docking")
final_approach  = Event("final_approach")
dock            = Event("dock")
undock          = Event("undock")
DONE            = Completor("DONE")

get_spare = Event("recycle")

# *********************************************************************
# Predicates
def check_moonship_deployed(p, sim):

    # Check if moonship in place
    moonship = sim.entities['MoonShip']

    if moonship.activity.name == "WaitForProp":
        logging.info(f"Predictate <{p.predicate.name}> Satisfied")
        return True
    else:
        return False

moonship_predeployed = Predicate("moonship_predeployed", check_moonship_deployed)
# *********************************************************************

# ConOps
tanker_conops = ConOps({
    # Nominal
    INIT.name: PredicatedActivity("WaitForMoonship", INIT, begin_countdown, predicate=moonship_predeployed),
    
    begin_countdown.name: Activity("Countdown", begin_countdown, liftoff,  duration = 10),
    liftoff.name:         Activity("Ascent", liftoff, meco, duration = 10, p_fail = 1/10, failure = get_spare),
    meco.name:            Activity("Rendezvous", meco, final_approach, duration = 10, p_fail = 1/10),
    final_approach.name:  Activity("Docking", final_approach, dock, duration = 10),
    dock.name:            Activity("PropTransfer", dock, undock, duration=10, p_fail = 2/10),
    undock.name:          Activity("Disposal", undock, DONE, duration=10, p_fail = 1/10),

    # Contingency
    get_spare.name: Activity("PrepSpare", get_spare, begin_countdown, duration = 100)
})

dosomething = Event("dosomething")
FINISH = Completor("FINISH")

together_conops = ConOps({
    INIT.name: Activity("DockingSuccess", INIT, dosomething, duration = 2),
    dosomething.name: Activity("DoSomething", dosomething, FINISH, duration = 20, p_fail = 1/20)
})

# populate conops that were used
moonship_conops.sequence['dock'].params['conops'] = together_conops

def populate_conops(vehicle, agg_event, conops):
    vehicle.sequence[agg_event].params['conops'] = conops


# -----------------------------------------------------------------------------------------------------------------
initial_vehicles = [
    (0.0, Vehicle("MoonShip", moonship_conops, {"propellant": 0})),
    (0.0, Vehicle("Tanker", tanker_conops, {"propellant": 100}))
]