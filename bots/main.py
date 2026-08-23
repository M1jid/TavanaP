import telebot
from telebot import types
from config import TOKEN, PROXY, USER_IDS
from handlers import (
    database_handler,
    channel_handler,
    account_handler,
    role_handler
)
from utils.state_manager import StateManager

# Initialize bot
telebot.apihelper.proxy = PROXY
bot = telebot.TeleBot(TOKEN)

# Setup menu
menu_button = types.MenuButtonCommands()
bot.set_chat_menu_button(menu_button=menu_button)
commands = [types.BotCommand("start", "شروع دوباره")]
bot.set_my_commands(commands)

# Initialize state manager
state_manager = StateManager()


def home(chat_id, message_id):
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
    state_manager.clear_state(message.chat.id)
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("پاکسازی دیتابیس", callback_data="db"),
        types.InlineKeyboardButton("افزودن کانال تلگرامی", callback_data="add_channel"),
        types.InlineKeyboardButton("افزودن اکانت تلگرامی", callback_data="add_account"),
        types.InlineKeyboardButton("قوانین", callback_data="roles"),
    )
    bot.send_message(message.chat.id, "به ربات دستیار خوش‌آمدید.\nخدمات:\n", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["db", "add_channel", "add_account", "roles"])
def handle_main_menu(call):
    if call.message.chat.id not in USER_IDS:
        bot.answer_callback_query(call.id, "⚠️ عدم دسترسی لازم")
        return

    if call.data == "db":
        state_manager.update_state(call.message.chat.id, "cleane_database")
        database_handler.send_next(bot, call.message.chat.id)
    elif call.data == "add_channel":
        state_manager.update_state(call.message.chat.id, "awaiting_channel_url")
        channel_handler.handle_add_channel(bot, call)
    elif call.data == "add_account":
        state_manager.update_state(call.message.chat.id, "awaiting_account_phone_number")
        account_handler.handle_add_account(bot, call)
    elif call.data == "roles":
        role_handler.handle_roles(bot, call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("option_"))
def handle_role_options(call):
    role_handler.handle_role_option(bot, call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_new_role_"))
def handle_add_role(call):
    state_manager.update_state(call.message.chat.id, "adding_channel_role")
    role_handler.handle_add_role(bot, call)

@bot.callback_query_handler(func=lambda call: call.data in ["yes", "no", "skip", "cancel_db_clean"])
def handle_db_actions(call):
    database_handler.handle_db_callback(bot, call)

@bot.callback_query_handler(func=lambda call: call.data in ["ignore_new_account"])
def handle_account_actions(call):
    account_handler.drop_account_creation(bot, call, state_manager)
    home(chat_id=call.message.chat.id, message_id=call.message.id)

@bot.callback_query_handler(func=lambda call: call.data in ["skip_api_id", "skip_api_hash", "skip_session_file"])
def handle_account_actions(call):
    account_handler.process_account_creation(bot, call.message, state_manager=state_manager, skip=True)

@bot.callback_query_handler(func=lambda call: call.data in ["accept_new_account"])
def handle_account_actions(call):
    account_handler.finalize_account_creation(bot, call, state_manager)

@bot.callback_query_handler(func=lambda call: call.data in ["accept_new_role", "ignore_new_role"])
def handle_role_actions(call):
    role_handler.finalize_role_creation(bot, call, state_manager)

@bot.callback_query_handler(func=lambda call: call.data in ["home", "cancel_roles", "cancel_add_account"])
def handle_cancel_actions(call):
    state_manager.clear_state(call.message.chat.id)
    if call.data == "home":
        home(chat_id=call.message.chat.id, message_id=call.message.id)

@bot.message_handler(func=lambda msg: state_manager.get_state(msg.chat.id), content_types=['text', 'document'])
def handle_state_messages(message):
    state_data = state_manager.get_state(message.chat.id)
    state = state_data["state"]

    if state == "awaiting_channel_url":
        channel_handler.process_channel_url(bot, message, state_manager)
    elif state in ["awaiting_account_phone_number", "awaiting_account_api_id", 
                  "awaiting_account_api_hash", "awaiting_session_file"]:
        account_handler.process_account_creation(bot, message, state_manager)
    elif state == "adding_channel_role":
        role_handler.process_role_creation(bot, message, state_manager)

print("Bot running with proxy...")
bot.infinity_polling()
