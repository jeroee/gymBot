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

import services
import utils
from constants import *

# Define your states for better readability
MENU, MY_SESSIONS, REMOVAL, DAY_CHOICE, PERIOD_CHOICE, TIME_CHOICE, EXERCISE_CHOICE, CONFIRMATION = range(8)

# Handlers
async def start_menu(update: Update, context):
    """Start menu handler"""
    # Create the initial message
    message = "Hi, welcome to gymBot. How can I help you?\n\nTo view the group's gym schedule for the next few days, type '/view' in the chat"
    # Define the inline keyboard options
    keyboard = [
        [InlineKeyboardButton("Schedule a session", callback_data="Schedule a session")],
        [InlineKeyboardButton("View my sessions", callback_data="View my sessions")],
        [InlineKeyboardButton("More Info - Under Maintenance 🔧", callback_data="More Info")],
        [InlineKeyboardButton("Exit", callback_data="Exit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Determine whether to reply to a message or edit an existing message
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=message, parse_mode="HTML", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=message, parse_mode="HTML", reply_markup=reply_markup
        )
    
    return MENU

async def quick_view(update: Update, context, user_activity):
    """Quick view handler"""
    # Generate the schedule display
    schedule_display = services.all_views(update, user_activity)
    # Build the message
    message = f"Hi, welcome to gymBot View. \n\n{schedule_display}To create or manage your schedule, type '/gym' in the chat\n\n"
    # Get a random quote
    quote = utils.get_random_quote(QUOTE_FILE)
    formatted_quote = f'Random motivational quote:\n\n ~ "{quote}" ~ \n' if quote[0] != '"' else f"Random motivational quote:\n\n ~ {quote} ~ \n"
    # Append the quote to the message
    message += formatted_quote
    # Send the message
    await update.message.reply_text(message, parse_mode="HTML")
    return ConversationHandler.END

async def day_selection(update: Update, context):
    """Day selection handler"""
    """Handle the day selection process."""
    query = update.callback_query
    # Get the days for selection
    days = services.get_days(CUT_OFF_HOUR)
    # Create the inline keyboard with day options and a back button
    keyboard = [
        [InlineKeyboardButton(day, callback_data=day)] for day in days
    ] + [[InlineKeyboardButton("⏎", callback_data="Back")]]
    # Define the reply markup
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Edit the message text and display the keyboard
    await query.edit_message_text(text=q1, reply_markup=reply_markup)
    # Tell ConversationHandler that we're in the DAY_CHOICE state
    return DAY_CHOICE

async def my_sessions(update: Update, context, user_activity):
    """Handle user's session view and deletion."""
    query = update.callback_query
    schedule_display, keyboard = services.my_view(update, user_activity)
    # Add session removal instructions if there are more than one session
    if len(keyboard) > 1:
        schedule_display += '\n\nIf you wish to delete an upcoming session, select the session below.'
    # Prepare the reply markup
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Edit the message text with the session details
    await query.edit_message_text(
        text=schedule_display, reply_markup=reply_markup, parse_mode="HTML"
    )
    return MY_SESSIONS

async def session_removal(update: Update, context, session_remove):
    """Session removal handler"""
    """Handles the session removal process."""
    query = update.callback_query
    session_id = query.data
    session_remove['id'] = session_id

    # Retrieve session name from the callback query's inline keyboard
    for button in query.message.reply_markup.inline_keyboard[0]:
        if button.callback_data == session_id:
            session_remove['name'] = button.text
            break
    # Prepare confirmation keyboard
    keyboard = [
        [InlineKeyboardButton('Confirm', callback_data='Confirm')],
        [InlineKeyboardButton('⏎', callback_data='Back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Respond to user
    await query.answer()
    await query.edit_message_text(
        text=(
            f'You have chosen to remove a session:\n\n'
            f'🏋️‍♀️ {session_remove["name"]}\n'
        ),
        reply_markup=reply_markup
    )
    return REMOVAL

async def removal_confirm(update: Update, context, user_activity):
    """Handles confirmation of session removal."""
    query = update.callback_query
    session_id = session_remove.get('id')
    if session_id:
        # Remove session from the database
        user_activity.delete_one({'_id': ObjectId(session_id)})
        text = "Session successfully removed.\n\nGoodbye!"
    else:
        text = "No session found to remove.\n\nGoodbye!"
    # Update message text
    await query.edit_message_text(text=text)
    return ConversationHandler.END

async def period_selection(update: Update, context,user_entry):
    """Period selection handler"""
    query = update.callback_query
    data = query.data

    if data != 'Back':
        # Parse selected day and date
        today = data.split(" ")[-1].replace("(", "").replace(")", "")
        today_date = " ".join(data.split(" ")[:-1])
        # Extract user and group details
        user_info = query['from']
        telegram_id = user_info.id
        telegram_username = user_info.username
        first_name = user_info.first_name
        group_id = query['message']['chat'].id

        # Update user_entry with session details
        user_entry.update({
            'telegram_id': telegram_id,
            'group_id': group_id,
            'telegram_username': telegram_username,
            'first_name': first_name,
            'day': today,
            'date': today_date,
        })
    else:
        # Fallback to previously stored date and day
        today_date = user_entry['date']
        today = user_entry['day']

    # Define period selection options
    period_keyboard = [
        [InlineKeyboardButton('Morning', callback_data='Morning')],
        [InlineKeyboardButton('Afternoon', callback_data='Afternoon')],
        [InlineKeyboardButton('Evening', callback_data='Evening')],
        [InlineKeyboardButton("⏎", callback_data="Back")]
    ]

    # Adjust options based on the current time if selecting today's date
    current_hour_min = utils.get_current_hour_min()
    current_day = date.today()
    selected_day = datetime.strptime(today_date, "%d %B %Y").date()

    if current_day == selected_day:
        if 1130 <= current_hour_min < 1630:
            period_keyboard = period_keyboard[1:]  # Remove 'Morning'
        elif current_hour_min >= 1630:
            period_keyboard = period_keyboard[2:]  # Remove 'Morning' and 'Afternoon'
    # Create and send reply markup
    reply_markup = InlineKeyboardMarkup(period_keyboard)
    await query.answer()
    await query.edit_message_text(
        text=f'You have selected to gym on {today}, {today_date}. {q2}',
        reply_markup=reply_markup,
    )
    print('reached here')
    return PERIOD_CHOICE
    
async def time_selection(update: Update, context, user_entry, time_slots):
    """Handles time slot selection for gym sessions."""
    query = update.callback_query
    # Retrieve date and time details
    current_hour_min = utils.get_current_hour_min()
    current_day = date.today()
    today_date = user_entry['date']
    today = user_entry['day']
    selected_day = datetime.strptime(today_date, "%d %B %Y").date()

    # Update or retain the selected period
    period = query.data if query.data != 'Back' else time_period
    if query.data == 'Back':
        todo_exercises = []
    else:
        time_period = period
    times = [
        t for t in time_slots[period]
        if current_day != selected_day or t >= current_hour_min
    ]
    # Generate the keyboard for time selection
    keyboard = [[InlineKeyboardButton(utils.format_time_slot(t), callback_data=utils.format_time_slot(t))] for t in times]
    keyboard.append([InlineKeyboardButton("⏎", callback_data="Back")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the updated message
    await query.edit_message_text(
        text=f'You have selected to gym on {today}, {today_date}, {period.lower()} session. {q3}',
        reply_markup=reply_markup
    )
    return TIME_CHOICE

async def exercise_selection(update: Update, context, user_entry, exercises):
    """Handles exercise selection for gym sessions."""
    query = update.callback_query
    await query.answer()

    # Handle user input
    if query.data == 'Back':
        time_selected = utils.hour_24_to_time(user_entry['time'])
    elif utils.has_numbers(query.data):
        time_selected = query.data
        user_entry['time'] = utils.time_to_24_hour(time_selected)
    else:
        time_selected = utils.hour_24_to_time(user_entry['time'])
        exercise_selected = query.data
        # Toggle exercise selection
        if exercise_selected in todo_exercises:
            todo_exercises.remove(exercise_selected)
        else:
            todo_exercises.append(exercise_selected)

    # Build keyboard for exercise selection
    keyboard = [[InlineKeyboardButton(ex, callback_data=ex)] for ex in exercises]

    # Include "Done" button if exercises are selected
    if todo_exercises:
        keyboard.insert(0, [InlineKeyboardButton("Done", callback_data="Done")])

    # Add "Back" button at the end
    keyboard.append([InlineKeyboardButton("⏎", callback_data="Back")])

    # Format the selected exercises for display
    exercise_response = "\n".join(f" - {ex.split(' ')[0]}" for ex in todo_exercises)

    # Retrieve date and time details
    today = user_entry['day']
    today_date = user_entry['date']

    # Reply with the updated keyboard
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=(
            f'You have selected to gym on {today}, {today_date} at {time_selected}. {q4} \n'
            f'(You may choose more than one workout)\n{exercise_response}'
        ),
        reply_markup=reply_markup
    )
    return EXERCISE_CHOICE

async def confirm_selection(update: Update, context, user_entry):
    """Handles confirmation of the selected gym session details."""
    query = update.callback_query
    await query.answer()

    # Extract user selection details
    today = user_entry['day']
    today_date = user_entry['date']
    time_selected = utils.hour_24_to_time(user_entry['time'])
    exercise_response = "\n".join(f" - {ex.split(' ')[0]}" for ex in todo_exercises)

    # Update user entry with selected workouts
    user_entry['workout'] = [ex.split(' ')[0] for ex in todo_exercises]

    # Build confirmation keyboard
    keyboard = [
        [InlineKeyboardButton('Confirm', callback_data='Confirm')],
        [InlineKeyboardButton('⏎', callback_data='Back')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send confirmation message
    await query.edit_message_text(
        text=(
            f'You have selected to gym on {today}, {today_date} at {time_selected}. '
            f'You will be training:\n{exercise_response}'
        ),
        reply_markup=reply_markup
    )
    return CONFIRMATION

async def end_conversation(update: Update, context, user_activity, user_entry):
    """Ends the conversation and handles database insertion or exit based on user selection."""
    
    query = update.callback_query
    await query.answer()

    # Prepare the response text
    if query.data == 'Confirm':
        # Insert activity into the database
        services.insert_activity_to_db(user_activity, user_entry)
        schedule_display = services.all_views(update, user_activity)
        text = f"{schedule_display}\nGoodbye! \n\nSee you at the gym!"
    elif query.data == 'Exit':
        text = "Goodbye!"

    # Edit the message with the appropriate text
    await query.edit_message_text(text=text, parse_mode=constants.ParseMode.HTML)
    return ConversationHandler.END