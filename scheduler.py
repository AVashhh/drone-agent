from sheets import read_sheet


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
