from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove)
from telegram.ext import (
    filters,
    Application,
    MessageHandler,
    CallbackQueryHandler,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler
)
import os
from dotenv import load_dotenv
from datetime import date, timedelta, datetime

load_dotenv()
API_KEY = os.getenv('API_KEY')

q1 = "Hello, which day are you planning to gym?"
q2 = "Which session are you planning to gym?"
q3 = "What time are you planning to gym?"
q4 = "What will you be training?"
cutOffHour = 20
user_entry = {
    "telegram_id": None,
    "telegram_username": None,
    "first_name": None,
    "day": None,
    "time": None,
    "workout_type": None
}
DAY_CHOICE, PERIOD_CHOICE, TIME_CHOICE, EXERCISE_CHOICE, CONFIRMATION = range(
    5)


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


def getDays(cutOffTime):
    currentDateAndTime = datetime.now()
    today = date.today()
    currentHour = currentDateAndTime.strftime("%H")
    day_0 = date.today()
    day_1 = date.today() + timedelta(days=1)
    day_2 = date.today() + timedelta(days=2)
    day_3 = date.today() + timedelta(days=3)
    if int(currentHour) < cutOffTime:
        days = [day_0.strftime("%d %B %Y"), day_1.strftime(
            "%d %B %Y"), day_2.strftime("%d %B %Y")]
    else:
        days = [day_1.strftime("%d %B %Y"), day_2.strftime(
            "%d %B %Y"), day_3.strftime("%d %B %Y")]
    return days


"""selecting day to gym """


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day_1, day_2, day_3 = getDays(cutOffHour)
    keyboard1 = [
        [day_1],
        [day_2],
        [day_3],
        ['Back']
    ]
    await update.message.reply_text(
        q1,
        reply_markup=ReplyKeyboardMarkup(keyboard1, one_time_keyboard=True)
    )
    return DAY_CHOICE

"""selecting 'morning','afternoon','evening' timings """


async def period_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text
    telegram_username = update.message['from'].username
    telegram_id = update.message['from'].id
    first_name = update.message['from'].first_name
    # update user_entry
    user_entry['telegram_id'] = telegram_id
    user_entry['telegram_username'] = telegram_username
    user_entry['first_name'] = first_name
    user_entry['day'] = day

    keyboard2 = [
        ['Morning'],
        ['Afternoon'],
        ['Evening'],
        ['Back']
    ]
    currentHourMin = getCurrentHourMin()
    currentDay = date.today()
    DaySelected = datetime.strptime(day, "%d %B %Y").date()
    if currentDay == DaySelected:
        if currentHourMin >= 1130 and currentHourMin < 1630:
            keyboard2 = keyboard2[1:]
        elif currentHourMin >= 1630:
            keyboard2 = keyboard2[2:]
    await update.message.reply_text(
        f'You have selected to gym on {day}. {q2}',
        reply_markup=ReplyKeyboardMarkup(keyboard2, one_time_keyboard=True)
    )
    return PERIOD_CHOICE


async def time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    period = update.message.text
    morning = [700, 730, 800, 830, 900, 930, 1000, 1030, 1100, 1130]
    afternoon = [1200, 1230, 1300, 1330, 1400, 1430, 1500, 1530, 1600, 1630]
    evening = [1700, 1730, 1800, 1830, 1900, 1930, 2000, 2030, 2100, 2130]
    currentHourMin = getCurrentHourMin()
    currentDay = date.today()
    day = user_entry['day']
    DaySelected = datetime.strptime(day, "%d %B %Y").date()

    if period == 'Morning':
        # if selected today, remove anytime stamp that is earlier than current time.
        if currentDay == DaySelected:
            for time in morning:
                if currentHourMin >= time:
                    morning.remove(time)
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
    await update.message.reply_text(
        f'You have selected to gym on {day}, {period.lower()} session. {q3}',
        reply_markup=ReplyKeyboardMarkup(keyboard3, one_time_keyboard=True)
    )
    return TIME_CHOICE


async def exercise_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    timeslot = update.message.text
    time_24hour = timeTo24Hour(timeslot)
    user_entry['time'] = time_24hour
    exercises = ['Chest', 'Shoulders', 'Back', 'Legs', 'Abs', 'Others']
    keyboard4 = []
    for ex in exercises:
        keyboard4.append([ex])
    keyboard4.append(['Back'])
    day = user_entry['day']
    time = user_entry['time']
    await update.message.reply_text(
        f'You have selected to gym on {day} at {timeslot}. {q4}',
        reply_markup=ReplyKeyboardMarkup(keyboard4, one_time_keyboard=True)
    )
    return TIME_CHOICE


# async def end_conversation


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('hello world')


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """reject any unknown command"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I don't understand that command. 😔")


if __name__ == '__main__':
    application = ApplicationBuilder().token(API_KEY).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("gym", start)],
        states={
            DAY_CHOICE: [
                MessageHandler(
                    filters.Regex(
                        r'January|Feburary|March|April|May|June|July|August|September|October|November|December'), period_selection,
                ),
                # MessageHandler(
                #     filters.Regex("^Back$"), end_conversation
                # )
            ],
            PERIOD_CHOICE: [
                MessageHandler(
                    filters.Regex(
                        '^Morning|Afternoon|Evening$'), time_selection,
                )
            ],
            TIME_CHOICE: [
                MessageHandler(
                    ~filters.Regex("^Back$"), exercise_selection,
                )
            ]
        },
        fallbacks=[
            MessageHandler(filters.Regex("^Done$"), done)
        ]
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
