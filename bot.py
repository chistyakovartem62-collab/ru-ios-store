import asyncio
import json
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import LabeledPrice

# Получаем токен из переменных окружения на Render (или подставьте строкой)
TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в **RU iOS Store**!\n\n"
        "Откройте каталог приложений через кнопку ниже, выберите нужные и оформите заказ в несколько кликов.",
        parse_mode="Markdown"
    )

# Обработка данных, поступающих при нажатии кнопки «Купить» в Mini App
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        if data.get("action") == "buy_apps":
            apps_list = data.get("apps", [])
            stars_price = data.get("stars", 10)
            
            apps_str = ", ".join(apps_list)
            
            # Формируем цену в Telegram Stars (валюта "XTR")
            prices = [LabeledPrice(label=f"Приложения: {apps_str}", amount=stars_price)]
            
            # Отправляем инвойс на оплату Stars
            await message.bot.send_invoice(
                chat_id=message.chat.id,
                title="Оплата доступа к приложениям",
                description=f"Вы выбрали: {apps_str}. Нажмите кнопку ниже для оплаты.",
                payload="ios_store_apps_order",
                currency="XTR",  # Код валюты Telegram Stars
                prices=prices,
                provider_token="" # Для Telegram Stars поле провайдера оставляем пустым!
            )
    except Exception as e:
        logging.error(f"Ошибка обработки заказа: {e}")
        await message.answer("Произошла ошибка при формировании заказа. Попробуйте еще раз.")

# Обязательный этап предварительной проверки платежа перед списанием звезд
@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# Успешная оплата: пользователь подтвердил списание Stars
@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    payment_info = message.successful_payment
    
    await message.answer(
        "🎉 **Оплата успешно прошла!**\n\n"
        f"Списано: {payment_info.total_amount} Telegram Stars ⭐️\n\n"
        "Благодарим за покупку! Вот ваши ссылки и инструкции для установки приложений:\n"
        "👉 [Открыть инструкции и ссылки на скачивание](https://t.me/your_channel_or_bot)\n\n"
        "Если у вас возникли вопросы, обратитесь в поддержку.",
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


