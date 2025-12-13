"""
WHITEBOARD CALENDAR CONFIGURATION
==================================

Customize the whiteboard calendar by editing these settings.
This makes it easy to change colors, refresh rates, and features without
touching the main code.
"""

# === EVENT COLORS ===
# Change these hex color codes to customize your calendar appearance

FLIGHT_COLORS = {
    'Scheduled': '#007bff',      # Blue - Standard scheduled flight
    'Dispatching': '#17a2b8',    # Cyan - Flight being prepared
    'OnTrip': '#20c997',         # Teal - Flight currently in air
    'Completed': '#28a745',      # Green - Flight finished
    'Cancelled': '#6c757d',      # Gray - Cancelled flight
    'Delayed': '#ffc107',        # Yellow - Delayed flight
    'Arrived': '#28a745',        # Green - Arrived at destination
    'Dispatched': '#0056b3',     # Dark Blue - Dispatched
}

EVENT_COLORS = {
    'flight': '#007bff',                    # Main flight color
    'flight_return': '#0056b3',             # Return flight color
    'crew_cabin': '#28a745',                # Cabin crew assignment
    'crew_flight': '#198754',               # Flight crew assignment
    'maintenance_due': '#dc3545',           # Maintenance urgent/due
    'maintenance_recommended': '#fd7e14',   # Maintenance recommended
    'maintenance_scheduled': '#6f42c1',     # Scheduled maintenance
}

# === EVENT ICONS/EMOJIS ===
# Customize the icons shown on calendar events

EVENT_ICONS = {
    'flight': '✈️',
    'flight_return': '↩️',
    'crew_cabin': '👤',
    'crew_flight': '✈️',
    'maintenance_due': '🔴',
    'maintenance_recommended': '🟠',
    'maintenance_scheduled': '🛠️',
}

# === DISPLAY SETTINGS ===

# Default view when calendar opens
DEFAULT_VIEW = 'timeGridWeek'  # Options: dayGridMonth, timeGridWeek, timeGridDay, listWeek

# Show weekends on calendar?
SHOW_WEEKENDS = True  # Set to False to hide Saturday/Sunday

# Working hours (24-hour format)
SLOT_MIN_TIME = '00:00:00'  # Start of day
SLOT_MAX_TIME = '24:00:00'  # End of day

# Default filters (what's shown when page loads)
DEFAULT_FILTERS = {
    'show_flights': True,
    'show_crew': True,
    'show_maintenance_due': True,
    'show_maintenance_recommended': True,
    'show_maintenance_scheduled': True,
}

# === PERFORMANCE SETTINGS ===

# How long to cache calendar data (in seconds)
CACHE_DURATION = 120  # 2 minutes

# Auto-refresh interval (in milliseconds)
AUTO_REFRESH_INTERVAL = 300000  # 5 minutes (300,000 ms)

# Maximum events to show at once (prevent overload)
MAX_EVENTS_PER_REQUEST = 1000

# Query optimization: How many days to look ahead for maintenance
MAINTENANCE_LOOKAHEAD_DAYS = 90  # 3 months

# === ALERT THRESHOLDS ===

# When to show warnings for maintenance hours
MAINTENANCE_HOURS_CRITICAL = 10   # Red alert
MAINTENANCE_HOURS_WARNING = 50    # Yellow alert

# When to show alerts for calendar-based maintenance (days before due)
CALENDAR_ALERT_CRITICAL = 7   # Show red if due within 7 days
CALENDAR_ALERT_WARNING = 30   # Show orange if due within 30 days

# === FEATURE FLAGS ===
# Turn features on/off easily

FEATURES = {
    'enable_quick_schedule': True,      # Allow scheduling from calendar clicks
    'enable_drag_drop': False,          # Allow dragging events to reschedule (advanced)
    'enable_conflict_detection': True,  # Warn about scheduling conflicts
    'enable_weather_integration': False,# Show weather forecasts (future feature)
    'enable_export': True,              # Allow exporting calendar to PDF/Excel
    'enable_notifications': False,      # Email/SMS notifications (future)
    'enable_crew_leave_display': True,  # Show approved leave requests
    'enable_resource_timeline': False,  # Show aircraft utilization timeline
}

