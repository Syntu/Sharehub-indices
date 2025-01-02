import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Function to scrape live trading data
def scrape_live_trading():
    url = "https://www.sharesansar.com/live-trading"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            data.append({
                "Symbol": cells[1].text.strip(),
                "LTP": cells[2].text.strip().replace(",", ""),
                "Change%": cells[4].text.strip(),
                "Day High": cells[6].text.strip().replace(",", ""),
                "Day Low": cells[7].text.strip().replace(",", ""),
                "Previous Close": cells[9].text.strip().replace(",", ""),
                "Volume": cells[8].text.strip().replace(",", "")
            })
    return data

# Function to scrape today's share price summary
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            data.append({
                "SN": cells[0].text.strip(),
                "Symbol": cells[1].text.strip(),
                "Turnover": cells[10].text.strip().replace(",", ""),
                "52 Week High": cells[19].text.strip().replace(",", ""),
                "52 Week Low": cells[20].text.strip().replace(",", "")
            })
    return data

# Function to merge live and today's data
def merge_data(live_data, today_data):
    merged = []
    today_dict = {item["Symbol"]: item for item in today_data}

    for live in live_data:
        symbol = live["Symbol"]
        if symbol in today_dict:
            try:
                today = today_dict[symbol]
                high = float(today["52 Week High"]) if today["52 Week High"] != "N/A" else None
                low = float(today["52 Week Low"]) if today["52 Week Low"] != "N/A" else None
                ltp = float(live["LTP"]) if live["LTP"] != "N/A" else None

                down_from_high = (high - ltp) / high * 100 if high and ltp else "N/A"
                up_from_low = (ltp - low) / low * 100 if low and ltp else "N/A"

                merged.append({
                    "SN": today["SN"],
                    "Symbol": symbol,
                    "LTP": live["LTP"],
                    "Change%": live["Change%"],
                    "Day High": live["Day High"],
                    "Day Low": live["Day Low"],
                    "Previous Close": live["Previous Close"],
                    "Volume": live["Volume"],
                    "Turnover": today["Turnover"],
                    "52 Week High": today["52 Week High"],
                    "52 Week Low": today["52 Week Low"],
                    "Down From High (%)": f"{down_from_high:.2f}" if isinstance(down_from_high, float) else "N/A",
                    "Up From Low (%)": f"{up_from_low:.2f}" if isinstance(up_from_low, float) else "N/A"
                })
            except Exception as e:
                print(f"Error processing data for symbol {symbol}: {e}")
    return merged

# Function to fetch stock data by symbol
def fetch_stock_data_by_symbol(symbol):
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)

    for stock in merged_data:
        if stock["Symbol"] == symbol:
            return stock
    return None

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Welcome to Syntoo's NEPSE BOT\n"
        "कृपया स्टकको सिम्बोल दिनुहोस्।\n"
        "उदाहरण: SHINE, SCB, SWBBL, SHPC"
    )
    await update.message.reply_text(welcome_message)

# Default handler for stock symbol
async def handle_stock_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()
    data = fetch_stock_data_by_symbol(symbol)

    if data:
        response = (
            f"Stock Data for <b>{data['Symbol']}</b>:\n\n"
            f"LTP: {data['LTP']}\n"
            f"Change Percent: {data['Change%']}\n"
            f"Day High: {data['Day High']}\n"
            f"Day Low: {data['Day Low']}\n"
            f"52 Week High: {data['52 Week High']}\n"
            f"52 Week Low: {data['52 Week Low']}\n"
            f"Volume: {data['Volume']}\n"
            f"Turnover: {data['Turnover']}\n"
            f"Down From High: {data['Down From High (%)']}%\n"
            f"Up From Low: {data['Up From Low (%)']}%\n"
            f"Recommendation : {data['Please keep using my bot and share with your friends']}%"
        )
    else:
        response = f"""Symbol '{symbol}'\n\nल्या, फेला परेन त हौं।🤗🤗\nSymbol मिलेन कि कारोबार बन्द छ?\nफेरि कोसिस गर्नुस त।"""
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)

# Main function to set up the bot and run polling
if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_API_KEY")

    # Set up Telegram bot application
    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers to the application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stock_symbol))

    # Start polling
    print("Starting polling...")
    application.run_polling()
