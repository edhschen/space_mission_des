import drivers.events
import drivers.time
import conceptualizations.datahandlers
import conceptualizations.object

def testbed():
    INIT = Event("INIT")
    liftoff = Event("Liftoff")
    stage = Event("Stage")
    orbit = Event("Orbit")

    # Activities
    activities = {
        INIT.name: Activity("waiting", INIT, liftoff, 0),
        liftoff.name: Activity("s1_ascent", liftoff, stage, 10),
        stage.name: Activity("s2_ascent", stage, orbit, 10)
    }

conops = ConOps(activities)

def run_sim():
    # Reset the clock
    set_time(0)

    # Create and empty events list
    future = FutureEventList()

    # Start a vehicle
    current_vehicle = Vehicle.initialize("LV1", conops)

    # Vehicle starts in some activity, which will end when that activities event is processed
    current_vehicle.schedule_next_event(future)

    # Trigger the ending event
    current_event = future.get_next()

    # Process the event
    # - Update the system state
    # - Update the vehicle state
    # v.propload -= 60  # some fancy code to handle this

    # Get the next activity
    next_activity = conops.after(current_event)

    print(f"The current activity is {current_vehicle.activity}")
    print(f"The current event is {current_event}")
    print(f"The next activity is {next_activity}")

    # - Change the activity
    current_vehicle.activity = next_activity

    # Schedule the next event
    current_vehicle.schedule_next_event(future)

    assert current_event.template == next_activity.start

    # - Update the vehicle trace
    current_vehicle.update_trace()

    current_vehicle.trace