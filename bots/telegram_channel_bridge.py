import os
import telebot
import socks
import json
import random
from routing_roles import config
from telebot import types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

telebot.apihelper.proxy = {
    "https": os.getenv("TELEGRAM_BOT_PROXY", "http://127.0.0.1:10809")
}

bot = telebot.TeleBot(TOKEN)

menu_button = types.MenuButtonCommands()
bot.set_chat_menu_button(menu_button=menu_button)
commands = [
    types.BotCommand("start", "شروع دوباره"),
]

bot.set_my_commands(commands)


import requests
from typing import Any, Dict, Optional, List

BASE_URL = os.getenv("TELEGRAM_ACCOUNT_MANAGER_HOST", "http://127.0.0.1:9000")

def get_telegram_channels() -> List[Dict]:
    resp = requests.get(f"{BASE_URL}/telegram/channels", timeout=30.0)
    data = resp.json()
    result = []
    for item in data:
        if item['blocked'] is False and item['in_progress'] is False and item['subscribed_by'] is None:
            result.append(item)
    return result

def update_telegram_channel(channel_id: int, data: Dict[str, Any]) -> Dict:
    resp = requests.put(f"{BASE_URL}/telegram/channels/{channel_id}", json=data, timeout=30.0)
    return resp.json()


def create_telegram_channel(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/telegram/channels", json=[data], timeout=30.0)
    if resp.status_code != 200:
        return resp.text
    return resp.json()


def create_telegram_account(data: Dict[str, Any]) -> Dict:
    resp = requests.post(f"{BASE_URL}/telegram/accounts", json=[data], timeout=30.0)
    if resp.status_code != 200:
        return resp.text
    return resp.json()


def get_telegram_channel_by_key(key) -> Dict:
    resp = requests.get(f"{BASE_URL}/telegram/channels_by_key/{key}", timeout=30.0)
    if resp.status_code != 200:
        return resp.text
    return resp.json()

DATABASE = get_telegram_channels()
random.shuffle(DATABASE)

volume = len(DATABASE)
print(volume)
index = -1

def get_new_channel():
    global index, DATABASE
    index +=1
    return DATABASE[index]


def update_saved_queue():
    with open('saved.json', 'w') as f:
        f.write(json.dumps(saved_queue, indent=4))

def update_ignored_queue():
    with open('ignored.json', 'w') as f:
        f.write(json.dumps(ignored_queue, indent=4))

def update_skiped_queue():
    with open('skiped.json', 'w') as f:
        f.write(json.dumps(skiped_queue, indent=4))


saved_queue = []
skiped_queue = []
ignored_queue = []
assigned_items = []
current_item = {}
user_current_item = {}          # user_id -> current item

user_ids = [424813528, 6253093238, 484924269, 7545468782] # replace with your Telegram user ID
user_states = {}

# /start command

def send_welcome(chat_id, message_id):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("پاکسازی دیتابیس", callback_data="db"),
        telebot.types.InlineKeyboardButton("افزودن کانال تلگرامی", callback_data="add_channel"),
        telebot.types.InlineKeyboardButton("افزودن اکانت تلگرامی", callback_data="add_account"),
        telebot.types.InlineKeyboardButton("قوانین", callback_data="roles"),
    )
    bot.edit_message_text(chat_id=chat_id, text="به ربات دستیار خوش‌آمدید.\nخدمات:\n", reply_markup=markup, message_id=message_id)


@bot.message_handler(commands=['start'])
def on_start(message):
    if message.chat.id in user_states:
        del user_states[message.chat.id]
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("پاکسازی دیتابیس", callback_data="db"),
        telebot.types.InlineKeyboardButton("افزودن کانال تلگرامی", callback_data="add_channel"),
        telebot.types.InlineKeyboardButton("افزودن اکانت تلگرامی", callback_data="add_account"),
        telebot.types.InlineKeyboardButton("قوانین", callback_data="roles"),
    )
    bot.send_message(message.chat.id, "به ربات دستیار خوش‌آمدید.\nخدمات:\n", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["db", "add_channel", "add_account", "roles"])
