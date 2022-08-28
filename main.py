from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)
from pymongo import MongoClient
import re
import os
from dotenv import load_dotenv
from datetime import date, timedelta, datetime
from bson.objectid import ObjectId

# -------------------------------------------------------------------
# to remove the warnings triggered by CallBackQueryHandler
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler",
               category=PTBUserWarning)
# -------------------------------------------------------------------
load_dotenv()
API_KEY = os.getenv('API_KEY')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')

connection_string = f'mongodb+srv://{USERNAME}:{PASSWORD}@cluster0.avfgdjd.mongodb.net/?retryWrites=true&w=majority'
client = MongoClient(connection_string)
db = client[DB_NAME]
user_activity = db[COLLECTION_NAME]

# print(db.list_collection_names())

q1 = "Hello, which day are you planning to gym?"
q2 = "Which session are you planning to gym?"
q3 = "What time are you planning to gym?"
q4 = "What will you be training?"

cutOffHour = 20
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
MENU, DAY_CHOICE, PERIOD_CHOICE, TIME_CHOICE, EXERCISE_CHOICE, CONFIRMATION = range(
    6)


def getCurrentHourMin():
    currentDateAndTime = datetime.now()
    currentHourMin = int(currentDateAndTime.strftime("%H%m"))
    return currentHourMin


def timeTo24Hour(time):
    am_pm = time[-2:]
    time = time.replace(am_pm, "").split(":")
    if am_pm == 'PM' and int(time[0]) != 12:
        time[0] = str(int(time[0])+12)
    time[0] = str(int(time[0]))
    if len(time[0]) == 1:
        time[0] = '0'+time[0]
    output = ''.join(time)
    return output


def Hour24ToTime(time):
    hr = int(time[:2])
    min = time[2:]
    if hr >= 12:
        am_pm = "PM"
        if hr > 12:
            hr -= 12
    elif hr < 12:
        am_pm = "AM"
    time_output = str(hr)+":"+str(min)+am_pm
    return time_output


def getDays(cutOffTime):
    currentDateAndTime = datetime.now()
    today = date.today()
    currentHour = currentDateAndTime.strftime("%H")
    day_0 = date.today()
    day_1 = date.today() + timedelta(days=1)
    day_2 = date.today() + timedelta(days=2)
    day_3 = date.today() + timedelta(days=3)
    # print(currentHour)
    # print(cutOffTime)
    # print(day_0.isoweekday(), day_1.isoweekday(), day_2.isoweekday())

    weekdays = ["()", "(Monday)", "(Tuesday)", "(Wednesday)",
                "(Thursday)", "(Friday)", "(Saturday)", "(Sunday)"]
    # print(weekdays[day_0.isoweekday()],
    #       weekdays[day_1.isoweekday()], weekdays[day_2.isoweekday()])

    if int(currentHour) < cutOffTime:
        days = [day_0.strftime("%d %B %Y") + " " + weekdays[day_0.isoweekday()],
                day_1.strftime("%d %B %Y") + " " +
                weekdays[day_1.isoweekday()],
                day_2.strftime("%d %B %Y") + " " + weekdays[day_2.isoweekday()]]
    else:
        days = [day_1.strftime("%d %B %Y") + " " + weekdays[day_1.isoweekday()],
                day_2.strftime("%d %B %Y") + " " +
                weekdays[day_2.isoweekday()],
                day_3.strftime("%d %B %Y") + " " + weekdays[day_3.isoweekday()]]
    return days


def has_numbers(inputString):
    return bool(re.search(r'\d', inputString))


