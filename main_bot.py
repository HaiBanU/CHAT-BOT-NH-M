# file: main_bot.py (PHIÊN BẢN SỬA LỖI VÀ GIỚI HẠN GIỜ HOẠT ĐỘNG)

import telegram
import asyncio
import random
import os
import threading
from flask import Flask
from dotenv import load_dotenv
from kho_kich_ban import SCENARIOS
from datetime import datetime, timedelta
from collections import deque

# --- Tải các biến môi trường từ file .env ---
load_dotenv()

# --- LẤY GIÁ TRỊ TỪ BIẾN MÔI TRƯỜNG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# --- PHẦN CẤU HÌNH CHO BOT ---
# <<< THAY ĐỔI 1: CẬP NHẬT LẠI CÁC KHUNG GIỜ HOẠT ĐỘNG >>>
TIME_WINDOWS = {
    "morning": (6, 11),  # Bắt đầu từ 6h30
    "noon": (12, 13),
    "afternoon": (15, 17),
    "evening": (20, 22),
    "late_night": (23, 23), # Hoạt động trong khung 23h (đến 23h30)
    "interaction": (6, 23), # Hoạt động từ 6h30 đến 23h30
    "experience_motivation": (6, 23) # Hoạt động từ 6h30 đến 23h30
}
MESSAGE_INTERVAL_MINUTES = (15, 35)
AVOID_LAST_N_MESSAGES = 25

# --- KHỞI TẠO WEB SERVER VỚI FLASK ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

# --- PHẦN LOGIC CỦA BOT ---
bot = telegram.Bot(token=BOT_TOKEN)
recent_messages = {
    category: deque(maxlen=AVOID_LAST_N_MESSAGES)
    for category in SCENARIOS.keys()
}

def get_unique_random_message(category):
    possible_messages = SCENARIOS.get(category, [])
    if not possible_messages: return None
    for _ in range(10):
        message = random.choice(possible_messages)
        if message not in recent_messages[category]:
            recent_messages[category].append(message)
            return message
    return random.choice(possible_messages)

async def send_message(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã gửi: {message}")
    except Exception as e:
        print(f"❌ Lỗi khi gửi tin nhắn: {e}")

async def bot_main_loop():
    """Vòng lặp bất đồng bộ chính của bot."""
    print("▶️  Bot logic is starting...")
    next_send_time = {}
    for category in SCENARIOS.keys():
        delay = random.randint(MESSAGE_INTERVAL_MINUTES[0], MESSAGE_INTERVAL_MINUTES[1])
        next_send_time[category] = datetime.now() + timedelta(minutes=delay)

    while True:
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        # <<< THAY ĐỔI 2: CẬP NHẬT LOGIC "NGỦ" CHO BOT >>>
        # Bot sẽ "ngủ" từ 23:31 đến 06:29 sáng hôm sau
        is_sleeping_time = (current_hour == 23 and current_minute > 30) or current_hour < 6 or (current_hour == 6 and current_minute < 30)
        
        if is_sleeping_time:
            print(f"😴 [{now.strftime('%H:%M:%S')}] Bot đang trong giờ nghỉ ngơi... Sẽ kiểm tra lại sau 1 phút.")
            await asyncio.sleep(60) # Tạm dừng 1 phút rồi kiểm tra lại
            continue # Bỏ qua vòng lặp hiện tại và bắt đầu lại

        for category, (start_hour, end_hour) in TIME_WINDOWS.items():
            in_window = False
            if start_hour <= end_hour:
                if start_hour <= current_hour <= end_hour: in_window = True
            else: # Dành cho trường hợp qua đêm (không còn dùng trong phiên bản này)
                if current_hour >= start_hour or current_hour <= end_hour: in_window = True

            if in_window and now >= next_send_time.get(category, now):
                message = get_unique_random_message(category)
                if message:
                    await send_message(message)

                delay = random.randint(MESSAGE_INTERVAL_MINUTES[0], MESSAGE_INTERVAL_MINUTES[1])
                next_send_time[category] = now + timedelta(minutes=delay)
                await asyncio.sleep(5)

        await asyncio.sleep(10)

def run_flask_server():
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Khởi động máy chủ web trên cổng {port}...")
    app.run(host='0.0.0.0', port=port)

# --- KHỞI ĐỘNG ---
if __name__ == "__main__":
    print("🚀 Script bắt đầu thực thi...")

    if not BOT_TOKEN or not CHAT_ID:
        print("❌ LỖI NGHIÊM TRỌNG: Thiếu BOT_TOKEN hoặc CHAT_ID!")
    else:
        print("✅ Biến môi trường đã được tải.")
        bot_thread = threading.Thread(target=lambda: asyncio.run(bot_main_loop()))
        bot_thread.daemon = True
        bot_thread.start()

    # Chạy Flask trong luồng chính
    run_flask_server()