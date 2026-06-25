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
    '@gamingsaidul', '@gamingsaidulchat', '@gamingsaidulapp', '@gamingsaidulgs', '@gamingsaidulnews'
]

WEBSITE_LINK = "https://gamingsaidulyt.blogspot.com" 
TASK_DURATION = 180  
FIREBASE_URL = "https://gs-free-i-come-default-rtdb.firebaseio.com/" 
FIREBASE_SECRET = "oL0LJgBqPGD2yppYuDltI4jDKCxSDYqAaVwZy2bX"

app = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)

# --- মূল ফাংশন ---
def get_user_data(user_id):
    try:
        url = f"{FIREBASE_URL}users/{user_id}.json?auth={FIREBASE_SECRET}"
        response = requests.get(url)
        data = response.json()
        if data is None:
            default = {'balance': 0.0, 'referred_by': None, 'referrals': 0, 'task_started_at': None, 'task_completed': False}
            requests.put(url, json=default)
            return default
        return data
    except:
        return {'balance': 0.0, 'referred_by': None, 'referrals': 0, 'task_started_at': None, 'task_completed': False}

def update_user_data(user_id, data):
    url = f"{FIREBASE_URL}users/{user_id}.json?auth={FIREBASE_SECRET}"
    requests.put(url, json=data)

def check_all_subscriptions(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']: return False
        except: return False
    return True

def send_force_join_msg(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    channel_names = ["Gaming Saidul 📢", "Gaming Saidul Chat 💬", "Gaming Saidul App 📱", "Gaming Saidul GS 🎮", "Gaming Saidul News 📰"]
    for i, channel in enumerate(REQUIRED_CHANNELS):
        markup.add(types.InlineKeyboardButton(channel_names[i], url=f"https://t.me/{channel.replace('@', '')}"))
    bot.send_message(user_id, "❌ আপনি সব চ্যানেলে জয়েন করেননি! কাজ করার আগে সব চ্যানেলে জয়েন থাকা বাধ্যতামূলক।", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    args = message.text.split()
    user_data = get_user_data(user_id)
    
    # রেফারেল লজিক (সাবস্ক্রিপশন চেক ছাড়াই হবে)
    if len(args) > 1 and referrer_id := args[1]:
        if referrer_id != str(user_id) and user_data.get('referred_by') is None:
            referrer_data = get_user_data(referrer_id)
            referrer_data['balance'] = referrer_data.get('balance', 0.0) + REFER_BONUS
            referrer_data['referrals'] = referrer_data.get('referrals', 0) + 1
            update_user_data(referrer_id, referrer_data)
            user_data['referred_by'] = referrer_id
            update_user_data(user_id, user_data)
            bot.send_message(referrer_id, f"🎉 নতুন রেফারেল! আপনি {REFER_BONUS} ⭐ বোনাস পেয়েছেন।")
            
    bot.send_message(user_id, "⚙️ স্বাগতম! কাজ শুরু করতে মেনু ব্যবহার করুন।", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("👤 Profile & Balance", "🔗 Referral Link", "💰 Withdraw", "🔄 Check Join"))

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

    # কঠোর সাবস্ক্রিপশন চেক
    if not check_all_subscriptions(user_id):
        send_force_join_msg(user_id)
        return

    # জয়েন করা থাকলে নিচের কোড কাজ করবে
    user_data = get_user_data(user_id)
    
    if text == "🔄 Check Join":
        if user_data.get('task_completed'):
            bot.send_message(user_id, "✅ আপনি অলরেডি সব কাজ শেষ করেছেন।")
        else:
            start_time = user_data.get('task_started_at')
            if start_time is None:
                user_data['task_started_at'] = time.time()
                update_user_data(user_id, user_data)
                bot.send_message(user_id, f"⚠️ ওয়েবসাইট ভিজিট করুন: {WEBSITE_LINK} (৩ মিনিট অপেক্ষা করুন)")
            else:
                if time.time() - start_time < TASK_DURATION:
                    bot.send_message(user_id, "⏳ কাজ চলছে, কিছুক্ষণ অপেক্ষা করুন।")
                else:
                    user_data['task_completed'] = True
                    user_data['balance'] = user_data.get('balance', 0.0) + 5.0 # টাস্ক বোনাস
                    update_user_data(user_id, user_data)
                    bot.send_message(user_id, "✅ টাস্ক সম্পন্ন হয়েছে! ৫ ⭐ বোনাস পেয়েছেন।")
                    if ref := user_data.get('referred_by'):
                        r_data = get_user_data(ref)
                        r_data['balance'] = r_data.get('balance', 0.0) + REFER_BONUS
                        update_user_data(ref, r_data)
                        bot.send_message(ref, "🎉 আপনার রেফার করা ইউজার টাস্ক শেষ করেছে!")

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
    json_str = request.stream.read().decode('UTF-8')
    bot.process_new_updates([telebot.types.Update.de_json(json_str)])
    return '!', 200

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{API_TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