def views(update):
    group_id = update.message.chat.id
    currentDateAndTime = datetime.now()
    schedules = user_activity.find(
        {'date_time': {"$gte": currentDateAndTime}, 'group_id': group_id}).sort('date_time')
    timetable = {}
    schedule_display = ""
    if schedules is not None:
        for s in schedules:
            if s['date'] not in timetable.keys():
                timetable[s['date']] = {Hour24ToTime(
                    s['time']): [{'name': s['first_name'], 'day':s['day'], 'workout':s['workout']}]}
            elif s['date'] in timetable.keys():
                if Hour24ToTime(s['time']) not in timetable[s['date']].keys():
                    timetable[s['date']][Hour24ToTime(s['time'])] = [
                        {'name': s['first_name'], 'day':s['day'], 'workout':s['workout']}]
                elif Hour24ToTime(s['time']) in timetable[s['date']].keys():
                    timetable[s['date']][Hour24ToTime(s['time'])].append(
                        {'name': s['first_name'], 'day': s['day'], 'workout': s['workout']})

        schedule_display += f"This is the group's gym schedule for the next few days:\n\n"
        for k, v in timetable.items():
            # date and day
            schedule_display += f'<b>{k} ({list(v.values())[0][0]["day"]})</b> \n\n'
            for i, j in v.items():
                # time
                schedule_display += f'{i} \n'
                for entry in j:
                    # name and workout
                    schedule_display += f' 🏋️‍♀️{entry["name"]:<10} {", ".join(entry["workout"])}\n'
                schedule_display += "\n"
            schedule_display += "\n"
    elif schedules is None:
        schedule_display += f'Nothing is scheduled in the next few days... 🙁'
    return schedule_display


async def quick_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('quick view mode')
    schedule_display = views(update)
    message = f"Hi welcome to gymBot QuickView. \n\n{schedule_display}To create or manage your schedule, type '/gym' in the chat"
    await update.message.reply_text(message, parse_mode=constants.ParseMode.HTML)
    return ConversationHandler.END


