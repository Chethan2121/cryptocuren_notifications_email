import os
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid

# ENV variables (you must set these in your environment)
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
TO_EMAILS = os.environ.get('TO_EMAILS', '').split(',')

COINS = {
    'bitcoin': 'Bitcoin',
    'worldcoin': 'Worldcoin'
}
CURRENCY = 'inr'

def get_current_prices():
    ids = ','.join(COINS.keys())
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies={CURRENCY}'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return {COINS[coin]: data[coin][CURRENCY] for coin in COINS}

def get_price_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={CURRENCY}&days=0.5&interval=hourly"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data['prices']  # List of [timestamp, price]

def generate_chart(coin_id, prices):
    times = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
    values = [p[1] for p in prices]

    plt.figure(figsize=(8, 4))
    plt.plot(times, values, marker='o', linestyle='-', color='blue')
    plt.title(f"{COINS[coin_id]} - Last 12 Hours Price (INR)")
    plt.xlabel("Time")
    plt.ylabel("Price (INR)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    filename = f"{coin_id}_12h.png"
    plt.savefig(filename)
    plt.close()
    return filename

def send_summary_email(prices, chart_paths):
    msg = EmailMessage()
    msg['Subject'] = "📈 Bitcoin & Worldcoin Report (INR) + 12h Graph"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ', '.join(TO_EMAILS)

    summary = "\n".join([f"{coin}: ₹{price:,.2f}" for coin, price in prices.items()])
    msg.set_content(f"Crypto Report\n\n{summary}")

    html = "<html><body>"
    html += "<h2>📈 INR Crypto Price Report</h2>"
    html += "<pre style='font-family: monospace; font-size: 14px'>" + summary + "</pre>"

    cid_map = {}

    for coin_id, path in chart_paths.items():
        coin_name = COINS[coin_id]
        cid = make_msgid(domain='crypto.local')[1:-1]
        cid_map[coin_id] = cid

        with open(path, 'rb') as img:
            msg.add_related(img.read(), maintype='image', subtype='png', cid=f"<{cid}>", filename=path)

    html += "<hr>"

    for coin_id, cid in cid_map.items():
        html += f"<h3>{COINS[coin_id]} - Last 12 Hours</h3>"
        html += f"<img src='cid:{cid}' style='width:600px;'><br><br>"

    html += "</body></html>"
    msg.add_alternative(html, subtype='html')

    # Send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print("✅ Email sent to:", ", ".join(TO_EMAILS))

def main():
    try:
        current_prices = get_current_prices()
        chart_paths = {}

        for coin_id in COINS:
            prices = get_price_history(coin_id)
            chart_path = generate_chart(coin_id, prices)
            chart_paths[coin_id] = chart_path

        send_summary_email(current_prices, chart_paths)

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    main()
