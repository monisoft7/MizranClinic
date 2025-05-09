from database import DatabaseManager
from telegram_bot import EmployeeQueryBot
from main_window import MainWindow
from PyQt6.QtWidgets import QApplication
import threading
import sys
import asyncio

def run_telegram_bot():
    """تشغيل بوت التليجرام في خيط منفصل"""
    bot_token = "7798615366:AAGhr928M-PZ19usrx6yr2nG0mLBXvP3r0E"
    db = DatabaseManager()
    bot = EmployeeQueryBot(bot_token, db)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(bot.run())
    finally:
        loop.close()

if __name__ == '__main__':
    db_manager = DatabaseManager()
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow(db_manager)
    window.show()
    
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    sys.exit(app.exec())