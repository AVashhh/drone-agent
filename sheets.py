import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# ---------------------------
# Google Auth
# ---------------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)

client = gspread.authorize(creds)

SPREADSHEET_NAME = "DroneAgentDB"   # ⭐ YOUR FILE NAME


# ---------------------------
# Generic Readers
# ---------------------------

def read_sheet(tab_name):
    """
    Reads any tab inside DroneAgentDB and returns pandas DataFrame
    Example: read_sheet("pilot_roster")
    """
    sheet = client.open(SPREADSHEET_NAME).worksheet(tab_name)
    return pd.DataFrame(sheet.get_all_records())


def get_sheet(tab_name):
    return client.open(SPREADSHEET_NAME).worksheet(tab_name)


# ---------------------------
# Generic Updater
# ---------------------------

def update_cell(tab_name, row, col, value):
    sheet = get_sheet(tab_name)
    sheet.update_cell(row, col, value)


# ---------------------------
# Pilot Functions
# ---------------------------

def update_pilot_status(name, new_status):
    sheet = get_sheet("pilot_roster")

    data = sheet.get_all_records()

    for i, row in enumerate(data):
        if row["name"] == name:
            headers = list(row.keys())
            status_col = headers.index("status") + 1
            sheet.update_cell(i + 2, status_col, new_status)
            break


def assign_pilot_to_mission(name, mission_id):
    sheet = get_sheet("pilot_roster")

    data = sheet.get_all_records()

    for i, row in enumerate(data):
        if row["name"] == name:
            headers = list(row.keys())

            status_col = headers.index("status") + 1
            assignment_col = headers.index("current_assignment") + 1

            sheet.update_cell(i + 2, status_col, "Busy")
            sheet.update_cell(i + 2, assignment_col, mission_id)
            break

def assign_drone_to_mission(drone_id, mission_id):
    sheet = client.open("DroneAgentDB").worksheet("drone_fleet")

    data = sheet.get_all_records()

    for i, row in enumerate(data):
        if row["drone_id"] == drone_id:
            row_index = i + 2

            headers = list(row.keys())

            status_col = headers.index("status") + 1
            assignment_col = headers.index("current_assignment") + 1

            sheet.update_cell(row_index, status_col, "Deployed")
            sheet.update_cell(row_index, assignment_col, mission_id)

            break
