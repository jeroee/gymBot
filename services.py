from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler
)
from datetime import datetime, timedelta, date
from bson.objectid import ObjectId
import utils

# Helper Services
def get_group_id(update):
    """Return the group ID from the update."""
    return update.message.chat.id if update.callback_query is None else update.callback_query.message.chat.id

def format_schedule_entry(entry):
    """Format a single schedule entry for display."""
    return f' 🏋️‍♀️{entry["name"]:<10}- {", ".join(entry["workout"])}\n'

def build_timetable(schedules):
    """Build a timetable dictionary from the schedule entries."""
    timetable = {}
    for schedule in schedules:
        schedule_time = utils.hour_24_to_time(schedule['time'])
        schedule_date = schedule['date']
        if schedule_date not in timetable:
            timetable[schedule_date] = {}

        if schedule_time not in timetable[schedule_date]:
            timetable[schedule_date][schedule_time] = []

        timetable[schedule_date][schedule_time].append({
            'name': schedule['first_name'],
            'day': schedule['day'],
            'workout': schedule['workout']
        })
    
    return timetable

def format_schedule_display(timetable):
    """Format the timetable for display."""
    schedule_display = "This is the group's gym schedule for the next few days:\n\n"
    for date, times in timetable.items():
        # Display date and day
        schedule_display += f'<b>{date} ({list(times.values())[0][0]["day"]})</b> \n\n'
        for time, entries in times.items():
            # Display time
            schedule_display += f'{time} \n'
            # Display each entry
            schedule_display += ''.join([format_schedule_entry(entry) for entry in entries])
            schedule_display += "\n"
        schedule_display += "\n"
    return schedule_display

def all_views(update, user_activity):
    """Generate and return the gym schedule view."""
    group_id = get_group_id(update)
    current_date_and_time = datetime.now()

    # Fetch schedules for the group after current time
    schedules = user_activity.find(
        {'date_time': {"$gte": current_date_and_time}, 'group_id': group_id}
    ).sort('date_time')

    # Build the timetable
    timetable = build_timetable(schedules)

    if timetable:
        return format_schedule_display(timetable)
    else:
        return 'Nothing is scheduled in the next few days... 🙁\nFeel free to schedule a session.\n'

def my_view(update, user_activity):
    query = update.callback_query
    telegram_id = query['from'].id
    group_id = update.callback_query.message.chat.id
    current_date_time = datetime.now()

    # Fetch schedules from the database
    schedules = user_activity.find(
        {'date_time': {"$gte": current_date_time}, 'group_id': group_id, 'telegram_id': telegram_id}).sort('date_time')
    
    timetable = {}
    keyboard = []
    schedule_display = "This is your upcoming schedule in the next few days:\n\n" if schedules else "You have nothing scheduled in the next few days... 🙁"
    print('schedules')
    print(schedules)
    # Process each schedule and build the timetable and keyboard
    for s in schedules:
        date = s['date']
        time = utils.hour_24_to_time(s['time'])
        day = s['day']
        workout = ', '.join(s['workout'])
        schedule_button = InlineKeyboardButton(
            f"{date} ({day[:3]}) {time} - {workout}", callback_data=f"{s['_id']}")
        
        # Add to timetable and keyboard
        if date not in timetable:
            timetable[date] = {}
        
        if time not in timetable[date]:
            timetable[date][time] = []

        timetable[date][time].append({'_id': s['_id'], 'day':day, 'name': s['first_name'], 'workout': s['workout']})
        keyboard.append([schedule_button])

    # Build schedule display
    print(f'timetable: {timetable}')
    for date, times in timetable.items():
        schedule_display += f'<b>{date} ({list(times.values())[0][0]["day"]})</b>\n\n'
        for time, entries in times.items():
            schedule_display += f"{time}\n"
            for entry in entries:
                schedule_display += f" 🏋️‍♀️{entry['name']:<10} {', '.join(entry['workout'])}\n"
            schedule_display += "\n"
        schedule_display += "\n"

    # Add back button to the keyboard
    keyboard.append([InlineKeyboardButton("⏎", callback_data="Back")])

    return schedule_display, keyboard


def get_days(cut_off_time):
    """Return the next few days with dates and weekdays."""
    current_time = datetime.now()
    current_hour = current_time.hour
    today = date.today()

    # Define the weekdays for easier access
    weekdays = ["()", "(Monday)", "(Tuesday)", "(Wednesday)",
                "(Thursday)", "(Friday)", "(Saturday)", "(Sunday)"]

    # Determine the days to return based on the cutoff time
    days = []
    if current_hour < cut_off_time:
        day_range = [today, today + timedelta(days=1), today + timedelta(days=2)]
    else:
        day_range = [today + timedelta(days=1), today + timedelta(days=2), today + timedelta(days=3)]

    # Format the days with their respective weekday names
    for day in day_range:
        formatted_day = day.strftime("%d %B %Y") + " " + weekdays[day.isoweekday()]
        days.append(formatted_day)

    return days

def insert_activity_to_db(user_activity, user_entry):
    """Inserts the user activity into the database."""
    global todo_exercises
    todo_exercises = []  # Reset todo_exercises after insertion

    # Prepare the datetime object
    user_entry['_id'] = ObjectId()
    datetime_str = f"{user_entry['date']} {user_entry['time']}"
    datetime_object = datetime.strptime(datetime_str, '%d %B %Y %H%M')
    user_entry['date_time'] = datetime_object
    
    print(user_entry)  # Optionally log the user entry
    user_activity.insert_one(user_entry)  # Insert into the database