import asyncio
import json
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import LabeledPrice

# Вставьте сюда токен вашего бота, полученный от @BotFather
TOKEN = "ВАШ_ТОКЕН_БОТА"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в **RU iOS Store**!\n\n"
        "Откройте каталог приложений через кнопку ниже, выберите нужные и оформите заказ в несколько кликов.",
        parse_mode="Markdown"
    )

# Обработчик данных, пришедших из Mini App (когда пользователь нажал «Купить»)
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        if data.get("action") == "buy_apps":
            apps_list = data.get("apps", [])
            stars_price = data.get("stars", 10)
            
            apps_str = ", ".join(apps_list)
            
            # Цены для Telegram Stars (валюта "XTR")
            # amount указывает количество звезд (число целое)
            prices = [LabeledPrice(label=f"Приложения: {apps_str}", amount=stars_price)]
            
            # Отправляем официальный инвойс на оплату Telegram Stars
            await message.bot.send_invoice(
                chat_id=message.chat.id,
                title="Оплата доступа к приложениям",
                description=f"Вы выбрали: {apps_str}. Нажмите кнопку ниже для оплаты.",
                payload="ios_store_apps_order",
                currency="XTR",  # Специальный код валюты для Telegram Stars
                prices=prices,
                provider_token="" # Для Telegram Stars провайдер токен всегда пустой!
            )
    except Exception as e:
        logging.error(f"Ошибка обработки заказа: {e}")
        await message.answer("Произошла ошибка при формировании заказа. Попробуйте еще раз.")

# 1. Обязательный этап проверки перед покупкой (Pre-checkout)
@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    # Подтверждаем готовность принять платеж
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# 2. Успешная оплата (Покупатель оплатил счет)
@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    payment_info = message.successful_payment
    
    # Здесь бот успешно получил Telegram Stars (оплата прошла)
    await message.answer(
        "🎉 **Оплата успешно прошла!**\n\n"
        f"Сумма платежа: {payment_info.total_amount} Telegram Stars ⭐️\n\n"
        "Благодарим за покупку! Вот ваши ссылки и инструкции для установки приложений:\n"
        "👉 [Открыть инструкции и ссылки на скачивание](https://t.me/your_channel_or_bot)\n\n"
        "Если у вас возникли вопросы, обратитесь в поддержку.",
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    # Запуск бота в режиме polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

