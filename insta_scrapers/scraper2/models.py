import requests
from utils import clean_and_check_farsi

session = requests.Session()

def sense_model(message):
    url = 'http://188.136.208.234:6005/sense'
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    cleaned = clean_and_check_farsi(message)
    if cleaned is None:
        print("❌ متن نامعتبر یا بدون محتوای فارسی است.")
        return None
    try:
        response = session.post(url, json={'message': cleaned}, headers=headers)
        response.raise_for_status()
        return response.json().get('result', 'نامشخص')
    except requests.exceptions.RequestException as e:
        print("❗ خطا در ارسال درخواست:", e)
        return None

def category_model(message):
    url = 'http://188.136.208.234:6005/category'
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    cleaned = clean_and_check_farsi(message)
    if cleaned is None:
        print("❌ پیام تگ‌گذاری قابل‌بررسی نیست.")
        return None
    try:
        response = session.post(url, json={'message': cleaned}, headers=headers)
        response.raise_for_status()
        result = response.json().get('result')
        return result if result else 'متفرقه'
    except requests.exceptions.RequestException as e:
        print("❗ خطا در تگ‌گذاری:", e)
        return None

def sentiment_model(message):
    url = 'http://188.136.208.234:6005/sentiment'
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    cleaned = clean_and_check_farsi(message)
    if cleaned is None:
        print("❌ پیام برای تحلیل احساس مناسب نیست.")
        return None
    try:
        response = session.post(url, json={'message': cleaned}, headers=headers)
        response.raise_for_status()
        return response.json().get('result', 'نامشخص')
    except requests.exceptions.RequestException as e:
        print("❗ خطا در ارسال به مدل احساس:", e)
        return None
