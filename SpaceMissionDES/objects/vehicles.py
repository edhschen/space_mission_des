# vehicles.py
from dataclasses import dataclass, field
import pandas as pd
from collections import Counter

from objects.activities import Activity, ConOps

#######################################################################################################################
# Vehicle

@dataclass
class Vehicle:
    name: str
    conops: ConOps
    # propload: float
    resource: dict = field(default_factory = dict)
    children: list = field(default_factory = list)
    parent: 'Vehicle' = None
    activity: Activity = None
    completed_conops: bool = False
    trace: pd.DataFrame = pd.DataFrame(columns=['Time', 'CurrentEvent', 'NextEvent', 'Prop', 'Activity'])
    state: list = field(default_factory = lambda: {'failures': 0})
    
    @staticmethod
    def create_agg(conops, name = False, *args):
        if len(args) <= 2:
            raise Exception("Not enough arguments provided for object collation")
        resources_agg = Counter({})
        for arg in args:
            resources_agg += Counter(arg.resource)

        if not name:
            name = ""
            for arg in args:
                name += arg.name + "/"
        
        parent = Vehicle(name, conops, resources_agg, children = [args])
        
        for arg in args:
            arg.parent = parent
        
        return parent, args



    def destroy_agg():
        a = 0

    def __repr__(self):
        return (f'{self.__class__.__name__} - {self.name}')

    def update_trace(self, sim_time):
        self.trace = pd.concat([
            self.trace,
            pd.DataFrame({
                "Time": sim_time,
                "CurrentEvent": self.activity.start, 
                "NextEvent": self.activity.end, 
                "Resource": self.resource, 
                "Activity": self.activity}, index = [len(self.trace) + 1])
        ])

    def handle_failure(self):
        self.state['failures'] += 1