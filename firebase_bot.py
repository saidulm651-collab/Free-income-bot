import telebot
from telebot import types
import time
import requests
import os
from flask import Flask, request

# --- সেটিংস ---
API_TOKEN = os.environ.get('API_TOKEN')
WEBHOOK_URL = "https://free-income-bot-sxd6.onrender.com" 
ADMIN_ID = 8426401567
ADMIN_USERNAME = "gamingsaidulyt"
REFER_BONUS = 3.0        
MIN_WITHDRAW = 100.0   

REQUIRED_CHANNELS = [
    '@gamingsaidul', '@gamingsaidulchat', '@gamingsaidulapp', '@gamingsaidulgs', '@gamingsaidulnews', '@gamingsaidulextra'
]

CHANNEL_NAMES = [
    "Gaming Saidul 📢", "Gaming Saidul Chat 💬", "Gaming Saidul App 📱", 
    "Gaming Saidul GS 🎮", "Gaming Saidul News 📰", "Gaming Saidul Extra ⚡"
]

WEBSITE_LINK = "https://gamingsaidulyt.blogspot.com" 
TASK_DURATION = 180  
FIREBASE_URL = "https://gs-free-i-come-default-rtdb.firebaseio.com/" 
FIREBASE_SECRET = "oL0LJgBqPGD2yppYuDltI4jDKCxSDYqAaVwZy2bX"

app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)

# --- ফাংশনসমূহ ---
def get_user_data(user_id):
    try:
        url = f"{FIREBASE_URL}users/{user_id}.json?auth={FIREBASE_SECRET}"
        data = requests.get(url).json()
        if data is None:
            default = {'balance': 0.0, 'referred_by': None, 'referrals': 0, 'task_completed': False, 'task_started_at': None}
            requests.put(url, json=default)
            return default
        return data
    except: return {'balance': 0.0, 'referred_by': None, 'referrals': 0, 'task_completed': False, 'task_started_at': None}

def update_user_data(user_id, data):
    requests.put(f"{FIREBASE_URL}users/{user_id}.json?auth={FIREBASE_SECRET}", json=data)

def check_all_subscriptions(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            if bot.get_chat_member(channel, user_id).status not in ['member', 'administrator', 'creator']: return False
        except: return False
    return True

def send_force_join_msg(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, ch in enumerate(REQUIRED_CHANNELS):
        markup.add(types.InlineKeyboardButton(CHANNEL_NAMES[i], url=f"https://t.me/{ch.replace('@', '')}"))
    bot.send_message(user_id, "❌ কাজ করার আগে সব চ্যানেলে জয়েন থাকা বাধ্যতামূলক।", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    args = message.text.split()
    user_data = get_user_data(user_id)
    
    # রেফারেল চেক
    if len(args) > 1:
        referrer_id = args[1]
        if referrer_id != str(user_id) and user_data.get('referred_by') is None:
            user_data['referred_by'] = referrer_id
            update_user_data(user_id, user_data)
            bot.send_message(user_id, "🎉 আপনি রেফারেল লিঙ্কের মাধ্যমে এসেছেন।")
            
    bot.send_message(user_id, "⚙️ স্বাগতম! মেনু ব্যবহার করুন।", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("👤 Profile & Balance", "🔗 Referral Link", "💰 Withdraw", "🔄 Check Join"))

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    text = message.text

    # এডমিন কমান্ড
    if text.startswith(("/check_bal", "/add_bal", "/sub_bal")) and user_id == ADMIN_ID:
        parts = text.split()
        if len(parts) >= 2:
            target_id = parts[1]
            target_data = get_user_data(target_id)
            if text.startswith("/check_bal"): bot.send_message(user_id, f"👤 User {target_id} ব্যালেন্স: {target_data.get('balance', 0.0)}")
            elif text.startswith("/add_bal") and len(parts) == 3:
                target_data['balance'] = target_data.get('balance', 0.0) + float(parts[2])
                update_user_data(target_id, target_data)
                bot.send_message(user_id, "✅ যোগ হয়েছে।")
        return

    # সাবস্ক্রিপশন চেক
    if not check_all_subscriptions(user_id):
        send_force_join_msg(user_id)
        return

    user_data = get_user_data(user_id)
    
    if text == "🔄 Check Join":
        if user_data.get('task_completed'):
            bot.send_message(user_id, "✅ আপনি অলরেডি টাস্ক শেষ করেছেন।")
        else:
            start_time = user_data.get('task_started_at')
            if start_time is None:
                user_data['task_started_at'] = time.time()
                update_user_data(user_id, user_data)
                bot.send_message(user_id, f"⚠️ ওয়েবসাইট ভিজিট করুন: {WEBSITE_LINK} (৩ মিনিট অপেক্ষা করুন)")
            elif time.time() - start_time < TASK_DURATION:
                bot.send_message(user_id, "⏳ কাজ চলছে, কিছুক্ষণ অপেক্ষা করুন।")
            else:
                user_data['task_completed'] = True
                update_user_data(user_id, user_data)
                bot.send_message(user_id, "✅ টাস্ক সম্পন্ন হয়েছে!")
                # রেফারার বোনাস ও নোটিফিকেশন
                if ref := user_data.get('referred_by'):
                    r_data = get_user_data(ref)
                    r_data['balance'] = r_data.get('balance', 0.0) + REFER_BONUS
                    r_data['referrals'] = r_data.get('referrals', 0) + 1
                    update_user_data(ref, r_data)
                    bot.send_message(ref, f"🎉 নতুন রেফারেল টাস্ক শেষ করেছে! আপনি {REFER_BONUS} ⭐ বোনাস পেয়েছেন।")

    elif text == "👤 Profile & Balance":
        bot.send_message(user_id, f"💰 ব্যালেন্স: {user_data.get('balance', 0.0)} ⭐")
    elif text == "🔗 Referral Link":
        bot.send_message(user_id, f"🔗 লিঙ্ক: https://t.me/{(bot.get_me()).username}?start={user_id}")
    elif text == "💰 Withdraw":
        if user_data.get('balance', 0.0) < MIN_WITHDRAW:
            bot.send_message(user_id, f"❌ প্রয়োজন {MIN_WITHDRAW} ⭐।")
        else:
            bot.send_message(user_id, f"✅ এডমিনকে মেসেজ দিন: @{ADMIN_USERNAME}")

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode('UTF-8'))])
    return '!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
