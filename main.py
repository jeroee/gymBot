from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler
)
from pymongo import MongoClient
from functools import partial
import logging
import sys

# bot functions
from handlers import *
from config import *
from constants import (
    BACK_PATTERN,
    DONE_PATTERN,
    CONFIRM_PATTERN,
    EXIT_PATTERN,
    SCHEDULE_PATTERN,
    VIEW_SESSIONS_PATTERN,
    MENU, 
    MY_SESSIONS, 
    REMOVAL, 
    DAY_CHOICE, 
    PERIOD_CHOICE, 
    TIME_CHOICE, 
    EXERCISE_CHOICE, 
    CONFIRMATION,
    user_entry,
    session_remove,
    time_slots,
    exercises
)

# -------------------------------------------------------------------
# to remove the warnings triggered by CallBackQueryHandler
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler",
               category=PTBUserWarning)
# -------------------------------------------------------------------

# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # Adjust the level (DEBUG, INFO, WARNING, etc.) as needed
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Send logs to stdout
    ],
)
logger = logging.getLogger(__name__)

connection_string = f'mongodb+srv://{USERNAME}:{PASSWORD}@testcluster.cpfwr.mongodb.net/?retryWrites=true&w=majority&appName=testCluster'
client = MongoClient(connection_string)
db = client[DB_NAME]
user_activity = db[COLLECTION_NAME]

def main() -> None:
    """Run the bot."""
    # Initialize the application with the bot's API key
    application = Application.builder().token(API_KEY).build()

    # Set up the conversation handler with states and respective handlers
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("gym", start_menu),
            CommandHandler("view", partial(quick_view, user_activity=user_activity)),
        ],
        states={
            MENU: [
                CallbackQueryHandler(day_selection, pattern=SCHEDULE_PATTERN),
                CallbackQueryHandler(partial(my_sessions, user_activity=user_activity), pattern=VIEW_SESSIONS_PATTERN),
                CallbackQueryHandler(partial(end_conversation, user_activity=user_activity, user_entry=user_entry), pattern=EXIT_PATTERN),
            ],
            MY_SESSIONS: [
                CallbackQueryHandler(partial(session_removal,session_remove=session_remove), pattern=f"[^Back]"),
                CallbackQueryHandler(start_menu, pattern=BACK_PATTERN),
            ],
            REMOVAL: [
                CallbackQueryHandler(partial(removal_confirm,user_activity=user_activity), pattern=CONFIRM_PATTERN),
                CallbackQueryHandler(partial(my_sessions,user_activity=user_activity), pattern=BACK_PATTERN),
            ],
            DAY_CHOICE: [
                CallbackQueryHandler(partial(period_selection,user_entry=user_entry), pattern=f"[^Back]"),
                CallbackQueryHandler(start_menu, pattern=BACK_PATTERN),
            ],
            PERIOD_CHOICE: [
                CallbackQueryHandler(partial(time_selection,time_slots=time_slots,user_entry=user_entry), pattern=f"[^Back]"),
                CallbackQueryHandler(day_selection, pattern=BACK_PATTERN),
            ],
            TIME_CHOICE: [
                CallbackQueryHandler(partial(exercise_selection,user_entry=user_entry,exercises=exercises), pattern=f"[^Back]"),
                CallbackQueryHandler(partial(period_selection,user_entry=user_entry), pattern=BACK_PATTERN),
            ],
            EXERCISE_CHOICE: [
                CallbackQueryHandler(partial(confirm_selection,user_entry=user_entry), pattern=DONE_PATTERN),
                CallbackQueryHandler(partial(exercise_selection,user_entry=user_entry,exercises=exercises), pattern="^Back workout$"),
                CallbackQueryHandler(partial(exercise_selection,user_entry=user_entry,exercises=exercises), pattern=f"[^Back]"),
                CallbackQueryHandler(partial(time_selection,time_slots=time_slots,user_entry=user_entry), pattern=BACK_PATTERN),
            ],
            CONFIRMATION: [
                CallbackQueryHandler(partial(end_conversation,user_activity=user_activity, user_entry=user_entry), pattern=CONFIRM_PATTERN),
                CallbackQueryHandler(partial(exercise_selection,user_entry=user_entry,exercises=exercises), pattern=BACK_PATTERN),
            ],
        },
        fallbacks=[CommandHandler("gym", start_menu)],
    )

    # Add conversation handler to application
    application.add_handler(conv_handler)

    # Run the bot
    logger.info("gymBot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()