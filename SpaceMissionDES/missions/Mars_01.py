import logging
from copy import deepcopy
from objects.events import *
from objects.activities import *
from objects.vehicles import Vehicle
from objects.predicates import Predicate, vehicle_in_activity

initial_vehicles = []

pra = {
    "scrub": 1/20,
    "ascent": 1/100,
    "RPO": 1/500,
    "mps_burn": 1/200,
    "sep_burn": 1/200,
    "dock": 1/200,
    "checkout": 1/1000,
    'landing': 1/200,
}

# Master Event List
INIT = Event("INIT")
launch = Event("launch")
transfer_burn = Event("transfer burn")
crew_transfer = Event('crew transfer burn')
capture_burn = Event("capture burn")
descent_burn = Event('descent burn')
landing = Event('landing')
wait = Event("wait")
wait_for_crew_arrival = Event('wait for crew arrival')
separation = Event("separation")
surface_operations = Event('surface operations')
tli = Event("tli")
insertion = Event("insertion")
ready = Event("ready")
rendezvous = Event("rendezvous")
spare = Event("spare")
separation_orion = Event('separation orion')
separation_tmi = Event('separation TMI')
wait_for_mars_arrival = Event('wait for mars arrival')
wait_for_surface_ops = Event('wait for surface operations')
rendezvous_hab_mls = Event('rendezvous of HAB with MLS')
rendezvous_hab_eoi = Event('rendezvous of HAB with EOI')
rendezvous_hab_tei = Event('rendezvous of HAB with TEI')
rendezvous_hab_orion_pickup = Event('rendezvous of HAB with Orion')
DONE = Completor("DONE")
mission_complete = Completor("MISSION COMPLETE")

# -----------------------------------------------------------------------------------------------------------------
# Predeployment of Earth Return Systems - 2 launches
# (1) SEP + TEI MCPS,
# (2) SEP + EOI MCPS

# ConOps
conops_SEP_EOI = ConOps({
    INIT.name: Activity(
        name="Countdown",
        start=INIT,
        end=launch,
        duration=3,
        p_fail=pra["scrub"]),
    launch.name: Activity(
        name="Ascent",
        start=launch,
        end=transfer_burn,
        duration=1,
        p_fail=pra["ascent"]),
    transfer_burn.name: Activity(
        name="Mars Transit",
        start=transfer_burn,
        end=capture_burn,
        duration=1457,
        p_fail=pra["mps_burn"]),
    capture_burn.name: Activity(
        name="Mars Orbit Capture, SEP Jettisoned, Awaiting Crew...",
        start=capture_burn,
        end=DONE,
        duration=10,
        p_fail=pra["mps_burn"]),
})
conops_SEP_TEI = ConOps({
    INIT.name: Activity(
        name="Countdown",
        start=INIT,
        end=launch,
        duration=3,
        p_fail=pra["scrub"]),
    launch.name: Activity(
        name="Ascent",
        start=launch,
        end=transfer_burn,
        duration=1,
        p_fail=pra["ascent"]),
    transfer_burn.name: Activity(
        name="Mars Transit",
        start=transfer_burn,
        end=capture_burn,
        duration=1457,
        p_fail=pra["mps_burn"]),
    capture_burn.name: Activity(
        name="Mars Orbit Capture, SEP Jettisoned, Awaiting Crew...",
        start=capture_burn,
        end=DONE,
        duration=10,
        p_fail=pra["mps_burn"]),
})

conops_EOI = ConOps({
    INIT.name: Activity(
        name='Vehicle Creation',
        start=INIT,
        end=DONE,
        duration=0,
    )
})
conops_TEI = ConOps({
    INIT.name: Activity(
        name='Vehicle Creation',
        start=INIT,
        end=DONE,
        duration=0,
    )
})

conops_HAB_EOI_TEI = ConOps({
    INIT.name: PredicatedActivity(
        name='Waiting for Crew...',
        start=INIT,
        end=transfer_burn,
        predicate=Predicate(name='Crew Onboard?', check=vehicle_in_activity('MLS', 'Rendezvous of MCT with HAB'))),
    transfer_burn.name: Activity(
        name='Trans Earth Injection Burn, TEI Jettisoned',
        start=transfer_burn,
        end=DONE,
        duration=198,
        agg_type='dejoin',)
})

