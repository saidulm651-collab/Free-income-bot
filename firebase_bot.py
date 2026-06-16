import telebot
from telebot import types
import time
import requests
import json
import os
from flask import Flask
import threading

# --- ওয়েব সার্ভিসের জন্য ফ্লাস্ক ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    # রেন্ডারের জন্য এনভায়রনমেন্ট পোর্ট ব্যবহার করা উত্তম
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ----------------- [ সেটিংস ] -----------------
API_TOKEN = os.environ.get('API_TOKEN')
ADMIN_ID = 8426401567
ADMIN_USERNAME = "gamingsaidulyt"
REFER_BONUS = 3.0        
MIN_WITHDRAW = 100.0   

REQUIRED_CHANNELS = [
    '@gamingsaidul', '@gamingsaidulchat', '@gamingsaidulapp', '@gamingsaidulgs', '@gamingsaidulnews'
]

WEBSITE_LINK = "https://gamingsaidulyt.blogspot.com" 
TASK_DURATION = 180  

# Firebase Settings
FIREBASE_URL = "https://gs-free-i-come-default-rtdb.firebaseio.com/" 
FIREBASE_SECRET = "oL0LJgBqPGD2yppYuDltI4jDKCxSDYqAaVwZy2bX"
# ----------------------------------------------

bot = telebot.TeleBot(API_TOKEN)

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

def get_unjoined_channel(user_id):
    channel_names = ["Gaming Saidul 📢", "Gaming Saidul Chat 💬", "Gaming Saidul App 📱", "Gaming Saidul GS 🎮", "Gaming Saidul News 📰"]
    for i, channel in enumerate(REQUIRED_CHANNELS):
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']: return channel_names[i]
        except: return channel_names[i]
    return None

def send_force_join_msg(user_id, text):
    markup = types.InlineKeyboardMarkup(row_width=1)
    channel_names = ["Gaming Saidul 📢", "Gaming Saidul Chat 💬", "Gaming Saidul App 📱", "Gaming Saidul GS 🎮", "Gaming Saidul News 📰"]
    for i, channel in enumerate(REQUIRED_CHANNELS):
        markup.add(types.InlineKeyboardButton(channel_names[i], url=f"https://t.me/{channel.replace('@', '')}"))
    markup.add(types.InlineKeyboardButton("🌐 Visit Website (৩ মিনিট বাধ্যতামূলক)", url=WEBSITE_LINK))
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    bot.send_message(user_id, "⚙️ মেনু লোড হচ্ছে...", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("👤 Profile & Balance", "🔗 Referral Link", "💰 Withdraw", "🔄 Check Join"))

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id
    text = message.text
    
    if text.startswith("/check_bal") or text.startswith("/add_bal") or text.startswith("/sub_bal"):
        if user_id == ADMIN_ID:
            parts = text.split()
            if len(parts) < 2: return
            target_id = parts[1]
            target_data = get_user_data(target_id)
            
            if text.startswith("/check_bal"):
                bot.send_message(user_id, f"👤 User {target_id} এর বর্তমান ব্যালেন্স: {target_data.get('balance', 0.0)} ⭐")
            elif text.startswith("/add_bal") and len(parts) == 3:
                amount = float(parts[2])
                target_data['balance'] = target_data.get('balance', 0.0) + amount
                update_user_data(target_id, target_data)
                bot.send_message(user_id, f"✅ যোগ করা হয়েছে। নতুন ব্যালেন্স: {target_data['balance']} ⭐")
            elif text.startswith("/sub_bal") and len(parts) == 3:
                amount = float(parts[2])
                target_data['balance'] = target_data.get('balance', 0.0) - amount
                update_user_data(target_id, target_data)
                bot.send_message(user_id, f"✅ কমানো হয়েছে। নতুন ব্যালেন্স: {target_data['balance']} ⭐")
        return

    user_data = get_user_data(user_id)
    is_subscribed = check_all_subscriptions(user_id)
    task_done = user_data.get('task_completed', False)

    if not is_subscribed and text != "🔄 Check Join":
        send_force_join_msg(user_id, f"❌ আগে সবগুলো চ্যানেলে জয়েন করুন। এখনো বাকি: **{get_unjoined_channel(user_id)}**")
        return

    if text == "🔄 Check Join":
        if not is_subscribed:
            send_force_join_msg(user_id, f"❌ এখনো জয়েন করেননি: **{get_unjoined_channel(user_id)}**")
        elif not task_done:
            start_time = user_data.get('task_started_at')
            if start_time is None:
                user_data['task_started_at'] = time.time()
                update_user_data(user_id, user_data)
                bot.send_message(user_id, "⚠️ ওয়েবসাইট লিংকে ক্লিক করে ৩ মিনিট ভিজিট করুন।")
            else:
                elapsed = time.time() - start_time
                if elapsed < TASK_DURATION:
                    bot.send_message(user_id, f"⏳ আরও {int((TASK_DURATION - elapsed)//60)} মিনিট অপেক্ষা করুন।")
                else:
                    user_data['task_completed'] = True
                    update_user_data(user_id, user_data)
                    bot.send_message(user_id, "✅ টাস্ক সম্পন্ন হয়েছে!")
        else:
            bot.send_message(user_id, "✅ আপনি অলরেডি সব কাজ শেষ করেছেন।")

    elif text == "👤 Profile & Balance":
        bot.send_message(user_id, f"💰 ব্যালেন্স: {user_data.get('balance', 0.0)} ⭐")

    elif text == "🔗 Referral Link":
        bot.send_message(user_id, f"🔗 লিঙ্ক: https://t.me/{(bot.get_me()).username}?start={user_id}")

    elif text == "💰 Withdraw":
        bal = user_data.get('balance', 0.0)
        if bal < MIN_WITHDRAW:
            bot.send_message(user_id, f"❌ পর্যাপ্ত ব্যালেন্স নেই। প্রয়োজন {MIN_WITHDRAW} ⭐।")
        else:
            bot.send_message(user_id, f"✅ এডমিনকে মেসেজ দিন: @{ADMIN_USERNAME}")

import sys

# কোডের এই অংশটি দিয়ে আপনার বর্তমান পোলিং অংশটি রিপ্লেস করা হয়েছে:
try:
    print("Starting bot polling...")
    # timeout বাড়ানো হয়েছে যাতে সার্ভার কানেকশন ড্রপ না করে
    bot.infinity_polling(
        none_stop=True, 
        timeout=120, 
        long_polling_timeout=120, 
        allowed_updates=None
    )
except Exception as e:
    print(f"Polling crashed: {e}")
    sys.exit(1) # রেন্ডারকে সার্ভিস রিস্টার্ট নিতে বাধ্য করা
