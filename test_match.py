from sheets import read_sheet
from scheduler import match_pilots_for_mission

missions = read_sheet("missions")

mission = missions.iloc[0]

print(match_pilots_for_mission(mission))