def handle_callback_query(call):
    global user_states
    
    if call.message.chat.id not in user_ids:
        bot.answer_callback_query(call.id, "⚠️ عدم دسترسی لازم")
        return

    if call.data == "db":
        user_states[call.message.chat.id] = {"state": "cleane_database", "data": {}}
        send_next(user_id=call.message.chat.id)
    
    if call.data == "add_channel":
        user_states[call.message.chat.id] = {"state": "awaiting_channel_url", "data": {}}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("انصراف", callback_data="cancel_add_account"),
        )
        bot.send_message(call.message.chat.id, ":لینک کانال را وارد کنید", reply_markup=markup)
    
    if call.data == "add_account":
        markup = telebot.types.InlineKeyboardMarkup()
        user_states[call.message.chat.id] = {"state": "awaiting_account_phone_number", "data": {}}
        markup.row(
            telebot.types.InlineKeyboardButton("انصراف", callback_data="cancel_add_account"),
        )
        bot.send_message(call.message.chat.id, "شماره تلفن را وارد کنید:", reply_markup=markup)
    
    if call.data == "roles":
        markup = telebot.types.InlineKeyboardMarkup()
        user_states[call.message.chat.id] = {"state": "searching_roles", "data": {}}
        for idx, option in enumerate(config):
            markup.add(telebot.types.InlineKeyboardButton(text=option['name'], callback_data=f"option_{idx}"))
        markup.add(telebot.types.InlineKeyboardButton(text='بازگشت', callback_data=f"home"))
        bot.send_message(call.message.chat.id, "لیست کانال های تعریف شده", reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "تعریف نشده")


def send_next(user_id):
    for item in DATABASE:
        try:
            if item['id'] not in assigned_items:
                user_current_item[user_id] = item
                assigned_items.append(item['id'])

                print(item, flush=True)
                markup = telebot.types.InlineKeyboardMarkup()
                markup.row(
                    telebot.types.InlineKeyboardButton("افزودن", callback_data="yes"),
                    telebot.types.InlineKeyboardButton("حذف", callback_data="no"),
                    telebot.types.InlineKeyboardButton("بعدی", callback_data="skip"),
                    telebot.types.InlineKeyboardButton("انصراف", callback_data="cancel_db_clean"),
                )
                bot.send_message(user_id, f"Item {index+1}/{volume-len(assigned_items)}\n{json.dumps(item, indent=4)}", reply_markup=markup)
                break
        except Exception:
            pass


