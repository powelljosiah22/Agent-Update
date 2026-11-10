#!/bin/bash
# Silently syncs Canvas ICS calendar events into your dedicated Academic Google Calendar every week.
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

ENV_FILE="$HOME/Agents/Agent 0/.env"
if [ -f "$ENV_FILE" ]; then
  source "$ENV_FILE"
fi

if [ -z "$CANVAS_ICS_CALENDAR_ID" ] || [ -z "$ACADEMIC_CALENDAR_ID" ]; then
  echo "Please configure CANVAS_ICS_CALENDAR_ID and ACADEMIC_CALENDAR_ID in ~/Agents/Agent 0/.env first."
  exit 1
fi

agy --print "Weekly Canvas Sync: Use the gcalendar skill/CLI to fetch the next 14 days of events from the Canvas calendar ($CANVAS_ICS_CALENDAR_ID). Then fetch the next 14 days of events from the Academic calendar ($ACADEMIC_CALENDAR_ID). For any Canvas event that doesn't already exist in the Academic calendar, create the event on the Academic calendar. IMPORTANT: For Canvas all-day events (where end date is exclusive), convert the actual due date (start date) to 23:59:00 in America/New_York RFC3339 format." --dangerously-skip-permissions
