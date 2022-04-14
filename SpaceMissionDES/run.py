
from objects.events import *

# -----------------------------------------------------------------------------------------------------------------
# Mission Definition
# - Events
INIT    = Event("INIT")
liftoff = Event("Liftoff")
stage   = Event("Stage")
burnout = Event("Burnout")
DONE    = Terminator("TERM")

