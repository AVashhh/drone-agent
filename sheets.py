import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

# ---------------------------
# Google Auth (CACHED)
# ---------------------------

@st.cache_resource
def get_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope
    )
    return gspread.authorize(creds)


@st.cache_resource
def get_spreadsheet():
    client = get_client()
    return client.open("DroneAgentDB")


# ---------------------------
# Cached Readers
# ---------------------------

@st.cache_data(ttl=60)
def read_sheet(tab_name):
    ss = get_spreadsheet()
    sheet = ss.worksheet(tab_name)
    return pd.DataFrame(sheet.get_all_records())


# ---------------------------
# WRITE HELPERS (clear cache)
# ---------------------------

def update_pilot_status(name, new_status):
    ss = get_spreadsheet()
    sheet = ss.worksheet("pilot_roster")
    data = sheet.get_all_records()

    for i, row in enumerate(data):
        if row["name"] == name:
            col = list(row.keys()).index("status") + 1
            sheet.update_cell(i + 2, col, new_status)
            break

    st.cache_data.clear()


def assign_pilot_to_mission(name, mission_id):
    ss = get_spreadsheet()
    sheet = ss.worksheet("pilot_roster")
    data = sheet.get_all_records()

    for i, row in enumerate(data):
        if row["name"] == name:
            headers = list(row.keys())
            sheet.update_cell(i + 2, headers.index("status") + 1, "Busy")
            sheet.update_cell(i + 2, headers.index("current_assignment") + 1, mission_id)
            break

    st.cache_data.clear()


def assign_drone_to_mission(drone_id, mission_id):
    ss = get_spreadsheet()

    # ---- update drone_fleet ----
    drone_sheet = ss.worksheet("drone_fleet")
    drone_data = drone_sheet.get_all_records()

    for i, row in enumerate(drone_data):
        if row["drone_id"] == drone_id:
            headers = list(row.keys())
            drone_sheet.update_cell(i + 2, headers.index("status") + 1, "Deployed")
            drone_sheet.update_cell(i + 2, headers.index("current_assignment") + 1, mission_id)
            break

    # ---- update missions (CRITICAL) ----
    mission_sheet = ss.worksheet("missions")
    mission_data = mission_sheet.get_all_records()

    for i, row in enumerate(mission_data):
        if row["project_id"] == mission_id:
            headers = list(row.keys())
            mission_sheet.update_cell(i + 2, headers.index("assigned_drone") + 1, drone_id)
            break

    st.cache_data.clear()


def update_drone_status(drone_id, new_status):
    ss = get_spreadsheet()
    sheet = ss.worksheet("drone_fleet")
    data = sheet.get_all_records()

    for i, row in enumerate(data):
        if row["drone_id"] == drone_id:
            col = list(row.keys()).index("status") + 1
            sheet.update_cell(i + 2, col, new_status)
            break

    st.cache_data.clear()


# ---------------------------
# LOGIC HELPERS (NO API CALLS)
# ---------------------------

def flag_maintenance_issues(drones_df):
    return drones_df[drones_df["status"].str.lower() == "maintenance"]


def check_pilot_double_booking(pilots, missions):
    conflicts = []

    missions["start_date"] = pd.to_datetime(missions["start_date"])
    missions["end_date"] = pd.to_datetime(missions["end_date"])

    for _, pilot in pilots.iterrows():
        if not pilot["current_assignment"] or pilot["current_assignment"] == "–":
            continue

        current = missions[missions["project_id"] == pilot["current_assignment"]]
        if current.empty:
            continue

        current = current.iloc[0]

        for _, m in missions.iterrows():
            if m["project_id"] == current["project_id"]:
                continue

            if (
                m["start_date"] <= current["end_date"]
                and m["end_date"] >= current["start_date"]
            ):
                conflicts.append({
                    "pilot": pilot["name"],
                    "assigned_mission": current["project_id"],
                    "conflicting_mission": m["project_id"]
                })

    return conflicts



def check_skill_cert_mismatch(pilots, missions):
    mismatches = []

    for _, pilot in pilots.iterrows():
        if not pilot["current_assignment"] or pilot["current_assignment"] == "–":
            continue

        mission = missions[missions["project_id"] == pilot["current_assignment"]]
        if mission.empty:
            continue

        mission = mission.iloc[0]

        req_skills = set(map(str.strip, mission["required_skills"].lower().split(",")))
        pilot_skills = set(map(str.strip, pilot["skills"].lower().split(",")))

        req_certs = set(map(str.strip, mission["required_certs"].lower().split(",")))
        pilot_certs = set(map(str.strip, pilot["certifications"].lower().split(",")))

        for skill in req_skills - pilot_skills:
            mismatches.append({
                "pilot": pilot["name"],
                "mission": mission["project_id"],
                "issue": f"Missing skill: {skill}"
            })

        for cert in req_certs - pilot_certs:
            mismatches.append({
                "pilot": pilot["name"],
                "mission": mission["project_id"],
                "issue": f"Missing certification: {cert}"
            })

    return mismatches



def check_location_mismatch(pilots, missions, drones):
    issues = []

    for _, mission in missions.iterrows():
        if not mission.get("assigned_drone") or mission["assigned_drone"] == "–":
            continue

        drone = drones[drones["drone_id"] == mission["assigned_drone"]]
        if drone.empty:
            continue

        drone = drone.iloc[0]

        if drone["location"].strip().lower() != mission["location"].strip().lower():
            issues.append({
                "mission": mission["project_id"],
                "drone": drone["drone_id"],
                "issue": "Drone location mismatch"
            })

    return issues


def check_drone_double_booking(drones, missions):
    conflicts = []

    missions["start_date"] = pd.to_datetime(missions["start_date"])
    missions["end_date"] = pd.to_datetime(missions["end_date"])

    for _, drone in drones.iterrows():
        if not drone["current_assignment"] or drone["current_assignment"] == "–":
            continue

        assigned = missions[missions["project_id"] == drone["current_assignment"]]
        if assigned.empty:
            continue

        assigned = assigned.iloc[0]

        for _, m in missions.iterrows():
            if m["project_id"] == assigned["project_id"]:
                continue

            if (
                m["start_date"] <= assigned["end_date"]
                and m["end_date"] >= assigned["start_date"]
            ):
                conflicts.append({
                    "drone": drone["drone_id"],
                    "assigned_mission": assigned["project_id"],
                    "conflicting_mission": m["project_id"]
                })

    return conflicts



def check_drone_maintenance_conflict(missions, drones):
    issues = []

    for _, mission in missions.iterrows():
        if not mission.get("assigned_drone") or mission["assigned_drone"] == "–":
            continue

        drone = drones[drones["drone_id"] == mission["assigned_drone"]]
        if drone.empty:
            continue

        drone = drone.iloc[0]

        if drone["status"].lower() == "maintenance":
            issues.append({
                "mission": mission["project_id"],
                "drone": drone["drone_id"],
                "issue": "Drone under maintenance"
            })

    return issues
