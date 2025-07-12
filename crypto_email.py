import os
import requests
import smtplib
from email.message import EmailMessage

# --------------------------
# Read from GitHub Secrets
# --------------------------
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
TO_EMAIL = os.environ.get('TO_EMAIL')

# --------------------------
# Crypto Watchlist
# --------------------------
CRYPTO_WATCHLIST = {
    'bitcoin': {'threshold': 60000},
    'ethereum': {'threshold': 3500},
    'dogecoin': {'threshold': 0.1}
}

# --------------------------
# Fetch Current Price
# --------------------------
def get_crypto_price(coin):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd'
    try:
        response = requests.get(url)
        data = response.json()
        return data[coin]['usd']
    except Exception as e:
        print(f"Error fetching price for {coin}: {e}")
        return None

# --------------------------
# Send Email
# --------------------------
def send_email(subject, content):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg.set_content(content)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print("✅ Email sent successfully.")

# --------------------------
# Main Logic
# --------------------------
def check_prices():
    for coin, details in CRYPTO_WATCHLIST.items():
        price = get_crypto_price(coin)
        if price is None:
            continue
        print(f"{coin.capitalize()} is at ${price}")
        if price >= details['threshold']:
            subject = f"{coin.capitalize()} 🚀 Price Alert!"
            content = f"The price of {coin} is now ${price}, which is above your alert threshold of ${details['threshold']}."
            send_email(subject, content)

if __name__ == '__main__':
    check_prices()
