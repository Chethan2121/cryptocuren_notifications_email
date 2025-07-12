import os
import requests
import smtplib
import csv
from datetime import datetime
from email.message import EmailMessage
import matplotlib.pyplot as plt

# --------------------------
# Read from GitHub Secrets
# --------------------------
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
TO_EMAIL = os.environ.get('TO_EMAIL')

# --------------------------
# Crypto Watchlist (you can add more)
# --------------------------
CRYPTO_WATCHLIST = [
    'bitcoin',
    'ethereum',
    'dogecoin',
    'worldcoin',
    'cardano',
    'solana',
    'polkadot'
]

# --------------------------
# Fetch Crypto Data from CoinGecko
# --------------------------
def get_crypto_data(coin):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}?localization=false&tickers=false&market_data=true"
    try:
        response = requests.get(url)
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
        print(f"❌ Error fetching data for {coin}: {e}")
        return None, {}

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
# Generate Bar Chart of Prices
# --------------------------
def generate_chart(prices):
    coins = [p['coin'].upper() for p in prices]
    values = [p['price'] for p in prices]

    plt.figure(figsize=(10, 5))
    plt.bar(coins, values, color='orange')
    plt.title("Current INR Prices of Cryptocurrencies")
    plt.xlabel("Cryptocurrency")
    plt.ylabel("Price in INR")
    plt.tight_layout()
    chart_path = "price_chart.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path

# --------------------------
# Send Email with Chart Attachment
# --------------------------
def send_summary_email(content, chart_path):
    msg = EmailMessage()
    msg['Subject'] = "📊 INR Crypto Prices + Chart & History"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg.set_content(content)

    # Attach the chart image
    with open(chart_path, 'rb') as img:
        msg.add_attachment(img.read(), maintype='image', subtype='png', filename='price_chart.png')

    # Send via Gmail SMTP
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print("✅ Email sent with chart successfully.")

# --------------------------
# Main Execution
# --------------------------
def generate_report():
    summary = "📈 INR Crypto Price Report + Profit/Loss Summary\n\n"
    log_data = []
    chart_prices = []

    for coin in CRYPTO_WATCHLIST:
        price, changes = get_crypto_data(coin)
        if price is None:
            continue

        summary += f"{coin.upper()} - ₹{price:,.2f}\n"
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), coin.upper(), price]

        for interval in ['1h', '24h', '7d', '14d', '30d']:
            change = changes.get(interval)
            if change is not None:
                summary += f"  • {interval}: {change:.2f}%\n"
                row.append(change)
            else:
                summary += f"  • {interval}: ❌ Not available\n"
                row.append("N/A")

        summary += "\n"
        log_data.append(row)
        chart_prices.append({'coin': coin, 'price': price})

    # Log to CSV and generate chart
    log_to_csv(log_data)
    chart_path = generate_chart(chart_prices)
    send_summary_email(summary, chart_path)

if __name__ == '__main__':
    generate_report()
