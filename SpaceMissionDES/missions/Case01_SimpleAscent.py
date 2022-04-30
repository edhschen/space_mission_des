
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle

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
    retry_liftoff.name: Activity("Recycle", retry_liftoff, liftoff, duration = 100)
})

# Execute the simulation based on the initialized vehicles
initial_vehicles = [
    (0.0, Vehicle("Booster-01", conops, {'propellant':100})),
    # (25.0, Vehicle("Booster-02", conops, 100))
]
