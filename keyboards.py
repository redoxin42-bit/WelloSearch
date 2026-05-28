# keyboards.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_source_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора источника при первом входе"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 TikTok (+3 поиска)", callback_data="src_tiktok")
    builder.button(text="📢 Telegram (+2 поиска)", callback_data="src_telegram")
    builder.adjust(1)
    return builder.as_markup()

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота Wello Searcher"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Начать поиск", callback_data="menu_search")
    builder.button(text="👤 Мой профиль", callback_data="menu_profile")
    builder.button(text="⭐ Купить подписку", callback_data="menu_buy_premium")
    builder.adjust(1)
    return builder.as_markup()

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В меню", callback_data="back_to_menu")
    return builder.as_markup()
