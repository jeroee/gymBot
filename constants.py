q1 = "Hello, which day are you planning to gym?"
q2 = "Which session are you planning to gym?"
q3 = "What time are you planning to gym?"
q4 = "What will you be training?"

QUOTE_FILE = 'quotes.txt'

# Constants for callback data patterns
BACK_PATTERN = "^Back$"
DONE_PATTERN = "^Done$"
CONFIRM_PATTERN = "^Confirm$"
EXIT_PATTERN = "^Exit$"
SCHEDULE_PATTERN = "^Schedule a session$"
VIEW_SESSIONS_PATTERN = "^View my sessions$"

# Define your states for better readability
MENU, MY_SESSIONS, REMOVAL, DAY_CHOICE, PERIOD_CHOICE, TIME_CHOICE, EXERCISE_CHOICE, CONFIRMATION = range(8)

# after 9pm, there will not be displays for similar gym timings
CUT_OFF_HOUR = 21

todo_exercises = []

time_period = ''

user_entry = {
    "telegram_id": None,
    "group_id": None,
    "telegram_username": None,
    "first_name": None,
    "date": None,
    "day": None,
    "time": None,
    "date_time": None,
    "workout": None
}

session_remove = {
    "id": None,
    "name": None
}

# Define available time slots
time_slots = {
    'Morning': [700, 730, 800, 830, 900, 930, 1000, 1030, 1100, 1130],
    'Afternoon': [1200, 1230, 1300, 1330, 1400, 1430, 1500, 1530, 1600, 1630],
    'Evening': [1700, 1730, 1800, 1830, 1900, 1930, 2000, 2030, 2100, 2130]
}

exercises = ['Chest workout', 'Shoulders workout',
            'Back workout', 'Legs workout', 'Arms workout', 'Abs workout']