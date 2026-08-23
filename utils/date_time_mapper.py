from khayyam import JalaliDatetime
from dateutil.parser import parse
import pytz


PERSIAN_DIGITS = {
    '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴', '5': '۵',
    '6': '۶', '7': '۷', '8': '۸', '9': '۹'
}


def to_persian_numbers(text):
    for english_digit, persian_digit in PERSIAN_DIGITS.items():
        text = text.replace(english_digit, persian_digit)
    return text


def create_date_object(date_str):
    return parse(date_str)


def get_time(parsed_date):
    # Convert to Tehran time and return time string
    dt_tehran = parsed_date.astimezone(pytz.timezone('Asia/Tehran'))
    return  dt_tehran.strftime('%H:%M:%S')


def get_jalali_date(parsed_date):
    jalali_date = JalaliDatetime(parsed_date)
    day_name = jalali_date.strftime('%A')
    day = jalali_date.day
    month = jalali_date.strftime('%B')
    year = jalali_date.year
    formatted_date = f"{day_name} {day} {month} {year}"
    return to_persian_numbers(formatted_date)
