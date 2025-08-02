import os
import requests
import smtplib
import csv
import time
from datetime import datetime
from email.message import EmailMessage
from email.utils import make_msgid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --------------------------
# Read from GitHub Secrets
# --------------------------
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
TO_EMAILS_RAW = os.environ.get('TO_EMAILS')

if not EMAIL_ADDRESS or not EMAIL_PASSWORD or not TO_EMAILS_RAW:
    raise EnvironmentError("❌ Missing EMAIL_ADDRESS, EMAIL_PASSWORD, or TO_EMAILS environment variables.")

TO_EMAILS = [email.strip() for email in TO_EMAILS_RAW.split(',')]

# --------------------------
# Crypto Watchlist (use correct CoinGecko IDs)
# --------------------------
CRYPTO_WATCHLIST = [
    'bitcoin',
    'worldcoin-wld',
    'dogecoin',
    'cardano',
    'solana',
    'polkadot',
    'kaspa',
    'ergo',
    'monero',
    'ethereum-classic',
    'litecoin'
]

# --------------------------
# Fetch Summary Data from CoinGecko
# --------------------------
def get_crypto_data(coin):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}?localization=false&tickers=false&market_data=true"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        market_data = data['market_data']
        inr_price = market_data['current_price']['inr']
        price_changes = {
            '1h': market_data['price_change_percentage_1h_in_currency']['inr'],
            '24h': market_data['price_change_percentage_24h_in_currency']['inr'],
            '7d': market_data['price_change_percentage_7d_in_currency']['inr'],
            '14d': market_data['price_change_percentage_14d_in_currency']['inr'],
            '30d': market_data['price_change_percentage_30d_in_currency']['inr']
        }
        return inr_price, price_changes
    except Exception as e:
        print(f"❌ Error fetching summary data for {coin}: {e}")
        return None, {}

# --------------------------
# Fetch Historical Prices (last 24h)
# --------------------------
def fetch_24h_history(coin):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    params = {'vs_currency': 'inr', 'days': 1, 'interval': 'hourly'}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data['prices']  # List of [timestamp, price]
    except Exception as e:
        print(f"❌ Error fetching historical data for {coin}: {e}")
        return []

# --------------------------
# Plot Line Graph for a Coin
# --------------------------
def plot_line_graph(coin, history):
    timestamps = [datetime.fromtimestamp(p[0]/1000) for p in history]
    prices = [p[1] for p in history]

    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, prices, color='dodgerblue')
    plt.title(f"{coin.upper()} - 24h INR Price Trend")
    plt.xlabel("Time")
    plt.ylabel("Price (INR)")
    plt.grid(True)
    plt.tight_layout()

    filename = f"{coin}_24h.png"
    plt.savefig(filename)
    plt.close()
    return filename

# --------------------------
# Send Email with Inline Charts
# --------------------------
def send_summary_email(summary, chart_paths):
    msg = EmailMessage()
    msg['Subject'] = "📊 INR Crypto Prices + 24h Line Graphs"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(TO_EMAILS)

    msg.set_content("This email contains HTML charts. Please view it in an HTML-compatible email client.")
    html = "<html><body>"
    html += "<h2>📈 INR Crypto Price Report + Profit/Loss Summary</h2>"
    html += f"<pre style='font-family: monospace; font-size: 14px'>{summary}</pre>"

    for coin, path in chart_paths.items():
        cid = make_msgid(domain='crypto.local')[1:-1]
        with open(path, 'rb') as img:
            msg.get_payload()[0].add_related(img.read(), 'image', 'png', cid=f"<{cid}>")
        html += f"<h3>{coin.upper()} - 24h Chart</h3>"
        html += f"<img src='cid:{cid}' style='width:600px'><br><br>"

    html += "</body></html>"
    msg.add_alternative(html, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print("✅ Email sent to:", ", ".join(TO_EMAILS))

# --------------------------
# Log Prices to CSV
# --------------------------
def log_to_csv(log_data):
    filename = "crypto_price_log.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            header = ["Time", "Coin", "Price (INR)", "1h%", "24h%", "7d%", "14d%", "30d%"]
            writer.writerow(header)
        for row in log_data:
            writer.writerow(row)

# --------------------------
# Main
# --------------------------
def generate_report():
    summary = ""
    log_data = []
    chart_paths = {}

    for coin in CRYPTO_WATCHLIST:
        print(f"🔍 Processing {coin}...")
        price, changes = get_crypto_data(coin)
        if price is None:
            print(f"⚠️ Skipping {coin}")
            continue

        print(f"✅ {coin.upper()} - ₹{price:,.2f}")
        summary += f"{coin.upper()} - ₹{price:,.2f}\n"
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), coin.upper(), price]

        for interval in ['1h', '24h', '7d', '14d', '30d']:
            val = changes.get(interval)
            if val is not None:
                summary += f"  • {interval}: {val:.2f}%\n"
                row.append(val)
            else:
                summary += f"  • {interval}: ❌\n"
                row.append("N/A")

        summary += "\n"
        log_data.append(row)

        history = fetch_24h_history(coin)
        if history:
            chart_path = plot_line_graph(coin, history)
            chart_paths[coin] = chart_path
        else:
            print(f"⚠️ No 24h history for {coin}")

        time.sleep(1)  # CoinGecko rate limit

    log_to_csv(log_data)
    send_summary_email(summary, chart_paths)

if __name__ == '__main__':
    generate_report()
