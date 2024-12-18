from datetime import datetime
import random
import re

def has_numbers(inputString):
    return bool(re.search(r'\d', inputString))

def get_random_quote(file_path):
    """Return a random quote from the specified file."""
    with open(file_path, 'r') as file:
        quotes = [line.strip() for line in file.readlines()]
    return random.choice(quotes) if quotes else None

def get_current_hour_min():
    return int(datetime.now().strftime("%H%M"))

def time_to_24_hour(time):
    am_pm = time[-2:]
    hours, minutes = map(int, time[:-2].split(":"))
    if am_pm == 'PM' and hours != 12:
        hours += 12
    elif am_pm == 'AM' and hours == 12:
        hours = 0
    return f"{hours:02}{minutes:02}"

def hour_24_to_time(time):
    hr = int(time[:2])
    min = time[2:]
    am_pm = "PM" if hr >= 12 else "AM"
    if hr > 12:
        hr -= 12
    elif hr == 0:
        hr = 12
    return f"{hr}:{min}{am_pm}"

def get_random_quote(file_path):
    """Return a random quote from the specified file."""
    with open(file_path, 'r') as file:
        quotes = [line.strip() for line in file.readlines()]
    return random.choice(quotes) if quotes else None

# Format time slots
def format_time_slot(t):
    hour, minute = divmod(t, 100)
    period = 'AM' if hour < 12 else 'PM'
    hour = hour if hour <= 12 else hour - 12
    return f"{hour}:{minute:02}{period}"