@bot.callback_query_handler(func=lambda call: call.data in ["yes", "no", "skip", "cancel_db_clean"])
def callback_query(call):
    if call.message.chat.id not in user_ids:
        bot.answer_callback_query(call.id, "⚠️ عدم دسترسی لازم")
        return

    if call.message.chat.id not in user_states or user_states[call.message.chat.id]['state'] != 'cleane_database':
        bot.answer_callback_query(call.id, "⚠️ از منو گزینه پاکسازی را انتخاب کنید.")
        return

    user_id = call.message.chat.id
    if user_id not in user_current_item:
        bot.answer_callback_query(call.id, "⚠️ No current item assigned to you.")
        return

    if call.data == "cancel_db_clean":
        bot.edit_message_text("عملیات متوقف شد", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return

    if call.data == "yes":
        saved_queue.append(user_current_item[user_id])
        bot.edit_message_text(f"✅ Added {user_current_item[user_id]['value']}.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        print(f"✅ Added {user_current_item[user_id]['value']}")
        update_saved_queue()
        current_id = user_current_item[user_id]['id']
        del user_current_item[user_id]['id']
        user_current_item[user_id]['subscribed_by']=1
        update_telegram_channel(current_id, user_current_item[user_id])
        send_next(call.message.chat.id)

    if call.data == "no":
        ignored_queue.append(user_current_item[user_id])
        bot.edit_message_text(f"❌ Ignored {user_current_item[user_id]['value']}.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        print(f'❌ Ignored {user_current_item[user_id]['value']}')
        update_ignored_queue()
        current_id = user_current_item[user_id]['id']
        del user_current_item[user_id]['id']
        user_current_item[user_id]['blocked']=True
        update_telegram_channel(current_id, user_current_item[user_id])
        send_next(call.message.chat.id)

    if call.data == "skip":
        skiped_queue.append(user_current_item[user_id])
        bot.edit_message_text(text=f"❌ Skiped {user_current_item[user_id]['value']}.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        print(f"❌ Skiped {user_current_item[user_id]['value']}")
        update_skiped_queue()
        send_next(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data in ["home"])
def home_page(call):
    if call.message.chat.id in user_states:
        del user_states[call.message.chat.id]
        return send_welcome(chat_id=call.message.chat.id, message_id=call.message.id)


@bot.callback_query_handler(func=lambda call: call.data in ["cancel_roles"])
def handle_cancel_roles(call):
    markup = telebot.types.InlineKeyboardMarkup()
    user_states[call.message.chat.id] = {"state": "searching_roles", "data": {}}
    for idx, option in enumerate(config):
        markup.add(telebot.types.InlineKeyboardButton(text=option['name'], callback_data=f"option_{idx}"))
    markup.add(telebot.types.InlineKeyboardButton(text='بازگشت', callback_data=f"home"))
    bot.edit_message_text(chat_id=call.message.chat.id, text="لیست کانال های تعریف شده", reply_markup=markup, message_id=call.message.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_new_role_"))
def handle_option_callback(call):
    idx = int(call.data[len("add_new_role_"):])  # extract the index after 'option_'
    user_states[call.message.chat.id] = {"state": "adding_channel_role", "data": {}}
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='بازگشت', callback_data=f"cancel_roles"))
    message = (
        f"در یک خط، همه واژه‌های must را با خط تیره (-) بین هر دو واژه بنویسید.\n"
        f"در خط بعد، واژه‌های should را بنویسید.\n"
        f"و در خط آخر، واژه‌های must_not را بنویسید.\n"
        f"مثال برای حالتی که واژه ارتش به همراه واژه جمهوری اسلامی یا واژه ایران باشد ولی واژه سپاه نباشد:\n"
        f"ارتش\n"
        f"ایران-جمهوری اسلامی\n"
        f"سپاه\n"
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=message,
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("option_"))
def handle_option_callback(call):
    idx = int(call.data[len("option_"):])  # extract the index after 'option_'
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton(text='افزودن به قوانین', callback_data=f"add_new_role_{idx}"),
        telebot.types.InlineKeyboardButton(text='حذف کانال', callback_data=f"remove_channel{idx}"),
        telebot.types.InlineKeyboardButton(text='بازگشت', callback_data=f"cancel_roles"),
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=f"برای {config[idx]['name']} انتخاب کنید",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data in ["accept_new_account", "ignore_new_account", "skip_api_id", "skip_api_hash", "skip_session_file", "cancel_add_account", "accept_new_role", "ignore_new_role"])
def callback_query(call):
    if call.message.chat.id not in user_ids:
        bot.answer_callback_query(call.id, "⚠️ عدم دسترسی لازم")
        return

    if call.message.chat.id in user_states and user_states[call.message.chat.id]['state'] in ["awaiting_channel_url", "awaiting_account_phone_number", "awaiting_account_api_id", "awaiting_account_api_hash", "awaiting_session_file"]:
        if call.data == "cancel_add_account":
            if call.message.chat.id in user_states:
                del user_states[call.message.chat.id]
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text="عملیات متوقف شد",
            )

    if call.message.chat.id in user_states and user_states[call.message.chat.id]['state'] == "adding_channel_role":
        if call.data == 'accept_new_role':
            bot.send_message(call.message.chat.id, "قانون افزوده شد")
            data=user_states[call.message.chat.id]['data']
            print(data, flush=True)
        if call.data == 'ignore_new_role':
            bot.send_message(call.message.chat.id, "عملیات متوقف شد")
        del user_states[call.message.chat.id]

    if call.message.chat.id in user_states and user_states[call.message.chat.id]['state'] == "accept_new_account":
        if call.data == 'accept_new_account':
            bot.send_message(call.message.chat.id, "حساب کاربری ذخیره شد")
            data=user_states[call.message.chat.id]['data']
            data['process'] = 0            
            result = create_telegram_account(data=data)
            print(result, flush=True)
        if call.data == 'ignore_new_account':
            bot.send_message(call.message.chat.id, "عملیات متوقف شد")
        if call.data == 'cancel_add_account':
            bot.send_message(call.message.chat.id, "عملیات متوقف شد")
        del user_states[call.message.chat.id]

    if call.message.chat.id in user_states and user_states[call.message.chat.id]['state'] == "awaiting_account_api_id":
        if call.data == "skip_api_id":
            # bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            user_states[call.message.chat.id]['data']['api_id'] = 23882441
            user_states[call.message.chat.id]["state"] = "awaiting_account_api_hash"
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(
                telebot.types.InlineKeyboardButton("ندارم api_hash", callback_data="skip_api_hash"),
                telebot.types.InlineKeyboardButton("انصراف", callback_data="cancel_add_account"),
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=":حساب کاربری را وارد کنید api_hash",
                reply_markup=markup
            )
            # bot.send_message(call.message.chat.id, ":حساب کاربری را وارد کنید api_hash", reply_markup=markup)

    if call.message.chat.id in user_states and user_states[call.message.chat.id]['state'] == "awaiting_account_api_hash":
        if call.data == "skip_api_hash":
            # bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            user_states[call.message.chat.id]['data']['api_hash'] = "473f5ab85fdf979abb17b114247f3523"
            user_states[call.message.chat.id]["state"] = "awaiting_session_file"
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(
                telebot.types.InlineKeyboardButton("ندارم session_file", callback_data="skip_session_file"),
                telebot.types.InlineKeyboardButton("انصراف", callback_data="cancel_add_account"),
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=":حساب کاربری را آپلود کنید session_file",
                reply_markup=markup
            )

            # bot.send_message(call.message.chat.id, ":حساب کاربری را آپلود کنید session_file", reply_markup=markup)

    if call.message.chat.id in user_states and user_states[call.message.chat.id]['state'] == "awaiting_session_file":
        if call.data == "skip_session_file":
            # bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            user_states[call.message.chat.id]['data']['session'] = None
            user_states[call.message.chat.id]["state"] = "accept_new_account"
            new_account = (
                f"اطلاعات فوق را تایید می‌کنید؟\n"
                f"Phone number: {user_states[call.message.chat.id]['data']['phone']}\n"
                f"api_id: {user_states[call.message.chat.id]['data']['api_id']}\n"
                f"api_hash: {user_states[call.message.chat.id]['data']['api_hash']}\n"
            )
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(
                telebot.types.InlineKeyboardButton("بله", callback_data="accept_new_account"),
                telebot.types.InlineKeyboardButton("خیر", callback_data="ignore_new_account"),
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=new_account,
                reply_markup=markup
            )
            # bot.send_message(call.message.chat.id, new_account, reply_markup=markup)


# Collect User Inputs Step-by-Step
@bot.message_handler(func=lambda msg: msg.chat.id in user_states, content_types=['text', 'document'])
def collect_info(message):
    state_data = user_states[message.chat.id]
    state = state_data["state"]
    data = state_data["data"]

    # Handle channel input flow
    if state == "awaiting_channel_url":
        url = message.text
        base_url = 'https://t.me/'
        key = url.replace(base_url, '').replace('@', '').replace('t.me', '').replace('/', '')
        data = {
            'key': key,
            'value': base_url + key,
            'subscribed_by': 1,
        }
        result = create_telegram_channel(data=data)
        del user_states[message.chat.id]
        if result:
            log = json.dumps(result, indent=4, ensure_ascii=False)
            bot.send_message(message.chat.id, f"ذخیره شد:\n{log}")
        else:
            result = get_telegram_channel_by_key(key=key)
            log = json.dumps(result, indent=4, ensure_ascii=False)
            bot.send_message(message.chat.id, f"کانال از قبل در دیتابیس موجود بود:\n{log}")
    
    if state == "awaiting_account_phone_number":
        user_states[message.chat.id]['data']['phone'] = int(message.text)
        user_states[message.chat.id]["state"] = "awaiting_account_api_id"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("ندارم api_id", callback_data="skip_api_id"),
            telebot.types.InlineKeyboardButton("انصراف", callback_data="cancel_add_account"),
        )
        bot.send_message(message.chat.id, ":حساب کاربری را وارد کنید api_id", reply_markup=markup)

    if state == "awaiting_account_api_id":
        user_states[message.chat.id]['data']['api_id'] = int(message.text)
        user_states[message.chat.id]["state"] = "awaiting_account_api_hash"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("ندارم api_hash", callback_data="skip_api_hash"),
            telebot.types.InlineKeyboardButton("انصراف", callback_data="cancel_add_account"),
        )
        bot.send_message(message.chat.id, ":حساب کاربری را وارد کنید api_hash", reply_markup=markup)

    if state == "awaiting_account_api_hash":
        user_states[message.chat.id]['data']['api_hash'] = message.text
        user_states[message.chat.id]["state"] = "awaiting_session_file"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("ندارم session_file", callback_data="skip_session_file"),
            telebot.types.InlineKeyboardButton("انصراف", callback_data="cancel_add_account"),
        )
        bot.send_message(message.chat.id, ":حساب کاربری را آپلود کنید session_file", reply_markup=markup)
        
    if state == "awaiting_session_file":
        if message.content_type == "document":
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

        # Save to local file
        filename = message.document.file_name
        with open(f"/home/appuser/services/conf/sessions/{user_states[message.chat.id]['data']['phone']}.session", "wb") as f:
            f.write(downloaded_file)

        user_states[message.chat.id]['data']['session_file'] = f"{user_states[message.chat.id]['data']['phone']}.session"
        user_states[message.chat.id]["state"] = "accept_new_account"
        new_account = (
            f"اطلاعات فوق را تایید می‌کنید؟\n"
            f"Phone number: {user_states[message.chat.id]['data']['phone']}\n"
            f"api_id: {user_states[message.chat.id]['data']['api_id']}\n"
            f"api_hash: {user_states[message.chat.id]['data']['api_hash']}\n"
        )
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("بله", callback_data="accept_new_account"),
            telebot.types.InlineKeyboardButton("خیر", callback_data="ignore_new_account"),
        )

        bot.send_message(message.chat.id, new_account, reply_markup=markup)

    if state == "adding_channel_role":
        roles = message.text.split('\n')
        print(roles, flush=True)
        roles = {'must': roles[0], 'should': roles[1], 'must_not': roles[2]}
        print(roles, flush=True)
        for role, data in roles.items():
            roles[role] = data.split('-')
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("بله", callback_data="accept_new_role"),
            telebot.types.InlineKeyboardButton("خیر", callback_data="ignore_new_role"),
        )
        bot.send_message(message.chat.id, f" {json.dumps(roles, indent=4, ensure_ascii=False)}اطلاعات فوق را تایید می‌کنید؟\n", reply_markup=markup)


print("Bot running with proxy...")
bot.infinity_polling()
