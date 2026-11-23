import os, asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
TOKEN=os.getenv("BOT_TOKEN","")
WEBAPP_URL=os.getenv("WEBAPP_URL","")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=("Добро пожаловать в RU iOS Store 🇷🇺\n\n"
          "Каталог приложений для iPhone. Выбирайте приложение и переходите "
          "на официальный сайт или доступную страницу установки.\n\n"
          "Важно: доступность приложений зависит от региона Apple ID и правил разработчика.")
    if WEBAPP_URL.startswith("https://"):
        keyboard=[[InlineKeyboardButton("Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL))]]
    else:
        keyboard=[[InlineKeyboardButton("Открыть каталог", url="https://t.me/")]]
        text += "\n\nКаталог ещё не опубликован. Администратор должен указать WEBAPP_URL."
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    if not TOKEN:
        raise SystemExit("Укажите BOT_TOKEN в .env")
    application=Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start",start))
    application.run_polling()

if __name__=="__main__":
    main()
