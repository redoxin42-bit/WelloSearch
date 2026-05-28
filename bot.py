# bot.py
import asyncio
import random
import string
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command

import config
import database as db
import keyboards as kb

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Функция симуляции поиска коротких юзернеймов (5-6 символов)
def generate_mock_username():
    length = random.choice([5, 6])
    letters = string.ascii_lowercase
    # Можно разбавить цифрами или нижним подчеркиванием
    pool = letters + "0123456789_"
    
    # Первая буква всегда должна быть символом по правилам TG
    username = random.choice(letters) + "".join(random.choice(pool) for _ in range(length - 1))
    
    # Шанс "успешного" улова (например, 40%)
    is_caught = random.random() < 0.4
    estimated_price = random.randint(150, 1200) if is_caught else 0
    
    return username, is_caught, estimated_price


# --- ХЕНДЛЕРЫ ---

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    db.register_user(user_id, message.from_user.username or "Unknown")
    
    user = db.get_user(user_id)
    
    # Если источник еще не выбран (новый пользователь)
    if user[2] == 'none':
        await message.answer(
            "👋 Привет! Откуда вы пришли в нашего бота?",
            reply_markup=kb.get_source_keyboard()
        )
    else:
        db.check_and_reset_daily_limit(user_id)
        await message.answer(
            "🌟 *Wello Searcher*\n\nПоиск дорогих и коротких юзернеймов.",
            parse_mode="Markdown",
            reply_markup=kb.get_main_menu_keyboard()
        )

@router.callback_query(F.data.startswith("src_"))
async def handle_source_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    source = callback.data.split("_")[1]
    
    # Распределение стартовых бонусов
    initial_searches = 3 if source == "tiktok" else 2
    db.set_user_source(user_id, source, initial_searches)
    
    await callback.answer(f"Выбрано! Начислено {initial_searches} поиска(ов).")
    await callback.message.edit_text(
        "🌟 *Wello Searcher*\n\nПоиск дорогих и коротких юзернеймов.",
        parse_mode="Markdown",
        reply_markup=kb.get_main_menu_keyboard()
    )

@router.callback_query(F.data == "back_to_menu")
async def handle_back_to_menu(callback: CallbackQuery):
    db.check_and_reset_daily_limit(callback.from_user.id)
    await callback.message.edit_text(
        "🌟 *Wello Searcher*\n\nПоиск дорогих и коротких юзернеймов.",
        parse_mode="Markdown",
        reply_markup=kb.get_main_menu_keyboard()
    )

@router.callback_query(F.data == "menu_profile")
async def handle_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    db.check_and_reset_daily_limit(user_id)
    
    user = db.get_user(user_id)
    catches = db.get_user_catches(user_id)
    
    searches_left = user[3]
    is_premium = "Активна ⭐" if user[5] == 1 else "Нет ❌"
    
    # Считаем статистику уловов
    total_catches = len(catches)
    total_value = sum(item[1] for item in catches)
    
    # Формируем список последних уловов (до 5 штук)
    catches_text = ""
    if catches:
        for c in catches[:5]:
            catches_text += f"• `@{c[0]}` (~{c[1]} Stars)\n"
    else:
        catches_text = "Пока ничего не поймано."

    profile_msg = (
        f"👤 *Мой профиль Wello Searcher*\n\n"
        f"▪️ Подписка: {is_premium}\n"
        f"▪️ Доступно поисков на сегодня: *{searches_left}*\n\n"
        f"📊 *Статистика:*\n"
        f"▪️ Всего поймано юзеров: {total_catches}\n"
        f"▪️ Примерная ценность: {total_value} Stars\n\n"
        f"🎣 *Последние уловы:*\n{catches_text}"
    )
    
    await callback.message.edit_text(
        profile_msg,
        parse_mode="Markdown",
        reply_markup=kb.get_back_to_menu_keyboard()
    )

@router.callback_query(F.data == "menu_search")
async def handle_search(callback: CallbackQuery):
    user_id = callback.from_user.id
    db.check_and_reset_daily_limit(user_id)
    
    user = db.get_user(user_id)
    searches_left = user[3]
    is_premium = user[5]
    
    # Проверка лимитов (если не премиум и поиски кончились)
    if searches_left <= 0 and is_premium == 0:
        await callback.answer("❌ У вас закончились поиски на сегодня! Обновление каждый день, либо купите подписку.", show_alert=True)
        return

    # Списываем поиск (если премиум, можно не списывать или списывать из расширенного лимита)
    db.deduct_search(user_id)
    
    await callback.message.edit_text("🔄 Сканируем свободные адреса Telegram Telegram... Ожидайте.")
    await asyncio.sleep(1.5) # Небольшой визуальный таймаут для эффекта работы
    
    username, is_caught, price = generate_mock_username()
    
    if is_caught:
        db.add_catch(user_id, username, price)
        result_text = (
            f"🎉 *Успешный улов!*\n\n"
            f"🔗 Юзернейм: `@{username}`\n"
            f"📏 Длина: {len(username)} символов\n"
            f"💰 Примерная стоимость: *{price}* Telegram Stars\n\n"
            f"Юзернейм сохранен в ваш профиль!"
        )
    else:
        result_text = (
            f"🔍 *Поиск завершен*\n\n"
            f"Проверен адрес: `@{username}`\n"
            f"Статус: Занят или не представляет ценности.\n\n"
            f"Попробуйте еще раз!"
        )
        
    await callback.message.edit_text(
        result_text,
        parse_mode="Markdown",
        reply_markup=kb.get_main_menu_keyboard()
    )

# --- ПЛАТЕЖНАЯ СИСТЕМА (TELEGRAM STARS) ---

@router.callback_query(F.data == "menu_buy_premium")
async def process_buy_premium(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if user[5] == 1:
        await callback.answer("У вас уже есть активная Premium подписка! ✨", show_alert=True)
        return

    # Выставляем инвойс на Telegram Stars
    # Валюта для звезд ВСЕГДА "XTR", а провайдер-токен оставляем пустым ""
    prices = [LabeledPrice(label="Wello Searcher Premium", amount=config.PREMIUM_PRICE_STARS)]
    
    await callback.message.answer_invoice(
        title="Wello Searcher Premium подписка",
        description="Получите доступ к увеличенному числу ежедневных поисков и повышенному шансу на редкие юзернеймы!",
        payload="premium_subscription_payload",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="premium-buy"
    )
    await callback.answer()

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Одобряем платеж
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user_id = message.from_user.id
    db.activate_premium(user_id)
    
    await message.answer(
        "🎉 *Спасибо за покупку!*\n\nВаша Premium-подписка успешно активирована. Теперь лимиты увеличены, а поиск стал ещё эффективнее!",
        parse_mode="Markdown"
    )

# --- ЗАПУСК БОТА ---

async def main():
    db.init_db() # Инициализируем БД при старте
    dp.include_router(router)
    print("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
