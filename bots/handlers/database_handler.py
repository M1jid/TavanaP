import json
import random
from telebot import types
from api_client import *
from utils.queue_manager import update_saved_queue, update_ignored_queue, update_skiped_queue

DATABASE = get_telegram_channels()
random.shuffle(DATABASE)
volume = len(DATABASE)
index = -1
assigned_items = []
user_current_item = {}

def get_new_channel():
    global index, DATABASE
    index += 1
    return DATABASE[index]

def send_next(bot, user_id):
    for item in DATABASE:
        try:
            if item['id'] not in assigned_items:
                user_current_item[user_id] = item
                assigned_items.append(item['id'])

                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("افزودن", callback_data="yes"),
                    types.InlineKeyboardButton("حذف", callback_data="no"),
                    types.InlineKeyboardButton("بعدی", callback_data="skip"),
                    types.InlineKeyboardButton("انصراف", callback_data="cancel_db_clean"),
                )
                bot.send_message(user_id, f"Item {index+1}/{volume-len(assigned_items)}\n{json.dumps(item, indent=4)}", reply_markup=markup)
                break
        except Exception:
            pass

def handle_db_callback(bot, call):
    user_id = call.message.chat.id
    
    if call.data == "cancel_db_clean":
        bot.edit_message_text("عملیات متوقف شد", chat_id=call.message.chat.id, message_id=call.message.message_id)
        return

    current_item = user_current_item.get(user_id)
    if not current_item:
        bot.answer_callback_query(call.id, "⚠️ No current item assigned to you.")
        return

    if call.data == "yes":
        update_saved_queue([current_item])
        bot.edit_message_text(f"✅ Added {current_item['value']}.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        update_telegram_channel(current_item['id'], {'subscribed_by': 1})
        send_next(bot, call.message.chat.id)

    elif call.data == "no":
        update_ignored_queue([current_item])
        bot.edit_message_text(f"❌ Ignored {current_item['value']}.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        update_telegram_channel(current_item['id'], {'blocked': True})
        send_next(bot, call.message.chat.id)

    elif call.data == "skip":
        update_skiped_queue([current_item])
        bot.edit_message_text(text=f"❌ Skiped {current_item['value']}.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        send_next(bot, call.message.chat.id)