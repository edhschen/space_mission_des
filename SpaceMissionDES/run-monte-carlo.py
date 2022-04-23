
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
from drivers.montecarlo import run_montecarlo

#######################################################################################################################
# Demo
#######################################################################################################################
# logging.basicConfig(level=logging.INFO, format='%(levelname)s>\t%(message)s')
set_logging_level(logging.ERROR)


# Import the desired case -- INPUT
from missions.Case03_TankThenMoon import initial_vehicles as case_setup

if __name__ == "__main__":

    mc_results = run_montecarlo(case_setup, N := 1000)

    success_rate = sum(mc_results.groupby("replicant").first().outcome) / N

    print(f"The success rate was: {success_rate} = {100*success_rate:.3f} %\n")
