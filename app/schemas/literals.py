from typing import Literal


DisciplineCategory = Literal["track", "field", "road", "combined", "race_walk"]
DisciplineSubCategory = Literal[
    "sprint", "middle_distance", "long_distance", "hurdles", "relay",
    "jump", "throw", "walks", "combined",
]
ScopeType = Literal["national", "international", "regional", "club", "training"]
RoundType = Literal["qualification", "heat", "quarterfinal", "semifinal", "final", "combined"]
EventStatus = Literal["scheduled", "running", "finished", "cancelled"]
ParticipationStatus = Literal["valid", "dns", "dnf", "dsq"]
ResultTypeCategory = Literal["valid", "invalid", "no_mark"]
PlanEventRole = Literal["preparatory", "qualifying", "control", "fundamental"]
SexType = Literal["male", "female"]