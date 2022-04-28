# SpaceMissionDES
Implementation of a discrete event simulation used for studying duration and reliability of space missions.

### requirements
python 3.10 (scipy, tqdm, pandas)

### running
1. install all dependencies and python 3.10
2. in `SpaceMissionDES/run-single.py` or `SpaceMissionDES/run-monte-carlo.py` import the input setting file for the mission in question, for instance `from missions.Case04_TwoMerge import initial_vehicles`
3. from the root directory, `python3.10 SpaceMissionDES/run-single.py` or `python3.10 SpaceMissionDES/run-monte-carlo.py`
    * run-monte-carlo runs 200 trials, whereas run-single runs one
    * run-monte-carlo outputs a trial results file in `results/`

### directory structure
`examples/`
* example jupyter notebook and execution scripts to demonstrate line of reasoning

`experiments/`
* miniapp experiments to test 

`results/`
* resulting files from monte carlo simulation

`SpaceMissionDES/`
* `analysis/`
    * jupyter notebook for risk analysis graphs
* `drivers/`
    * main simulation driver logic
* `missions/`
    * pre-populated missions of interest
* `objects/`
    * simulation object declarations and utility functions
* `src/`
    * unused separate code migration
* `utilities/`
    * logging utility for simulation state
* main execution files and testing utilities