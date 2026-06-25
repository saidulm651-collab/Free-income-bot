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

# --- ফায়ারবেস ফাংশন ---
def get_user_data(user_id):
    url = f"{FIREBASE_URL}users/{user_id}.json?auth={FIREBASE_SECRET}"
    response = requests.get(url).json()
    if response is None:
        default = {'balance': 0.0, 'referred_by': None, 'referrals': 0, 'task_completed': False, 'task_started_at': None}
        requests.put(url, json=default)
        return default
    return response

def update_user_data(user_id, data):
    requests.put(f"{FIREBASE_URL}users/{user_id}.json?auth={FIREBASE_SECRET}", json=data)

# --- সাবস্ক্রিপশন চেক ---
def check_sub(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ['member', 'administrator', 'creator']: return False
        except: return False
    return True

# --- বট হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1:
        data = get_user_data(user_id)
        if data.get('referred_by') is None:
            data['referred_by'] = args[1]
            update_user_data(user_id, data)
    bot.send_message(user_id, "স্বাগতম! কাজ শুরু করতে মেনু ব্যবহার করুন।", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("👤 Profile & Balance", "🔗 Referral Link", "💰 Withdraw", "🔄 Check Join"))

@bot.message_handler(func=lambda message: True)
def menu(message):
    user_id = message.from_user.id
    text = message.text

    # এডমিন কমান্ড
    if user_id == ADMIN_ID and text.startswith(("/add_bal", "/check_bal")):
        parts = text.split()
        if len(parts) >= 2:
            u_id = parts[1]
            d = get_user_data(u_id)
            if text.startswith("/add_bal"):
                d['balance'] = d.get('balance', 0.0) + float(parts[2])
                update_user_data(u_id, d)
                bot.reply_to(message, "✅ ব্যালেন্স যোগ করা হয়েছে।")
            else:
                bot.reply_to(message, f"💰 ব্যালেন্স: {d.get('balance', 0.0)}")
        return

    # সব বাটনের জন্য সাবস্ক্রিপশন চেক
    if not check_sub(user_id):
        markup = types.InlineKeyboardMarkup()
        for i, ch in enumerate(REQUIRED_CHANNELS):
            markup.add(types.InlineKeyboardButton(CHANNEL_NAMES[i], url=f"https://t.me/{ch.replace('@', '')}"))
        bot.send_message(user_id, "❌ আগে সবগুলো চ্যানেলে জয়েন করুন:", reply_markup=markup)
        return

    # মেনু লজিক
    data = get_user_data(user_id)
    if text == "🔄 Check Join":
        if data.get('task_completed'): bot.reply_to(message, "✅ আপনি অলরেডি কাজ শেষ করেছেন।")
        elif not data.get('task_started_at'):
            data['task_started_at'] = time.time()
            update_user_data(user_id, data)
            bot.reply_to(message, f"⚠️ ওয়েবসাইটে গিয়ে ৩ মিনিট থাকুন:\n{WEBSITE_LINK}")
        else:
            if time.time() - data.get('task_started_at') < TASK_DURATION: bot.reply_to(message, "⏳ কাজ চলছে...")
            else:
                data['task_completed'] = True
                data['balance'] = data.get('balance', 0.0) + 5.0
                update_user_data(user_id, data)
                bot.reply_to(message, "✅ টাস্ক শেষ! ৫ ⭐ পেয়েছেন।")
                if ref := data.get('referred_by'):
                    r_d = get_user_data(ref)
                    r_d['balance'] = r_d.get('balance', 0.0) + REFER_BONUS
                    update_user_data(ref, r_d)
                    bot.send_message(ref, f"🎉 আপনার রেফারেল কাজ শেষ করেছে! আপনি {REFER_BONUS} ⭐ পেয়েছেন।")
    elif text == "👤 Profile & Balance": bot.reply_to(message, f"💰 ব্যালেন্স: {data.get('balance', 0.0)} ⭐")
    elif text == "🔗 Referral Link": bot.reply_to(message, f"🔗 লিঙ্ক: https://t.me/{(bot.get_me()).username}?start={user_id}")
    elif text == "💰 Withdraw":
        if data.get('balance', 0.0) < MIN_WITHDRAW: bot.reply_to(message, f"❌ প্রয়োজন {MIN_WITHDRAW} ⭐")
        else: bot.reply_to(message, f"✅ এডমিনকে মেসেজ দিন: @{ADMIN_USERNAME}")

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode('UTF-8'))])
    return '!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
