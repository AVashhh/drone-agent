Drone Operations Coordinator AI Agent

An AI-assisted operations coordinator for managing pilots, drones, and missions across multiple client projects.
The system reduces manual coordination by automating assignment matching, conflict detection, and fleet tracking using a conversational, human-in-the-loop interface.

Features
1. Pilot Roster Management

View pilot availability, skills, certifications, and locations

Update pilot status (Available / On Leave / Unavailable)

Syncs updates back to Google Sheets (2-way)

2. Assignment Tracking

Match pilots to missions based on skills, certifications, location, and availability

Assign pilots to missions

Track current assignments

Supports reassignment workflows

3. Drone Inventory Management

View drone fleet with capabilities, location, and status

Match drones to missions based on required capabilities

Track deployment status

Flag drones under maintenance

Syncs drone status updates back to Google Sheets

4. Conflict Detection

Pilot double-booking detection (overlapping mission dates)

Drone double-booking detection

Skill and certification mismatch warnings

Pilot–drone–mission location mismatch alerts

Maintenance conflicts (drone assigned while under maintenance)

5. Conversational Agent Interface

Guided, multi-step interaction via Streamlit

Context-aware responses using session state

Clear success, warning, and error feedback

Human-in-the-loop decision making

Component Breakdown
1️⃣ Streamlit UI (app.py)

Acts as the conversational interface

Handles user interaction:

Mission selection

Pilot and drone assignment

Status updates

Displays:

Tables

Warnings

Conflict reports

Maintains context using st.session_state

2️⃣ Agent Logic Layer
scheduler.py

Responsible for decision making:

match_pilots_for_mission()
Matches pilots using:

Required skills

Required certifications

Location

Availability

match_drones_for_mission()
Matches drones using:

Capabilities

Location

Availability

Maintenance status

This layer contains no Google Sheets calls, enabling clean separation of logic and data.

Conflict Detection (sheets.py)

Implements rule-based checks:

Pilot double booking

Drone double booking

Skill & certification mismatches

Location mismatches

Maintenance conflicts

Returns structured conflict objects for UI display.

3️⃣ Data Layer (sheets.py)

Google Sheets acts as the single source of truth

2-way sync using gspread

Cached reads to prevent quota exhaustion

Explicit cache clearing on writes

Sheets Used:

pilot_roster

missions

drone_fleet

🔄 Data Flow

User selects a mission in the UI

Agent fetches cached data from Google Sheets

Matching logic evaluates pilots/drones

Conflicts are detected and surfaced

User confirms assignment

Updates are written back to Google Sheets

Cache is cleared and UI refreshes

⚠️ Error Handling & Edge Cases

Prevents pilot or drone double booking

Flags missing skills or certifications

Detects drone maintenance conflicts

Identifies location mismatches

Graceful warnings instead of hard failures

🔥 Urgent Reassignments (Design Intent)

Urgent missions can be prioritized by:

Allowing reassignment even if pilots or drones are currently busy

Highlighting conflicts instead of blocking actions

Keeping the human operator in control