conops_HAB_EOI = ConOps({
    INIT.name: Activity(
        name='Rendezvous of HAB + EOI-MCPS with TEI-MCPS',
        start=INIT,
        end=wait,
        duration=1,
        agg_type='join',
        agg_params={'conops': conops_HAB_EOI_TEI, 'vehicles': ['HAB + EOI-MCPS', 'TEI-MCPS'], 'name': 'HAB + EOI-MCPS + TEI-MCPS'}),
    wait.name: PredicatedActivity(
        name='Waiting for TEI Burn...',
        start=wait,
        end=capture_burn,
        predicate=Predicate(name='TEI Burn Complete?', check=vehicle_in_activity('HAB + EOI-MCPS + TEI-MCPS', 'Trans Earth Injection Burn, TEI Jettisoned')),),
    capture_burn.name: Activity(
        name='Earth Orbit Insertion Burn into LDRO, EOI Jettisoned',
        start=capture_burn,
        end=DONE,
        duration=1,
        agg_type='dejoin',)

})

conops_SEP_01 = ConOps({
    INIT.name: Activity(
        name='Vehicle Creation',
        start=INIT,
        end=DONE,
        duration=0,
    )
})
conops_SEP_02 = ConOps({
    INIT.name: Activity(
        name='Vehicle Creation',
        start=INIT,
        end=DONE,
        duration=0,
    )
})


initial_vehicles += [
    (0.0, Vehicle(name="SEP-01", parent='SEP-01 + TEI-MCPS', conops=conops_SEP_01, resource={'propellant': 100})),
    (0.0, Vehicle(name="SEP-02", parent='SEP-02 + EOI-MCPS', conops=conops_SEP_02, resource={'propellant': 100})),
    (0.0, Vehicle(name="TEI-MCPS", parent='SEP-01 + TEI-MCPS', conops=conops_TEI, resource={'propellant': 100})),
    (0.0, Vehicle(name="EOI-MCPS", parent='SEP-02 + EOI-MCPS', conops=conops_EOI, resource={'propellant': 100})),
    (1.0, Vehicle(name="SEP-01 + TEI-MCPS", children=['SEP-01', 'TEI-MCPS'], conops=conops_SEP_TEI)),
    (1.0, Vehicle(name="SEP-02 + EOI-MCPS", children=['SEP-02', 'EOI-MCPS'], conops=conops_SEP_EOI)),
]

# -----------------------------------------------------------------------------------------------------------------
# Pre-deployments of Mars Lander System - 1 launches
# (1) SEP-03 + MLS

# ConOps
conops_SEP_03 = ConOps({
    INIT.name: Activity(
        name='Vehicle Creation',
        start=INIT,
        end=DONE,
        duration=0)
})

conops_MLS = ConOps({
    INIT.name: Activity(
        name='Vehicle Creation',
        start=INIT,
        end=wait,
        duration=0),
    wait.name: PredicatedActivity(
        name='Waiting for HAB Separation',
        start=wait,
        end=transfer_burn,
        predicate=Predicate(name='HAB Separated?', check=vehicle_in_activity('HAB + MLS', 'Crew Transferred to MLS, HAB Separating'))),
    transfer_burn.name: Activity(
        name='Transfer Burn to Mars Surface',
        start=transfer_burn,
        end=surface_operations,
        duration=5),
    surface_operations.name: Activity(
        name='Mars Surface Operations',
        start=surface_operations,
        end=crew_transfer,
        duration=300, ),
    crew_transfer.name: Activity(
        name='Boarding MCT',
        start=crew_transfer,
        end=launch,
        duration=0),
    launch.name: Activity(
        name='MCT Launch to HAB',
        start=launch,
        end=rendezvous,
        duration=1,
        p_fail=pra['ascent']),
    rendezvous.name: Activity(
        name='Rendezvous of MCT with HAB',
        start=rendezvous,
        end=DONE,
        duration=1,
        p_fail=pra['dock']),
})

conops_SEP_03_MLS = ConOps({
    INIT.name: Activity(
        name="Countdown",
        start=INIT,
        end=launch,
        duration=3),
    launch.name: Activity(
        name="Ascent",
        start=launch,
        end=transfer_burn,
        duration=1,
        p_fail=pra["ascent"]),
    transfer_burn.name: Activity(
        name="Mars Transit, SEP Jettisoned",
        start=transfer_burn,
        end=capture_burn,
        duration=1457,
        p_fail=pra["sep_burn"],
        agg_type='dejoin'),
    capture_burn.name: Activity(
        name="Mars Aerocapture, awaiting crew...",
        start=capture_burn,
        end=DONE,
        duration=5)
})

