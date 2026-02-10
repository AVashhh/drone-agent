import streamlit as st
import pandas as pd

from sheets import (
    read_sheet,
    update_pilot_status,
    assign_pilot_to_mission,
    assign_drone_to_mission,
    update_drone_status,
    flag_maintenance_issues,
    check_pilot_double_booking,
    check_skill_cert_mismatch,
    check_location_mismatch
)

from scheduler import match_pilots_for_mission, match_drones_for_mission

st.title("Drone Operations Coordinator")

# -------------------------
# Load Data ONCE
# -------------------------
missions = read_sheet("missions")
pilots = read_sheet("pilot_roster")
drones = read_sheet("drone_fleet")

# -------------------------
# Mission Assignment
# -------------------------
st.header("Mission Assignment")

mission_id = st.selectbox("Select Mission", missions["project_id"])
mission = missions[missions["project_id"] == mission_id].iloc[0]

if st.button("Find Matching Pilots"):
    matches = match_pilots_for_mission(mission)
    st.session_state.matches = matches

if "matches" in st.session_state and st.session_state.matches:
    selected_pilot = st.selectbox("Select Pilot", st.session_state.matches)

    if st.button("Confirm Assignment"):
        assign_pilot_to_mission(selected_pilot, mission_id)
        st.success("Pilot assigned")

# -------------------------
# Pilot Roster
# -------------------------
st.header("Pilot Roster")
st.dataframe(pilots)

pilot_name = st.selectbox("Select Pilot", pilots["name"])
new_status = st.selectbox("Update Status", ["Available", "On Leave", "Unavailable"])

if st.button("Update Pilot Status"):
    update_pilot_status(pilot_name, new_status)
    st.success("Pilot status updated")

# -------------------------
# Drone Assignment
# -------------------------
st.header("Drone Inventory")
st.dataframe(drones)

if st.button("Find Available Drones"):
    st.session_state.drone_matches = match_drones_for_mission(mission)

if "drone_matches" in st.session_state and st.session_state.drone_matches:
    selected_drone = st.selectbox("Select Drone", st.session_state.drone_matches)

    if st.button("Assign Drone"):
        assign_drone_to_mission(selected_drone, mission_id)
        st.success("Drone assigned")

# -------------------------
# Maintenance
# -------------------------
maintenance = flag_maintenance_issues(drones)
if not maintenance.empty:
    st.warning("Drones needing maintenance")
    st.dataframe(maintenance)

# -------------------------
# Conflict Detection
# -------------------------
st.header("Conflict Detection")

pilot_conflicts = check_pilot_double_booking(pilots, missions)
skill_issues = check_skill_cert_mismatch(pilots, missions)
location_issues = check_location_mismatch(pilots, missions, drones)

if pilot_conflicts:
    st.warning("Pilot double booking")
    st.dataframe(pd.DataFrame(pilot_conflicts))

if skill_issues:
    st.warning("Skill mismatches")
    st.dataframe(pd.DataFrame(skill_issues))

if location_issues:
    st.warning("Location mismatches")
    st.dataframe(pd.DataFrame(location_issues))

if not (pilot_conflicts or skill_issues or location_issues):
    st.success("No conflicts detected")
