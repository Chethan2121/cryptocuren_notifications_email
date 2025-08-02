import os
import smtplib
import requests
import matplotlib.pyplot as plt
from datetime import datetime
from email.message import EmailMessage
from io import BytesIO

# Read email credentials from environment
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TO_EMAILS_RAW = os.environ.get("TO_EMAILS")  # comma-separated emails
TO_EMAILS = [email.strip() for email in TO_EMAILS_RAW.split(",")]

COINS = {
    "bitcoin": "Bitcoin",
    "worldcoin-wld": "Worldcoin"
}

CURRENCY = "inr"
COINGECKO_API = "https://api.coingecko.com/api/v3"

def get_price_summary(coin_id):
    url = f"{COINGECKO_API}/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false"
    }
    response = requests.get(url, params=params)
    data = response.json()

    current_price = data["market_data"]["current_price"][CURRENCY]
    change_1h = data["market_data"]["price_change_percentage_1h_in_currency"][CURRENCY]
    change_24h = data["market_data"]["price_change_percentage_24h_in_currency"][CURRENCY]
    change_7d = data["market_data"]["price_change_percentage_7d_in_currency"][CURRENCY]
    change_14d = data["market_data"]["price_change_percentage_14d_in_currency"][CURRENCY]
    change_30d = data["market_data"]["price_change_percentage_30d_in_currency"][CURRENCY]

    return {
        "price": current_price,
        "1h": change_1h,
        "24h": change_24h,
        "7d": change_7d,
        "14d": change_14d,
        "30d": change_30d
    }

def get_chart_image(coin_id):
    url = f"{COINGECKO_API}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": CURRENCY,
        "days": "1",
        "interval": "hourly"
    }
    response = requests.get(url, params=params)
    prices = response.json()["prices"]

    times = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
    values = [p[1] for p in prices]

    # Plot and save image to memory
    plt.figure(figsize=(6, 4))
    plt.plot(times, values, label=COINS[coin_id], color="blue")
    plt.title(f"{COINS[coin_id]} Price (Last 24h)")
    plt.xlabel("Time")
    plt.ylabel(f"Price in {CURRENCY.upper()}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close()
    img_bytes.seek(0)
    return img_bytes

def build_email():
    msg = EmailMessage()
    msg["Subject"] = "📈 INR Crypto Price Report (Bitcoin + Worldcoin)"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(TO_EMAILS)

    html_content = "<h2>📊 INR Crypto Price Summary</h2>"

    for idx, coin_id in enumerate(COINS):
        summary = get_price_summary(coin_id)
        image_bytes = get_chart_image(coin_id)

        # Embed image
        img_cid = f"image{idx}"
        msg.add_attachment(image_bytes.read(),
                           maintype='image',
                           subtype='png',
                           filename=f"{coin_id}.png",
                           cid=img_cid)

        html_content += f"""
        <h3>{COINS[coin_id]} - ₹{summary['price']:,.2f}</h3>
        <ul>
            <li>1h: {summary['1h']:.2f}%</li>
            <li>24h: {summary['24h']:.2f}%</li>
            <li>7d: {summary['7d']:.2f}%</li>
            <li>14d: {summary['14d']:.2f}%</li>
            <li>30d: {summary['30d']:.2f}%</li>
        </ul>
        <img src="cid:{img_cid}" width="500"><br><br>
        """

    msg.set_content("INR Crypto Price Summary (with charts)")
    msg.add_alternative(html_content, subtype='html')
    return msg

def send_email(msg):
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    try:
        email_msg = build_email()
        send_email(email_msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
