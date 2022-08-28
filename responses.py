from datetime import datetime


def sample_responses(input_text):
    user_message = str(input_text).lower()

    if user_message in ('hello', 'hi'):
        return 'Hows it going?'

    if user_message in ('time'):
        now = datetime.now()
        date_time = now.strftime('%d/%m/%y, %H:%M:%S')
        return str(date_time)

    return "I don't understand you..."
