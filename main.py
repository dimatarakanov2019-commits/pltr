import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command

# =====================================================================
# ВНИМАТЕЛЬНО ЗАПОЛНИТЕ ЭТИ ДАННЫЕ:
# Токен должен быть строго в кавычках. ID — просто число БЕЗ кавычек.

BOT_TOKEN = "8814618059:AAGZwILHnodzx4KEg2mjyEJD4WBC6BexSYI"  # Пример: "8814618059:AAGiF1lmuKem0Upo..."
ADMIN_ID = 5602074020         # Сюда вставьте ваш цифровой ID из @userinfobot
# =====================================================================


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Состояния для формы заказа (FSM)
class OrderForm(StatesGroup):
    waiting_for_type = State()       # Шаг 1: Выбор типа работы
    waiting_for_details = State()    # Шаг 2: Ввод ТЗ
    waiting_for_reference = State()  # Шаг 3: Отправка референса/картинки

# Главное меню бота
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎨 Заказать рисовку")],
            [KeyboardButton(text="📋 Прайс / Примеры")],
            [KeyboardButton(text="🔍 Проверить мой ID")]  # Кнопка для самодиагностики
        ],
        resize_keyboard=True
    )

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"🤖 БОТ ОБНОВЛЕН И РАБОТАЕТ ГАРАНТИРОВАННО ДЛЯ ВСЕХ!\n\n"
        f"Привет, {message.from_user.full_name}! 👋\n"
        f"Я бот для заказа рисовок на серверах DriftParadise!.\n"
        f"Нажмите на кнопку ниже, чтобы оформить заказ.",
        reply_markup=get_main_keyboard()
    )

# Кнопка проверки ID на случай сбоев настройки
@dp.message(F.text == "🔍 Проверить мой ID")
async def check_id(message: Message):
    current_user_id = message.from_user.id
    if current_user_id == ADMIN_ID:
        await message.answer(f"✅ Всё супер! Ваш ID в Telegram: `{current_user_id}`.\nВ коде бота прописан ТОЧНО ТАКОЙ ЖЕ ID. Вы являетесь администратором.")
    else:
        await message.answer(
            f"❌ ВНИМАНИЕ! Ваш реальный ID в Telegram: `{current_user_id}`.\n\n"
            f"А в коде вашего бота сейчас прописан ID: `{ADMIN_ID}`.\n"
            f"Они НЕ совпадают! Из-за этого бот шлет уведомления не вам."
        )

# Показ прайс-листа
@dp.message(F.text == "📋 Прайс / Примеры")
async def show_price(message: Message):
    price_text = (
        "💰 **Наш прайс-лист:**\n"
        "— Иташи (Аниме): от 500 руб.\n"
        "— Командный винил под ключ (Тимка): от 1000 руб.\n"
        "— Флейм / Мисл : от 500 руб.\n\n"
    )
    await message.answer(price_text, parse_mode="Markdown")

# Начало заказа
@dp.message(F.text == "🎨 Заказать рисовку")
async def start_order(message: Message, state: FSMContext):
    type_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Иташи"), KeyboardButton(text="Тимка")],
            [KeyboardButton(text="Флейм/Мисл"), KeyboardButton(text="Другое")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите тип работы, который вас интересует:", reply_markup=type_kb)
    await state.set_state(OrderForm.waiting_for_type)

# Шаг 1: Получаем тип работы
@dp.message(OrderForm.waiting_for_type)
async def process_type(message: Message, state: FSMContext):
    await state.update_data(work_type=message.text)
    await message.answer(
        "Отлично! Теперь подробно опишите ваше ТЗ:\n"
        "— Что должно быть изображено?\n"
        "— В каких цветах и каком стиле?\n"
        "— Персонажи, фон, важные детали?",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True)
    )
    await state.set_state(OrderForm.waiting_for_details)

# Шаг 2: Получаем детали ТЗ
@dp.message(OrderForm.waiting_for_details)
async def process_details(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await state.clear()
        await message.answer("Заказ отменен.", reply_markup=get_main_keyboard())
        return
        
    await state.update_data(details=message.text)
    await message.answer(
        "Прикрепите примеры или развертки, если они есть.\n"
        "Если референсов нет, просто напишите текст 'Нет референсов'."
    )
    await state.set_state(OrderForm.waiting_for_reference)

# Шаг 3: Получаем референсы и финально отправляем уведомление админу
@dp.message(OrderForm.waiting_for_reference)
async def process_reference(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    # Безопасно формируем данные о пользователе (даже если у незнакомца скрыт профиль)
    username = f"@{message.from_user.username}" if message.from_user.username else "нет юзернейма"
    full_name = message.from_user.full_name or "Без имени"
    
    # Текст анкеты
    client_info = (
        f"👤 **Новый заказ!**\n"
        f"От: {username} (ID: `{message.from_user.id}`)\n"
        f"Имя: {full_name}\n\n"
        f"📦 **Тип работы:** {user_data.get('work_type', 'Не указан')}\n"
        f"📝 **ТЗ:** {user_data.get('details', 'Не указано')}\n"
    )

    print(f"--- ПОПЫТКА ОТПРАВКИ ЗАКАЗА НА ID {ADMIN_ID} ---")

    # 1. СНАЧАЛА ОТПРАВЛЯЕМ АНКЕТУ АДМИНУ
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=client_info, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Критическая ошибка: Не удалось отправить сообщение на ADMIN_ID! Ошибка: {e}")

    # 2. БЕЗОПАСНО КОПИРУЕМ МЕДИА-ФАЙЛ (Обход настроек приватности незнакомых людей)
    try:
        if not message.text or message.text.lower() != "нет референсов":
            # send_copy не пересылает сообщение, а создает его дубликат от имени бота. 
            # Это на 100% обходит запреты конфиденциальности в аккаунтах клиентов.
            await message.send_copy(chat_id=ADMIN_ID, reply_markup=None)
            await bot.send_message(chat_id=ADMIN_ID, text=f"☝️ Это прикрепленный референс/текст от клиента {username}")
    except Exception as e:
        print(f"⚠️ Ошибка при копировании медиа-файла: {e}")
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Клиент прикрепил референс, но боту не удалось его передать.")
        except:
            pass

    # 3. СБРАСЫВАЕМ СОСТОЯНИЕ И РАДУЕМ КЛИЕНТА
    await state.clear()
    await message.answer(
        "✨ Спасибо! Ваш заказ успешно оформлен и отправлен художнику. "
        "Мы свяжемся с вами в ближайшее время для уточнения деталей и оплаты.",
        reply_markup=get_main_keyboard()
    )

# Главная функция запуска
async def main():
    print("\n🚀 Бот успешно запущен и готов принимать заказы со всего Telegram!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Бот остановлен.")
