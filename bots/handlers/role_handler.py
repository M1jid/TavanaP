from telebot import types
from routing_roles import config
import json

def handle_roles(bot, call):
    markup = types.InlineKeyboardMarkup()
    for idx, option in enumerate(config):
        markup.add(types.InlineKeyboardButton(text=option['name'], callback_data=f"option_{idx}"))
    markup.add(types.InlineKeyboardButton(text='بازگشت', callback_data=f"home"))
    bot.send_message(call.message.chat.id, "لیست کانال های تعریف شده", reply_markup=markup)

def handle_role_option(bot, call):
    idx = int(call.data[len("option_"):])
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(text='افزودن به قوانین', callback_data=f"add_new_role_{idx}"),
        types.InlineKeyboardButton(text='حذف کانال', callback_data=f"remove_channel{idx}"),
        types.InlineKeyboardButton(text='بازگشت', callback_data=f"home"),
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=f"برای {config[idx]['name']} انتخاب کنید",
        reply_markup=markup,
    )

def handle_add_role(bot, call):
    idx = int(call.data[len("add_new_role_"):])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='بازگشت', callback_data=f"cancel_roles"))
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

def process_role_creation(bot, message, state_manager):
    roles = message.text.split('\n')
    roles = {'must': roles[0], 'should': roles[1], 'must_not': roles[2]}
    for role, data in roles.items():
        roles[role] = data.split('-')
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("بله", callback_data="accept_new_role"),
        types.InlineKeyboardButton("خیر", callback_data="ignore_new_role"),
    )
    bot.send_message(message.chat.id, f" {json.dumps(roles, indent=4, ensure_ascii=False)}اطلاعات فوق را تایید می‌کنید؟\n", reply_markup=markup)

def finalize_role_creation(bot, call, state_manager):
    if call.data == 'accept_new_role':
        data = state_manager.get_state(call.message.chat.id)['data']
        bot.send_message(call.message.chat.id, "قانون افزوده شد")
    else:
        bot.send_message(call.message.chat.id, "عملیات متوقف شد")
    state_manager.clear_state(call.message.chat.id)