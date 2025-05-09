from telegram import Bot

# استبدل بـ Token الخاص بالبوت
BOT_TOKEN = "YOUR_BOT_TOKEN"

def send_telegram_notification(user_id, message):
    """إرسال إشعار عبر التليجرام"""
    try:
        bot = Bot(BOT_TOKEN)
        bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        print(f"تعذر إرسال الإشعار: {e}")