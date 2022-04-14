# vehicles.py
from dataclasses import dataclass, field
import pandas as pd

from objects.activities import Activity, ConOps

#######################################################################################################################
# Vehicle

@dataclass
class Vehicle:
    name: str
    conops: ConOps
    propload: float
    activity: Activity = None
    trace: pd.DataFrame = pd.DataFrame(columns=['Time', 'CurrentEvent', 'NextEvent', 'Prop', 'Activity'])

    def __repr__(self):
        return (f'{self.__class__.__name__} - {self.name}')

    def update_trace(self, sim_time):
        self.trace = pd.concat([
            self.trace,
            pd.DataFrame({
                "Time": sim_time,
                "CurrentEvent": self.activity.start, 
                "NextEvent": self.activity.end, 
                "Prop": self.propload, 
                "Activity": self.activity}, index = [len(self.trace) + 1])
        ])