initial_vehicles += [
    (1500.0, Vehicle(name="SEP-03", parent='SEP-03 + MLS', conops=conops_SEP_03)),
    (1501.0, Vehicle(name="MLS", parent='SEP-03 + MLS', conops=conops_MLS)),
    (1502.0, Vehicle(name="SEP-03 + MLS", children=['SEP-03', 'MLS'], conops=conops_SEP_03_MLS)),
]

# -----------------------------------------------------------------------------------------------------------------
# Deployment of HAB and Propulsion Systems to LDRO - 3 launches
# (1) HAB,
# (2) MOI MCPS,
# (3) TMI MCPS,


# ConOps
conops_HAB_MOI_TMI_Orion = ConOps({
    INIT.name: Activity(
        name='Crew Transferring From Orion to HAB.',
        start=INIT,
        end=separation_orion,
        duration=0),
    separation_orion.name: Activity(
        name='Jettisoning Orion',
        start=separation_orion,
        end=DONE,
        duration=0,
        agg_type='dejoin'),
})

conops_HAB_MOI_TMI = ConOps({
    INIT.name: PredicatedActivity(
        name='Waiting for Orion...',
        start=INIT,
        end=rendezvous,
        predicate=Predicate(name='Is Orion in Lunar Orbit?', check=vehicle_in_activity('Orion', 'Lunar Insertion'))),
    rendezvous.name: Activity(
        name='Rendezvous-ing',
        start=rendezvous,
        end=wait,
        duration=1,
        p_fail=pra['dock'],
        agg_type='join',
        agg_params={'conops': conops_HAB_MOI_TMI_Orion, "vehicles": ['HAB + MOI-MCPS + TMI-MCPS', 'Orion'], 'name': 'Orion + HAB + MOI-MCPS + TMI-MCPS'}),
    wait.name: PredicatedActivity(
        name='Waiting for Orion Jettison...',
        start=wait,
        end=transfer_burn,
        predicate=Predicate(name='Orion Jettisoned?', check=vehicle_in_activity('Orion + HAB + MOI-MCPS + TMI-MCPS', 'Jettisoning Orion'))),
    transfer_burn.name: Activity(
        name='Mars Transfer Burn, TMI Jettisoned',
        start=transfer_burn,
        end=DONE,
        duration=350,
        p_fail=pra['mps_burn'],
        agg_type='dejoin'),
})

conops_HAB_MOI = ConOps({
    INIT.name: Activity(
        name="Successfully Rendezvous!",
        start=INIT,
        end=wait,
        duration=0),
    wait.name: PredicatedActivity(
        name='Waiting for TMI...',
        start=wait,
        end=rendezvous,
        predicate=Predicate(name='Is TMI in Lunar Orbit?', check=vehicle_in_activity('TMI-MCPS', 'Lunar Insertion'))),
    rendezvous.name: Activity(
        name='Rendezvous-ing',
        start=rendezvous,
        end=wait_for_mars_arrival,
        duration=1,
        p_fail=pra['dock'],
        agg_type='join',
        agg_params={'conops': conops_HAB_MOI_TMI, "vehicles": ['HAB + MOI-MCPS', 'TMI-MCPS'], 'name': 'HAB + MOI-MCPS + TMI-MCPS'}),
    wait_for_mars_arrival.name: PredicatedActivity(
        name='Waiting for Mars Arrival...',
        start=wait_for_mars_arrival,
        end=capture_burn,
        predicate=Predicate(name='Arrived at Mars?', check=vehicle_in_activity('HAB + MOI-MCPS + TMI-MCPS', 'Mars Transfer Burn, TMI Jettisoned'))),
    capture_burn.name: Activity(
        name='Mars Capture Burn, MOI Jettisoned',
        start=capture_burn,
        end=DONE,
        duration=0,
        p_fail=pra['mps_burn'],
        agg_type='dejoin'),
})

conops_HAB_MLS_01 = ConOps({
    INIT.name: Activity(
        name='Crew Transferred to MLS, HAB Separating',
        start=INIT,
        end=DONE,
        duration=1,
        agg_type='dejoin')
})

