# Case03_TankThenMoon


from turtle import undo
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle

# -----------------------------------------------------------------------------------------------------------------
# Mission Definition
# - Events

INIT        = Event("INIT")
liftoff      = Event("Liftoff")
meco         = Event("meco")
begin_loiter = Event("begin_loiter")
prop_full     = Event("prop_full")
tli_burn     = Event("tli_burn")
ARRIVE       = Completor("ARRIVE")


moonship_conops = ConOps({
    # Nominal
    INIT.name: Activity("Countdown", INIT, liftoff,  duration = 10),
    liftoff.name: Activity("Ascent", liftoff, meco, duration = 10),
    meco.name: Activity("Circularize", meco, begin_loiter, duration = 10),
    begin_loiter.name: Activity("WaitForProp", begin_loiter, prop_full, duration = 110),
    prop_full.name: Activity("Checkout", prop_full, tli_burn, duration = 10),
    tli_burn.name: Activity("TranslunarCoast", tli_burn, ARRIVE, duration = 10)
})



begin_countdown = Event("begin_countdown")
begin_docking = Event("begin_docking")
final_approach = Event("final_approach")
dock = Event("dock")
undock = Event("undock")
DONE = Completor("DONE")


# *********************************************************************
def check_moonship_deployed(p, sim):

    # Check if moonship in place
    moonship = sim.entities['MoonShip']

    if moonship.activity.name == "WaitForProp":
        print(f"Predictate <{p.name}> Satisfied")
        return True
    else:
        return False

moonship_predeployed = Predicate("moonship_predeployed", check_moonship_deployed)
# *********************************************************************

tanker_conops = ConOps({
    # Nominal
    INIT.name: PredicatedActivity("Countdown", INIT, begin_countdown, predicate=moonship_predeployed),
    
    begin_countdown.name: Activity("Countdown", begin_countdown, liftoff,  duration = 10),
    liftoff.name: Activity("Ascent", liftoff, meco, duration = 10),
    meco.name: Activity("Rendezvous", meco, final_approach, duration = 10),
    final_approach.name: Activity("Docking", final_approach, dock, duration = 10),
    dock.name: Activity("PropTransfer", dock, undock, duration=10),
    undock.name: Activity("Disposal", undock, DONE, duration=10)
})


initial_vehicles = [
    (0.0, Vehicle("MoonShip", moonship_conops, 0)),
    (0.0, Vehicle("Tanker", tanker_conops, 100))
]