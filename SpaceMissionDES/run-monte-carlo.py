
# Imports
# - Standard Library
import logging
from multiprocessing import Pool
# - Dependencies
import tqdm
# - SpaceMissionDES
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle
from drivers.simulator import Simulator
from utilities.logging import set_logging_level


def run_case(i):

    # Import the desired case -- INPUT
    from missions.Case03_TankThenMoon import initial_vehicles
    
    sim = Simulator()

    try:
        asyncio.run(
            sim.run(initial_vehicles)
        )
    except asyncio.CancelledError:
        logging.warning("CONOPS FAILED")

    logging.info(f"Mission Success: {sim.success}")
    return sim.success

#######################################################################################################################
# Demo
#######################################################################################################################
# logging.basicConfig(level=logging.INFO, format='%(levelname)s>\t%(message)s')
set_logging_level(logging.ERROR)
run_parallel = True

if __name__ == "__main__":

    print("\nRun Monte Carlo")
    N = 1000

    if run_parallel:
        with Pool() as p:
            mc_results = list(
                tqdm.tqdm(
                    p.imap_unordered(run_case, range(N)), 
                    total=N))

    else:
        mc_results = list(
            tqdm.tqdm(
                map(run_case, range(N)),
                total=N))

    success_rate = sum(mc_results)

    print(f"The success rate was: {success_rate}/{N} = {100*success_rate/N:.3f} %")
