
import logging

from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle
from drivers.simulator import Simulator
from utilities.logging import set_logging_level

async def fly_mission(sim: Simulator):

    # -----------------------------------------------------------------------------------------------------------------
    # Mission Definition
    # - Events
    INIT    = Event("INIT")
    liftoff = Event("Liftoff")
    stage   = Event("Stage")
    burnout = Event("Burnout")
    DONE    = Completor("TERM")

    retry_liftoff = Event("retry_liftoff")

    # - ConOps
    conops = ConOps({

        # Nominal
        INIT.name:    Activity("Countdown", INIT, liftoff,  duration = 3),
        liftoff.name: Activity("Ascent S1", liftoff, stage, duration = 10, p_fail = 1/10, failure = retry_liftoff),
        stage.name:   Activity("Ascent S2", stage, burnout, duration = 10, p_fail = 1/20),
        burnout.name: Activity("Insertion", burnout, DONE,  duration = 2,  p_fail = 1/50),

        # Contingency
        retry_liftoff.name: Activity("shortcut", retry_liftoff, liftoff, duration = 100)
    })

    # Execute the simulation based on the initilized vehicles
    initial_vehicles = [
        (0.0, Vehicle("Booster-01", conops, 100)),
        # (25.0, Vehicle("Booster-02", conops, 100))
    ]

    try:
        await sim.run(initial_vehicles)
    except asyncio.CancelledError:
        logging.warning("CONOPS FAILED")


#######################################################################################################################
# Demo
#######################################################################################################################
# logging.basicConfig(level=logging.INFO, format='%(levelname)s>\t%(message)s')
set_logging_level(logging.INFO)

if __name__ == "__main__":

    sim = Simulator()
    
    print("\n***********\n***BEGIN***\n")

    asyncio.run(fly_mission(sim))

    print("\n***DONE****\n***********")