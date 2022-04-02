import asyncio
import time

async def start(liftoff):
    for i in [3, 2, 1]:
        time.sleep(0.2)
        print("T-", i)

    liftoff.set()

# liftoff = asyncio.Event()
# start(liftoff)

async def ascent_1(liftoff, stage, duration = 2): 

    await liftoff.wait()
    print("We have liftoff!")

    # Wait Until time now() + duration
    # AdvanceTime(now() + duration)
    await asyncio.sleep(duration)

    stage.set()
    # print(f"{name}: staging")

async def ascent_2(stage, meco, duration = 2): 

    await stage.wait()
    print("Staging complete")

    # Wait Until time now() + duration
    # AdvanceTime(now() + duration)
    await asyncio.sleep(1)

    meco.set()
    # print(f"{name}: staging")


async def in_orbit(meco):

    await meco.wait()
    print("System nominal --> We're in Orbit")


async def fly_mission():

    liftoff = asyncio.Event()
    stage = asyncio.Event()
    meco  = asyncio.Event()

    tasks = [
        asyncio.create_task(start(liftoff)),
        asyncio.create_task(ascent_1(liftoff, stage)),
        asyncio.create_task(ascent_2(stage, meco)),
        asyncio.create_task(in_orbit(meco)),
    ]

    await asyncio.gather(*tasks)


asyncio.run(fly_mission())

# flightA = loop.create_task(fly_mission(end_flightA, "Vehicle A"), name="flightA")
# flightB = loop.create_task(fly_mission(end_flightB, "Vehicle B"), name="flightB")

# fel = [end_flightA, end_flightB]

print("DONE.")