# === CREW SCHEDULE SETTINGS ===

# Maximum flight hours per crew member per day
MAX_FLIGHT_HOURS_PER_DAY = 8

# Minimum rest time between flights (in hours)
MIN_REST_TIME_HOURS = 2

# Show crew availability indicators
SHOW_CREW_AVAILABILITY = True

# === MAINTENANCE SETTINGS ===

# Automatically calculate next maintenance date
AUTO_CALCULATE_NEXT_MAINTENANCE = True

# Maintenance types and their default durations (in hours)
MAINTENANCE_DURATIONS = {
    'Class_A': 24,   # A-check: 1 day
    'Class_B': 72,   # B-check: 3 days
    'Class_C': 168,  # C-check: 7 days
    'Class_D': 720,  # D-check: 30 days
}

# === TEXT CUSTOMIZATION ===

# Customize labels and messages
LABELS = {
    'whiteboard_title': 'Flight Operations Whiteboard',
    'no_events': 'No events scheduled for this period',
    'loading': 'Loading events...',
    'error_loading': 'Error loading calendar data',
    'confirm_delete': 'Are you sure you want to cancel this flight?',
    'confirm_schedule': 'Schedule a flight for this date?',
}

# === DATE FORMAT PREFERENCES ===

# How to display dates and times
DATE_FORMAT = '%Y-%m-%d'           # 2024-03-15
TIME_FORMAT = '%H:%M'              # 14:30
DATETIME_FORMAT = '%Y-%m-%d %H:%M' # 2024-03-15 14:30

# Timezone (use your local timezone)
DISPLAY_TIMEZONE = 'Africa/Kampala'  # Uganda time

# === MOBILE SETTINGS ===

# Optimize for mobile devices
MOBILE_FRIENDLY = True

# Show fewer events on mobile to improve performance
MOBILE_MAX_EVENTS = 50

# === LOGGING ===

# Log calendar operations for debugging
ENABLE_LOGGING = True

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = 'INFO'

# === INTEGRATION SETTINGS ===

# API endpoints for future integrations
WEATHER_API_URL = None  # Add when weather integration is ready
NOTIFICATION_SERVICE_URL = None  # Add when notifications are ready

# === ACCESS CONTROL ===

# Who can schedule flights from calendar?
CAN_SCHEDULE_FLIGHTS = ['Admin', 'IT_Admin']  # User rights that can schedule

# Who can schedule maintenance?
CAN_SCHEDULE_MAINTENANCE = ['Admin', 'IT_Admin']  # User rights

# Who can view the whiteboard?
CAN_VIEW_WHITEBOARD = ['Admin', 'IT_Admin', 'User']  # Everyone can view

# === EXPORT SETTINGS ===

# When exporting calendar to PDF/Excel
EXPORT_DATE_RANGE_DAYS = 30  # How many days to include in export
EXPORT_INCLUDE_DETAILS = True  # Include full details or just summary

# === TIPS FOR CUSTOMIZATION ===
"""
HOW TO USE THIS FILE:

1. Import in your views:
   from .whiteboard_config import FLIGHT_COLORS, FEATURES
   
2. Use the settings:
   if FEATURES['enable_quick_schedule']:
       # Show quick schedule button
   
3. Change colors easily:
   Just edit the hex codes above
   
4. Enable/disable features:
   Just change True to False in FEATURES dictionary

EXAMPLES:

# Change flight color from blue to purple:
FLIGHT_COLORS['Scheduled'] = '#6f42c1'

# Disable quick scheduling:
FEATURES['enable_quick_schedule'] = False

# Change cache duration to 5 minutes:
CACHE_DURATION = 300

# Show only weekdays:
SHOW_WEEKENDS = False
"""

# === COLOR PICKER REFERENCE ===
"""
Common hex colors you can use:

Blues:    #007bff, #0056b3, #17a2b8
Greens:   #28a745, #20c997, #198754  
Reds:     #dc3545, #c82333, #ff6b6b
Yellows:  #ffc107, #ff9800, #ffd700
Purples:  #6f42c1, #764ba2, #9b59b6
Grays:    #6c757d, #adb5bd, #495057
Orange:   #fd7e14, #ff7043

Or use any hex color from: https://htmlcolorcodes.com/
"""