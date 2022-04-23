# montecarlo.py
import asyncio
from csv import Dialect
import logging
from typing import Callable
from drivers.simulator import Simulator
from tqdm import tqdm
from multiprocessing import Pool
from functools import partial
import pandas as pd

def run_case(i, case_setup):
    """."""
    sim = Simulator()

    try:
        asyncio.run(
            sim.run(case_setup)
        )
    except asyncio.CancelledError:
        logging.warning("CONOPS FAILED")

    logging.info(f"Mission Success: {sim.success}")
    
        # "failures": sim.failures
    if len(sim.failures) >= 1:
        
        fails = []
        for j, fail_data in sim.failures.iterrows():
            fails.append(
                pd.DataFrame({
                    "replicant": i,
                    "outcome": sim.success, 
                    "duration": sim.clock,
                    "anomaly_count": j+1,
                    "anomaly_time": fail_data.Time,
                    "anomaly_vehicle": fail_data.Vehicle,
                    "anomaly_activity": fail_data.Activity,
                }, index=[j]))

        result = pd.concat(fails)

    else:
        result = pd.DataFrame({
            "replicant": i,
            "outcome": sim.success, 
            "duration": sim.clock,
            "anomaly_count": 0
        }, index=[0])

    # for name, data in sim.entities.items():
    #     result.update({f"vehicle_trace_{name}": data.trace})

    return result


def run_montecarlo(case_setup, N: int, run_parallel = True):
    logging.info("\nRun Monte Carlo")

    case = partial(run_case, case_setup=case_setup)

    if run_parallel:
        with Pool() as p:
            mc_results = list(tqdm(
                p.imap_unordered(case, range(N)), 
                total=N))

    else:
        mc_results = list(
            tqdm(
                map(case, range(N)),
                total=N))

    return pd.concat(mc_results)