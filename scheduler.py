from sheets import read_sheet
import pandas as pd

def get_available_pilots():
    pilots = read_sheet("pilot_roster")
    return pilots[pilots["status"] == "Available"]


def get_available_drones():
    drones = read_sheet("drone_fleet")
    return drones[drones["status"] == "Available"]


def skill_match(pilot_skills, required):
    pilot = set(pilot_skills.split(","))
    req = set(required.split(","))
    return req.issubset(pilot)


def match_pilots_for_mission(mission_row):
    pilots = get_available_pilots()

    matches = []

    for _, p in pilots.iterrows():
        if skill_match(p["skills"], mission_row["required_skills"]):
            matches.append(p["name"])

    return matches

def match_drones_for_mission(mission):
    drones = read_sheet("drone_fleet")

    required_skill = mission["required_skills"]
    location = mission["location"]

    available = drones[
        (drones["status"] == "Available") &
        (drones["location"] == location) &
        (drones["capabilities"].str.contains(required_skill, case=False))
    ]

    return available["drone_id"].tolist()

def match_drones_for_mission(mission):
    drones = read_sheet("drone_fleet")

    required_caps = [
        c.strip().lower()
        for c in mission["required_skills"].split(",")
    ]

    mission_location = mission["location"].strip().lower()

    available = []

    for _, drone in drones.iterrows():
        # 1️⃣ Status check
        if drone["status"] != "Available":
            continue

        # 2️⃣ Capability check
        drone_caps = [
            c.strip().lower()
            for c in drone["capabilities"].split(",")
        ]
        if not all(cap in drone_caps for cap in required_caps):
            continue

        # 3️⃣ Location check
        if drone["location"].strip().lower() != mission_location:
            continue

        # 4️⃣ Maintenance date check
        if drone.get("maintenance_due"):
            if pd.to_datetime(drone["maintenance_due"]) <= pd.Timestamp.today():
                continue

        available.append(drone["drone_id"])

    return available
