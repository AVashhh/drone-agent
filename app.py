import streamlit as st
from sheets import read_sheet, update_pilot_status, assign_pilot_to_mission, assign_drone_to_mission
from scheduler import match_pilots_for_mission, match_drones_for_mission

st.title("Drone Operations Coordinator")

# -------------------------
# Session State Init
# -------------------------
if "matches" not in st.session_state:
    st.session_state.matches = []

# -------------------------
# Load Data
# -------------------------
missions = read_sheet("missions")
pilots = read_sheet("pilot_roster")

# =====================================================
# 1️⃣ MISSION → FIND MATCHING PILOTS
# =====================================================
st.header("Mission Assignment")

mission_id = st.selectbox(
    "Select Mission",
    missions["project_id"],
    key="mission_select"
)

if st.button("Find Matching Pilots", key="match_btn"):
    mission = missions[missions["project_id"] == mission_id].iloc[0]
    st.session_state.matches = match_pilots_for_mission(mission)

# Show results
if st.session_state.matches:
    st.success("Matching pilots found")

    selected_pilot = st.selectbox(
        "Select Pilot to Assign",
        st.session_state.matches,
        key="pilot_assign_select"
    )

    if st.button("Confirm Assignment", key="assign_btn"):
        assign_pilot_to_mission(selected_pilot, mission_id)
        st.success(f"{selected_pilot} assigned to {mission_id}")

# =====================================================
# 2️⃣ PILOT ROSTER MANAGEMENT
# =====================================================
st.header("Pilot Roster")

st.dataframe(pilots)

pilot_name = st.selectbox(
    "Select Pilot",
    pilots["name"],
    key="pilot_status_select"
)

new_status = st.selectbox(
    "Update Status",
    ["Available", "On Leave", "Unavailable"],
    key="status_select"
)

if st.button("Update Status", key="update_status_btn"):
    update_pilot_status(pilot_name, new_status)
    st.success("Status updated in Google Sheets!")

# =====================================================
# 3️⃣ DRONE INVENTORY
# =====================================================
st.header("Drone Assignment")

drones = read_sheet("drone_fleet")

st.dataframe(drones)

if st.button("Find Available Drones", key="find_drones_btn"):
    mission = missions[missions["project_id"] == mission_id].iloc[0]
    st.session_state.drone_matches = match_drones_for_mission(mission)

if "drone_matches" not in st.session_state:
    st.session_state.drone_matches = []

if st.session_state.drone_matches:
    selected_drone = st.selectbox(
        "Select Drone",
        st.session_state.drone_matches,
        key="drone_select"
    )

    if st.button("Assign Drone", key="assign_drone_btn"):
        assign_drone_to_mission(selected_drone, mission_id)
        st.success(f"{selected_drone} assigned to {mission_id}")