conops_Crew = ConOps({
    INIT.name: PredicatedActivity(
        name='Waiting for Arrival on Mars',
        start=INIT,
        end=surface_operations,
        predicate=Predicate(name='Is MLS on MARS?', check=vehicle_in_activity('MLS', 'Transfer Burn to Mars Surface'))),
    surface_operations.name: Activity(
        name='Mars Surface Operations',
        start=surface_operations,
        end=crew_transfer,
        duration=300,),
    crew_transfer.name: Activity(
        name='Boarding MCT (TBD)',
        start=crew_transfer,
        end=DONE,
        duration=0)
})

conops_HAB = ConOps({
    INIT.name: Activity(
        name="Countdown",
        start=INIT,
        end=launch,
        duration=3,
        p_fail=pra["scrub"],
        failure=INIT),
    launch.name: Activity(
        name="Ascent",
        start=launch,
        end=transfer_burn,
        duration=1,
        p_fail=pra["ascent"]),
    transfer_burn.name: Activity(
        name="Lunar Transit",
        start=transfer_burn,
        end=capture_burn,
        duration=6,
        p_fail=pra["mps_burn"]),
    capture_burn.name: Activity(
        name="Lunar Insertion",
        start=capture_burn,
        end=wait,
        duration=1,
        p_fail=pra["mps_burn"]),
    wait.name: PredicatedActivity(
        name='Waiting for MOI...',
        start=wait,
        end=rendezvous,
        predicate=Predicate(name='Is MOI in Lunar Orbit?', check=vehicle_in_activity('MOI-MCPS', 'Lunar Insertion'))),
    rendezvous.name: Activity(
        name='Rendezvous-ing',
        start=rendezvous,
        end=wait_for_mars_arrival,
        duration=1,
        p_fail=pra['dock'],
        agg_type='join',
        agg_params={"conops": conops_HAB_MOI, "vehicles": ["HAB", "MOI-MCPS"], "name": "HAB + MOI-MCPS"}),
    wait_for_mars_arrival.name: PredicatedActivity(
        name='Waiting for Mars Arrival...',
        start=wait_for_mars_arrival,
        end=rendezvous_hab_mls,
        predicate=Predicate(name='Arrived at Mars?', check=vehicle_in_activity('HAB + MOI-MCPS', 'Mars Capture Burn, MOI Jettisoned'))),
    rendezvous_hab_mls.name: Activity(
        name='Rendezvous of HAB with MLS, Crew Transferring to MLS',
        start=rendezvous_hab_mls,
        end=wait_for_surface_ops,
        duration=1,
        agg_type='join',
        agg_params={'conops': conops_HAB_MLS_01, 'vehicles': ['HAB', 'MLS'], 'name': 'HAB + MLS'}),
    wait_for_surface_ops.name: PredicatedActivity(
        name='Waiting for Surface Operations',
        start=wait_for_surface_ops,
        end=rendezvous_hab_eoi,
        predicate=Predicate(name='Surface Operations Started?', check=vehicle_in_activity('MLS', 'Mars Surface Operations'))),
    rendezvous_hab_eoi.name: Activity(
        name='Rendezvous of HAB with Pre-deployed EOI',
        start=rendezvous_hab_eoi,
        end=DONE,
        duration=1,
        p_fail=pra['dock'],
        agg_type='join',
        agg_params={'conops': conops_HAB_EOI, 'vehicles': ['HAB', 'EOI-MCPS'], 'name': 'HAB + EOI-MCPS'})
})

conops_MOI = ConOps({
    INIT.name: Activity(
        name="Countdown",
        start=INIT,
        end=launch,
        p_fail=pra["scrub"],
        duration=3),
    launch.name: Activity(
        name="Ascent",
        start=launch,
        end=transfer_burn,
        duration=1,
        p_fail=pra["ascent"]),
    transfer_burn.name: Activity(
        name="Lunar Transit",
        start=transfer_burn,
        end=capture_burn,
        duration=6,
        p_fail=pra["mps_burn"]),
    capture_burn.name: Activity(
        name="Lunar Insertion",
        start=capture_burn,
        end=DONE,
        duration=1,
        p_fail=pra["mps_burn"]),
})

conops_TMI = ConOps({
    INIT.name: Activity(
        name="Countdown",
        start=INIT,
        end=launch,
        p_fail=pra["scrub"],
        duration=3),
    launch.name: Activity(
        name="Ascent",
        start=launch,
        end=transfer_burn,
        duration=1,
        p_fail=pra["ascent"]),
    transfer_burn.name: Activity(
        name="Lunar Transit",
        start=transfer_burn,
        end=capture_burn,
        duration=6,
        p_fail=pra["mps_burn"]),
    capture_burn.name: Activity(
        name="Lunar Insertion",
        start=capture_burn,
        end=DONE,
        duration=1,
        p_fail=pra["mps_burn"]),
})

