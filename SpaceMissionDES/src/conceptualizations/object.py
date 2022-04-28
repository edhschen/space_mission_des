@dataclass
class Vehicle:
    name: str
    activity: Activity
    propload: float
    trace: pd.DataFrame = pd.DataFrame(columns=['CurrentEvent', 'NextEvent', 'Prop', 'Activity'])

    def __repr__(self):
        return (f'{self.__class__.__name__} - {self.name}')

    @staticmethod
    def initialize(name, conops, propload = 100):
        v = Vehicle(name, conops.first(), propload)
        v.update_trace()
        return v

    def schedule_next_event(self, future_event_list):
        template = self.activity.end
        name = self.activity.end.name
        heappush(
            future_event_list.events,
            ScheduledEvent(name, template, self, now() + self.activity.duration)
        )

    def update_trace(self):
        self.trace = pd.concat([
            self.trace,
            pd.DataFrame({
                "CurrentEvent": self.activity.start, 
                "NextEvent": self.activity.end, 
                "Prop": self.propload, 
                "Activity": self.activity}, index = [len(self.trace) + 1])
        ])