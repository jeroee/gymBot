'''https://github.com/python-telegram-bot/python-telegram-bot'''

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

q1 = "Which day are you planning to gym?"
q2 = "What time are you planning to gym?"
q3 = "What will you be training?"
cutOffHour = 20
user_entry = {
    "telegram_id": None,
    "telegram_username": None,
    "day": None,
    "time": None,
    "workout_type": None
}

"""to get 3 dates: today, tomorrow, day after.
if current time goes beyond cutOffTime, each of the 3 days will add 1 day.
eg: 12 Aug, 13 Aug, 14 Aug --> 13 Aug, 14 Aug, 15 Aug"""


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    day_1, day_2, day_3 = getDays(cutOffHour)
    keyboard = [
        [InlineKeyboardButton(day_1, callback_data=day_1)],
        [InlineKeyboardButton(day_2, callback_data=day_2)],
        [InlineKeyboardButton(day_3, callback_data=day_3)],
        [InlineKeyboardButton("Back", callback_data="back")]

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(q1, reply_markup=reply_markup)
    # await context.bot.send_message(chat_id=update.effective_chat.id, text="Which days would you like to gym?")


# async def getTime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")

    question = query.message.text
    answer = query.data
    telegram_username = query['from'].username
    telegram_id = query['from'].id

    if question == q1:
        if answer != "back":
            user_entry['telegram_username'] = telegram_username
            user_entry['telegram_id'] = telegram_id
            user_entry['day'] = answer

    print(user_entry)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """reject any unknown command"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I don't understand that command. 😔")


if __name__ == '__main__':
    application = ApplicationBuilder().token(API_KEY).build()

    # creating to handler
    # conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler("gym", start)],
    #     states={
    #         START_ROUTES: [
    #             CallbackQueryHandler(one, pattern="^" + str(ONE) + "$"),
    #             CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"),
    #             CallbackQueryHandler(three, pattern="^" + str(THREE) + "$"),
    #             CallbackQueryHandler(four, pattern="^" + str(FOUR) + "$"),
    #         ],
    #         END_ROUTES: [
    #             CallbackQueryHandler(start_over, pattern="^" + str(ONE) + "$"),
    #             CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
    #         ],
    #     },
    #     fallbacks=[CommandHandler("start", start)],
    # )
    start_handler = CommandHandler('gym', start)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    # adding the handlers to the telegram bot
    application.add_handler(start_handler)
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(unknown_handler)

    application.run_polling()
