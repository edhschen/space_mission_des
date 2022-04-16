
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

# Import the desired case -- INPUT
# from missions.Case01_SimpleAscent import initial_vehicles
# from missions.Case03_TankThenMoon import initial_vehicles


def run_case(i):
    from missions.Case01_SimpleAscent import initial_vehicles
    sim = Simulator()
    
    # new_loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(new_loop)

    # print("\n***********\n***BEGIN***\n")

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

if __name__ == "__main__":

    N = 1000

    # with Pool(processes=8) as pool:
    #     mc_results = pool.map(run_case, range(N))

    with Pool() as p:
        mc_results = list(
            tqdm.tqdm(
                p.imap_unordered(run_case, range(N)), 
                total=N))

    # mc_results = list(map(run_case, range(N)))

    success_rate = sum(mc_results)

    print(f"The success rate was: {success_rate}/{N} = {100*success_rate/N:.3f} %")
