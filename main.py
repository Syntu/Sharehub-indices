import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Function to fetch stock data
def fetch_stock_data_by_symbol(symbol):
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Error: Unable to fetch data from Sharesansar. Status code:", response.status_code)
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')
    if not table:
        print("Error: No table found in the response.")
        return None
    
    rows = table.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('td')
        row_symbol = cols[1].text.strip()

        if row_symbol.upper() == symbol.upper():
            day_high = cols[4].text.strip()
            day_low = cols[5].text.strip()
            closing_price = cols[6].text.strip()
            change_percent = cols[14].text.strip()
            volume = cols[8].text.strip()
            turnover = cols[10].text.strip()
            week_52_high = cols[19].text.strip()
            week_52_low = cols[20].text.strip()

            # Calculating Down From High and Up From Low
            try:
                down_from_high = (
                    (float(week_52_high) - float(closing_price)) / float(week_52_high) * 100
                )
                up_from_low = (
                    (float(closing_price) - float(week_52_low)) / float(week_52_low) * 100
                )
            except ValueError:
                down_from_high = "N/A"
                up_from_low = "N/A"

            return {
                'Symbol': symbol,
                'Day High': day_high,
                'Day Low': day_low,
                'LTP': closing_price,
                'Change Percent': change_percent,
                'Volume': volume,
                'Turnover': turnover,
                '52 Week High': week_52_high,
                '52 Week Low': week_52_low,
                'Down From High': f"{down_from_high:.2f}%" if isinstance(down_from_high, float) else down_from_high,
                'Up From Low': f"{up_from_low:.2f}%" if isinstance(up_from_low, float) else up_from_low
            }
    return None

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Welcome to Syntu's NEPSE BOT\n"
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
            f"Change Percent: {data['Change Percent']}\n"
            f"Day High: {data['Day High']}\n"
            f"Day Low: {data['Day Low']}\n"
            f"52 Week High: {data['52 Week High']}\n"
            f"52 Week Low: {data['52 Week Low']}\n"
            f"Volume: {data['Volume']}\n"
            f"Turnover: {data['Turnover']}\n"
            f"Down From High: {data['Down From High']}\n"
            f"Up From Low: {data['Up From Low']}\n"
        )
    else:
        response = f"""Symbol '{symbol}' फेला परेन। कृपया सही सिम्बोल दिनुहोस्।"""
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
