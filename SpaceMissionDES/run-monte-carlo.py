
# Imports
# - Standard Library
import logging
from pathlib import Path
# - Dependencies

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
# from missions.Case03_TankThenMoon import initial_vehicles
# from missions.Case04_TwoMerge import initial_vehicles
from missions.Mars_01 import initial_vehicles

out_dir = Path.cwd() / "results" / "test-05"
if not out_dir.exists():
    out_dir.mkdir()

if __name__ == "__main__":

    mc_results = run_montecarlo(initial_vehicles, N := 6000, run_parallel=True)

    success_rate = sum(mc_results.groupby("replicant").first().outcome) / N

    mc_results.to_csv(out_dir / "mc.csv", index=False)

    print(f"The success rate was: {success_rate:.3f} = {100*success_rate:.2f} %\n")
