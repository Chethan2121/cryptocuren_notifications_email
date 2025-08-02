import os
import smtplib
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from io import BytesIO

# Configuration
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
TO_EMAILS_RAW = os.environ.get('TO_EMAILS')  # comma-separated
TO_EMAILS = TO_EMAILS_RAW.split(',')

COINS = {
    'bitcoin': 'Bitcoin',
    'worldcoin': 'Worldcoin-WLD',
    'dogecoin': 'Dogecoin',
    'cardano': 'Cardano',
    'solana': 'Solana',
    'polkadot': 'Polkadot',
    'kaspa': 'Kaspa',
    'ergo': 'Ergo',
    'monero': 'Monero',
    'ethereum-classic': 'Ethereum Classic',
    'litecoin': 'Litecoin'
}

def get_price_and_history(coin_id):
    url_price = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=inr&include_24hr_change=true"
    url_chart = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=inr&days=1"

    price_res = requests.get(url_price).json()
    chart_res = requests.get(url_chart).json()

    price = price_res.get(coin_id, {}).get("inr", 0)
    change_24h = price_res.get(coin_id, {}).get("inr_24h_change", 0)

    prices = chart_res.get("prices", [])

    times = [datetime.fromtimestamp(ts / 1000) for ts, _ in prices]
    values = [val for _, val in prices]

    return price, change_24h, times, values

def plot_graph(times, values, coin_id):
    plt.figure(figsize=(6, 3))
    plt.plot(times, values, label=COINS[coin_id], color="blue")
    plt.title(f"{COINS[coin_id]} - Last 24h")
    plt.xlabel("Time")
    plt.ylabel("INR Price")
    plt.xticks(rotation=45)
    plt.tight_layout()

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()
    img_buffer.seek(0)
    return img_buffer

def create_email():
    msg = MIMEMultipart('related')
    msg['Subject'] = "📈 INR Crypto Price Report + Profit/Loss Summary"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(TO_EMAILS)

    html = """<html><body>
    <h2>📈 INR Crypto Price Report + Profit/Loss Summary</h2>
    """

    images = []

    for i, coin_id in enumerate(COINS.keys()):
        try:
            price, change_24h, times, values = get_price_and_history(coin_id)
            html += f"<h3>{COINS[coin_id]} - ₹{price:,.2f}</h3>"
            html += f"<p>24h Change: {change_24h:.2f}%</p>"
            cid = f'image{i}'
            html += f'<img src="cid:{cid}" width="600"><br><br>'

            img_buffer = plot_graph(times, values, coin_id)
            img_part = MIMEImage(img_buffer.read(), _subtype="png")
            img_part.add_header('Content-ID', f'<{cid}>')
            img_part.add_header('Content-Disposition', 'inline', filename=f"{coin_id}.png")
            images.append(img_part)
        except Exception as e:
            html += f"<p><b>{COINS[coin_id]}:</b> Error fetching data: {str(e)}</p>"

    html += "</body></html>"

    msg.attach(MIMEText(html, 'html'))

    for img in images:
        msg.attach(img)

    return msg

def send_email():
    msg = create_email()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# Run the script
if __name__ == "__main__":
    send_email()
