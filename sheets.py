import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

# ---------------------------
# Google Auth
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
# Write Helpers (CLEAR CACHE)
# ---------------------------

def update_pilot_status(name, new_status):
    ss = get_spreadsheet()
    sheet = ss.worksheet("pilot_roster")
    data = sheet.get_all_records()

    for i, row in enumerate(data):
        if row["name"] == name:
            status_col = list(row.keys()).index("status") + 1
            sheet.update_cell(i + 2, status_col, new_status)
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
    sheet = ss.worksheet("drone_fleet")
    data = sheet.get_all_records()

    for i, row in enumerate(data):
        if row["drone_id"] == drone_id:
            headers = list(row.keys())
            sheet.update_cell(i + 2, headers.index("status") + 1, "Deployed")
            sheet.update_cell(i + 2, headers.index("current_assignment") + 1, mission_id)
            break

    st.cache_data.clear()


def update_drone_status(drone_id, new_status):
    ss = get_spreadsheet()
    sheet = ss.worksheet("drone_fleet")
    data = sheet.get_all_records()

    for i, row in enumerate(data):
        if row["drone_id"] == drone_id:
            status_col = list(row.keys()).index("status") + 1
            sheet.update_cell(i + 2, status_col, new_status)
            break

    st.cache_data.clear()


# ---------------------------
# Logic Helpers (NO SHEET CALLS)
# ---------------------------

def flag_maintenance_issues(drones_df):
    return drones_df[drones_df["status"].str.lower() == "maintenance"]


def check_pilot_double_booking(pilots, missions):
    conflicts = []

    for _, pilot in pilots.iterrows():
        if pilot["current_assignment"]:
            assigned = missions[missions["project_id"] == pilot["current_assignment"]]
            if assigned.empty:
                continue

            a = assigned.iloc[0]
            for _, m in missions.iterrows():
                if m["project_id"] != a["project_id"]:
                    if pd.to_datetime(m["start_date"]) <= pd.to_datetime(a["end_date"]) \
                       and pd.to_datetime(m["end_date"]) >= pd.to_datetime(a["start_date"]):
                        conflicts.append({
                            "pilot": pilot["name"],
                            "assigned_mission": a["project_id"],
                            "conflicting_mission": m["project_id"]
                        })
    return conflicts


def check_skill_cert_mismatch(pilots, missions):
    mismatches = []

    for _, pilot in pilots.iterrows():
        if pilot["current_assignment"]:
            mission = missions[missions["project_id"] == pilot["current_assignment"]]
            if mission.empty:
                continue

            mission = mission.iloc[0]
            required = set(mission["required_skills"].lower().split(","))
            skills = set(pilot["skills"].lower().split(","))

            for skill in required - skills:
                mismatches.append({
                    "pilot": pilot["name"],
                    "mission": mission["project_id"],
                    "missing_skill": skill.strip()
                })
    return mismatches


def check_location_mismatch(pilots, missions, drones):
    issues = []

    for _, pilot in pilots.iterrows():
        if pilot["current_assignment"]:
            mission = missions[missions["project_id"] == pilot["current_assignment"]]
            if mission.empty:
                continue

            mission = mission.iloc[0]
            assigned_drones = drones[drones["current_assignment"] == mission["project_id"]]

            for _, drone in assigned_drones.iterrows():
                if drone["location"].lower() != mission["location"].lower():
                    issues.append({
                        "pilot": pilot["name"],
                        "drone": drone["drone_id"],
                        "mission": mission["project_id"],
                        "issue": "Location mismatch"
                    })

    return issues