conops_Orion = ConOps({
    INIT.name: Activity(
        name="Countdown",
        start=INIT,
        end=launch,
        p_fail=pra["scrub"],
        duration=3),
    launch.name: Activity(
        name="Ascent",
        start=launch,
        end=transfer_burn,
        duration=1,
        p_fail=pra["ascent"]),
    transfer_burn.name: Activity(
        name="Lunar Transit",
        start=transfer_burn,
        end=capture_burn,
        duration=6,
        p_fail=pra["mps_burn"]),
    capture_burn.name: Activity(
        name="Lunar Insertion",
        start=capture_burn,
        end=crew_transfer,
        duration=1,
        p_fail=pra["mps_burn"]),
    wait.name: PredicatedActivity(
        name='Waiting for Crew Transfer from Orion to HAB',
        start=wait,
        end=crew_transfer,
        predicate=Predicate(name='Is Orion Docked To HAB?', check=vehicle_in_activity('Orion + HAB + MOI-MCPS + TMI-MCPS', 'Crew Transferring From Orion to HAB.')),),
    crew_transfer.name: Activity(
        name='Crew Transferring from Orion to HAB.',
        start=crew_transfer,
        end=DONE,
        duration=0,
    )
})

conops_HAB_Orion_Pickup = ConOps({
    INIT.name: Activity(
        name='Crew Successfully Transferred from HAB to Orion, HAB Jettisoned',
        start=INIT,
        end=DONE,
        duration=0,
        agg_type='dejoin',)
})

conops_Orion_Pickup = ConOps({
    INIT.name: PredicatedActivity(
        name="Waiting for Crew Arrival to LDRO",
        start=INIT,
        end=launch,
        predicate=Predicate(name='Crew at LDRO?', check=vehicle_in_activity('HAB + EOI-MCPS', 'Earth Orbit Insertion Burn into LDRO, EOI Jettisoned'))),
    launch.name: Activity(
        name="Ascent",
        start=launch,
        end=transfer_burn,
        duration=1,
        p_fail=pra["ascent"]),
    transfer_burn.name: Activity(
        name="Lunar Transit",
        start=transfer_burn,
        end=capture_burn,
        duration=6,
        p_fail=pra["mps_burn"]),
    capture_burn.name: Activity(
        name="Lunar Insertion",
        start=capture_burn,
        end=rendezvous,
        duration=1,
        p_fail=pra["mps_burn"]),
    rendezvous.name: Activity(
        name='Rendezvous of Orion with HAB, Crew Transferring to Orion',
        start=rendezvous,
        end=wait,
        duration=1,
        agg_type='join',
        agg_params={'conops': conops_HAB_Orion_Pickup, 'vehicles': ['HAB', 'Orion-Pickup'], 'name': 'HAB + Orion-Pickup'}),
    wait.name: PredicatedActivity(
        name='Waiting for Crew Transfer...',
        start=wait,
        end=descent_burn,
        predicate=Predicate(name='Crew Transferred?', check=vehicle_in_activity('HAB + Orion-Pickup', 'Crew Successfully Transferred from HAB to Orion, HAB Jettisoned'))),
    descent_burn.name: Activity(
        name='Descent Burn Back to Earth',
        start=descent_burn,
        end=landing,
        duration=20,
        p_fail=pra['mps_burn']),
    landing.name: Activity(
        name='Crew Landing on Earth',
        start=landing,
        end=mission_complete,
        duration=1,
        p_fail=pra['landing'])
})


# Start Vehicles
initial_vehicles += [
    (3100.0, Vehicle("HAB", conops_HAB, resource={'crew': 0})),  # resource for habitat is number of crew members
    (3101.0, Vehicle("MOI-MCPS", conops_MOI, resource={'propellant': 100})),
    (3102.0, Vehicle("TMI-MCPS", conops_TMI, resource={'propellant': 100})),
    (3103.0, Vehicle("Orion", conops_Orion, resource={'crew': 5})),
    (3104.0, Vehicle("Orion-Pickup", conops_Orion_Pickup, resource={'crew': 0})),
]
