from telebot import types
from api_client import create_telegram_account

def handle_add_account(bot, call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("انصراف", callback_data="home"))
    bot.edit_message_text(chat_id=call.message.chat.id, text="شماره تلفن را وارد کنید:", reply_markup=markup, message_id=call.message.id)

def process_account_creation(bot, message, state_manager, skip=False):
    state_data = state_manager.get_state(message.chat.id)
    state = state_data["state"]
    data = state_data["data"]

    if state == "awaiting_account_phone_number":
        data['phone'] = int(message.text)
        state_manager.update_state(message.chat.id, "awaiting_account_api_id", data)
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("ندارم api_id", callback_data="skip_api_id"),
            types.InlineKeyboardButton("انصراف", callback_data="home"),
        )
        bot.delete_message(chat_id=message.chat.id, message_id=message.id)
        bot.send_message(chat_id=message.chat.id, text=":حساب کاربری را وارد کنید api_id", reply_markup=markup)

    elif state == "awaiting_account_api_id":
        if not skip:
            data['api_id'] = int(message.text)
        else:
            data['api_id'] = 16846146
        state_manager.update_state(message.chat.id, "awaiting_account_api_hash", data)
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("ندارم api_hash", callback_data="skip_api_hash"),
            types.InlineKeyboardButton("انصراف", callback_data="home"),
        )

        bot.send_message(chat_id=message.chat.id, text=":حساب کاربری را وارد کنید api_hash", reply_markup=markup)

    elif state == "awaiting_account_api_hash":
        if not skip:
            data['api_hash'] = message.text
        else:
            data['api_hash'] = "456ce17312b69e7422a148cde39ee834"
        state_manager.update_state(message.chat.id, "awaiting_session_file", data)
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("ندارم session_file", callback_data="skip_session_file"),
            types.InlineKeyboardButton("انصراف", callback_data="home"),
        )
        bot.send_message(chat_id=message.chat.id, text=":حساب کاربری را آپلود کنید session_file", reply_markup=markup)

    elif state == "awaiting_session_file":
        if message and message.content_type == "document":
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            filename = f"{data['phone']}.session"
            with open(f"/home/appuser/services/conf/sessions/{filename}", "wb") as f:
                f.write(downloaded_file)
            data['session_file'] = filename

        state_manager.update_state(message.chat.id, "accept_new_account", data)
        new_account = (
            f"اطلاعات فوق را تایید می‌کنید؟\n"
            f"Phone number: {data['phone']}\n"
            f"api_id: {data['api_id']}\n"
            f"api_hash: {data['api_hash']}\n"
        )
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("بله", callback_data="accept_new_account"),
            types.InlineKeyboardButton("خیر", callback_data="ignore_new_account"),
        )
        bot.send_message(message.chat.id, new_account, reply_markup=markup)


def drop_account_creation(bot, call, state_manager):
    state_manager.clear_state(call.message.chat.id)


def finalize_account_creation(bot, call, state_manager):
    state_data = state_manager.get_state(call.message.chat.id)
    if call.data == 'accept_new_account':
        data = state_data['data']
        data['process'] = 0            
        result = create_telegram_account(data=data)
        bot.send_message(call.message.chat.id, "حساب کاربری ذخیره شد")
    else:
        bot.send_message(call.message.chat.id, "عملیات متوقف شد")
    state_manager.clear_state(call.message.chat.id)