async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('start menu mode')
    schedule_display = views(update)
    message = f"Hi welcome to gymBot. \n\n{schedule_display} \n"
    keyboard0 = [
        [InlineKeyboardButton("Schedule a session",
                              callback_data="Schedule a session")],
        [InlineKeyboardButton(
            "Edit a session", callback_data="Edit a session")],
        [InlineKeyboardButton("More Info", callback_data="More Info")],
        [InlineKeyboardButton("Exit", callback_data="Exit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard0)
    await update.message.reply_text(message, parse_mode=constants.ParseMode.HTML, reply_markup=reply_markup)
    return MENU


async def day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    day_1, day_2, day_3 = getDays(cutOffHour)
    keyboard1 = [
        [InlineKeyboardButton(day_1, callback_data=day_1)],
        [InlineKeyboardButton(day_2, callback_data=day_2)],
        [InlineKeyboardButton(day_3, callback_data=day_3)],
        [InlineKeyboardButton("Back", callback_data="Back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard1)
    # Send message with text and appended InlineKeyboard
    # if query is None:
    #     await update.message.reply_text(q1, reply_markup=reply_markup)
    # elif query is not None:
    await query.edit_message_text(
        text=q1, reply_markup=reply_markup
    )
    # Tell ConversationHandler that we're in state `FIRST` now
    return DAY_CHOICE


async def period_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data != 'Back':
        today = query.data.split(" ")[-1].replace("(", "").replace(")", "")
        today_date = " ".join(query.data.split(" ")[:-1])
        telegram_username = query['from'].username
        telegram_id = query['from'].id
        first_name = query['from'].first_name
        group_id = query['message']['chat'].id

        # update user_entry
        user_entry['telegram_id'] = telegram_id
        user_entry['group_id'] = group_id
        user_entry['telegram_username'] = telegram_username
        user_entry['first_name'] = first_name
        user_entry['day'] = today
        user_entry['date'] = today_date

    elif query.data == 'Back':
        today_date = user_entry['date']
        today = user_entry['day']

    keyboard2 = [
        [InlineKeyboardButton('Morning', callback_data='Morning')],
        [InlineKeyboardButton('Afternoon', callback_data='Afternoon')],
        [InlineKeyboardButton('Evening', callback_data='Evening')],
        [InlineKeyboardButton("Back", callback_data="Back")]
    ]
    currentHourMin = getCurrentHourMin()
    currentDay = date.today()
    DaySelected = datetime.strptime(today_date, "%d %B %Y").date()
    if currentDay == DaySelected:
        if currentHourMin >= 1130 and currentHourMin < 1630:
            keyboard2 = keyboard2[1:]
        elif currentHourMin >= 1630:
            keyboard2 = keyboard2[2:]

    reply_markup = InlineKeyboardMarkup(keyboard2)
    await query.answer()
    await query.edit_message_text(
        text=f'You have selected to gym on {today}, {today_date}. {q2}', reply_markup=reply_markup
    )
    return PERIOD_CHOICE


async def time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    currentHourMin = getCurrentHourMin()
    currentDay = date.today()
    today_date = user_entry['date']
    today = user_entry['day']
    DaySelected = datetime.strptime(today_date, "%d %B %Y").date()

    # allows function to operate with 'back' input data
    global time_period
    global todo_exercises
    if query.data != 'Back':
        period = query.data
        time_period = period
    elif query.data == 'Back':
        period = time_period
        todo_exercises = []

    morning = [700, 730, 800, 830, 900, 930, 1000, 1030, 1100, 1130]
    afternoon = [1200, 1230, 1300, 1330, 1400, 1430, 1500, 1530, 1600, 1630]
    evening = [1700, 1730, 1800, 1830, 1900, 1930, 2000, 2030, 2100, 2130]

    if period == 'Morning':
        # if selected today, remove anytime stamp that is earlier than current time.
        print(period)
        if currentDay == DaySelected:
            print(f'currentHourMin: {currentHourMin}')
            print(morning)
            for t in morning:
                print(f'times: {t}')
                if currentHourMin >= t:
                    morning.remove(t)
        times = morning
    elif period == 'Afternoon':
        if currentDay == DaySelected:
            for time in afternoon:
                if currentHourMin >= time:
                    afternoon.remove(time)
        times = afternoon
    elif period == 'Evening':
        if currentDay == DaySelected:
            for time in evening:
                if currentHourMin >= time:
                    evening.remove(time)
        times = evening
    keyboard3 = []
    # morning timeslots
    if times[-1] == 1130:
        for time in times:
            time = str(time)
            time_str = time[:-2]+':'+time[-2:]+'AM'
            keyboard3.append([time_str])

    # afternonn or evening timeslots
    else:
        for time in times:
            time = str(time)
            new_hour = int(time[:-2])
            if new_hour != 12:
                time_str = str(new_hour-12)+':'+time[-2:]+'PM'
            elif new_hour == 12:
                time_str = time[:-2]+':'+time[-2:]+'PM'
            keyboard3.append([time_str])

    keyboard3.append(['Back'])

    keyboard3_clone = keyboard3.copy()
    keyboard3 = []
    for item in keyboard3_clone:
        keyboard3.append(
            [InlineKeyboardButton(item[0], callback_data=item[0])])
    reply_markup = InlineKeyboardMarkup(keyboard3)
    await query.edit_message_text(
        text=f'You have selected to gym on {today}, {today_date}, {period.lower()} session. {q3}', reply_markup=reply_markup
    )
    return TIME_CHOICE


async def exercise_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'Back':
        time_selected = Hour24ToTime(user_entry['time'])
    elif has_numbers(query.data) is True:
        time_selected = query.data
        time_24hour = timeTo24Hour(time_selected)
        user_entry['time'] = time_24hour

    elif has_numbers(query.data) is False:
        time_selected = Hour24ToTime(user_entry['time'])
        exercise_selected = query.data
        if exercise_selected not in todo_exercises:
            todo_exercises.append(exercise_selected)
        elif exercise_selected in todo_exercises:
            todo_exercises.remove(exercise_selected)

    exercises = ['Chest workout', 'Shoulders workout',
                 'Back workout', 'Legs workout', 'Arms workout', 'Abs workout']
    keyboard4 = []
    for ex in exercises:
        keyboard4.append([ex])

    today = user_entry['day']
    today_date = user_entry['date']

    exercise_response = ''
    if len(todo_exercises) != 0:
        keyboard4.insert(0, ['Done'])
        for ex in todo_exercises:
            exercise_response += f"\n - {ex.split(' ')[0]}"

    keyboard4.append(['Back'])
    keyboard4_clone = keyboard4.copy()
    keyboard4 = []
    for item in keyboard4_clone:
        keyboard4.append(
            [InlineKeyboardButton(item[0], callback_data=item[0])])
    reply_markup = InlineKeyboardMarkup(keyboard4)

    await query.answer()
    await query.edit_message_text(
        text=f'You have selected to gym on {today}, {today_date} at {time_selected}. {q4} \n (You may choose more than one workout) \n {exercise_response}', reply_markup=reply_markup
    )
    return EXERCISE_CHOICE


async def confirm_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    today = user_entry['day']
    today_date = user_entry['date']
    time_selected = Hour24ToTime(user_entry['time'])
    exercise_response = ""
    for ex in todo_exercises:
        exercise_response += f"\n - {ex.split(' ')[0]}"

    user_entry['workout'] = [ex.split(' ')[0] for ex in todo_exercises]

    keyboard5 = [
        [InlineKeyboardButton('Confirm', callback_data='Confirm')],
        [InlineKeyboardButton('Back', callback_data='Back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard5)

    await query.answer()
    await query.edit_message_text(
        text=f'You have selected to gym on {today}, {today_date} at {time_selected}. You will be training: \n {exercise_response}', reply_markup=reply_markup
    )
    return CONFIRMATION


async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    global todo_exercises
    todo_exercises = []
    query = update.callback_query
    await query.answer()

    if query.data == 'Confirm':
        # insert activity into database
        user_entry['_id'] = ObjectId()
        datetime_str = user_entry['date'] + ' ' + user_entry['time']
        datetime_object = datetime.strptime(datetime_str, '%d %B %Y %H%M')
        user_entry['date_time'] = datetime_object
        print(user_entry)
        user_activity.insert_one(user_entry)
        text = "Goodbye! See you at the gym!"
    elif query.data == 'Exit':
        text = "Goodbye!"
    await query.edit_message_text(text=text)
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(API_KEY).build()

    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    print(f'gymBot is running...')
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler(
            "gym", start_menu), CommandHandler("view", quick_view)],
        states={
            MENU: [
                CallbackQueryHandler(
                    day_selection, pattern="^Schedule a session$"
                ),
                CallbackQueryHandler(
                    end_conversation, pattern="^Exit$"
                ),
            ],
            DAY_CHOICE: [
                CallbackQueryHandler(
                    period_selection, pattern="[^Back$]"
                ),
                CallbackQueryHandler(
                    end_conversation, pattern="^Back$"
                ),
            ],
            PERIOD_CHOICE: [
                CallbackQueryHandler(
                    time_selection, pattern="[^Back$]"
                ),
                CallbackQueryHandler(
                    day_selection, pattern="^Back$"
                ),
            ],
            TIME_CHOICE: [
                CallbackQueryHandler(
                    exercise_selection, pattern="[^Back$]"
                ),
                CallbackQueryHandler(
                    period_selection, pattern="^Back$"
                ),
            ],
            EXERCISE_CHOICE: [
                CallbackQueryHandler(
                    confirm_selection, pattern="^Done$"
                ),
                CallbackQueryHandler(
                    exercise_selection, pattern="^Back workout$"
                ),
                CallbackQueryHandler(
                    exercise_selection, pattern="[^Back$]"
                ),
                CallbackQueryHandler(
                    time_selection, pattern="^Back$"
                ),
            ],
            CONFIRMATION: [
                CallbackQueryHandler(
                    end_conversation, pattern="^Confirm$"
                ),
                CallbackQueryHandler(
                    exercise_selection, pattern="^Back$"
                )
            ]
        },
        fallbacks=[CommandHandler("gym", start_menu)],
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
