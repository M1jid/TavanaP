import json
from telebot import types
from api_client import create_telegram_channel, get_telegram_channel_by_key


def handle_add_channel(bot, call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("انصراف", callback_data="home"))
    bot.edit_message_text(chat_id=call.message.chat.id, text=":لینک کانال را وارد کنید", reply_markup=markup, message_id=call.message.id)

def process_channel_url(bot, message, state_manager):
    url = message.text
    base_url = 'https://t.me/'
    key = url.replace(base_url, '').replace('@', '').replace('t.me', '').replace('/', '')
    data = {
        'key': key,
        'value': base_url + key,
        'subscribed_by': 1,
    }
    result = create_telegram_channel(data=data)
    state_manager.clear_state(message.chat.id)
    
    if result:
        log = json.dumps(result, indent=4, ensure_ascii=False)
        bot.send_message(message.chat.id, f"ذخیره شد:\n{log}")
    else:
        result = get_telegram_channel_by_key(key=key)
        log = json.dumps(result, indent=4, ensure_ascii=False)
        bot.send_message(message.chat.id, f"کانال از قبل در دیتابیس موجود بود:\n{log}")
