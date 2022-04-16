
# Imports
# - Standard Library
import logging
# - SpaceMissionDES
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle
from drivers.simulator import Simulator
from utilities.logging import set_logging_level

# Import the desired case -- INPUT
# from missions.Case01_SimpleAscent import initial_vehicles
from missions.Case03_TankThenMoon import initial_vehicles


#######################################################################################################################
# Demo
#######################################################################################################################
# logging.basicConfig(level=logging.INFO, format='%(levelname)s>\t%(message)s')
set_logging_level(logging.INFO)

if __name__ == "__main__":

    sim = Simulator()
    
    print("\n***********\n***BEGIN***\n")

    try:
        asyncio.run(
            sim.run(initial_vehicles)
        )
    except asyncio.CancelledError:
        logging.warning("CONOPS FAILED")

    print("\n***DONE****\n***********")