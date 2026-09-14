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
# Токен должен быть в кавычках. ID — просто число без кавычек.

BOT_TOKEN = "8814618059:AAGiF1lmuKemOUpoQhpDWaliWcFOY7cFwng"  # Пример: "1234567890:ABCdefGhIJKlmNoPQRsT"
ADMIN_ID = 5602074020         # Пример: 583920193
# =====================================================================

# Проверка на дурака: не забыл ли пользователь поменять заглушки
if BOT_TOKEN == "ВАШ_ТОКЕН_БОТА" or ADMIN_ID == 123456789:
    print("\n❌ ОШИБКА: Вы забыли заменить 'ВАШ_ТОКЕН_БОТА' или 'ADMIN_ID' на свои реальные данные!")
    print("Откройте файл main.py в блокноте и вставьте туда токен от @BotFather и ваш ID.\n")
    sys.exit(1)

try:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
except Exception as e:
    print(f"\n❌ ОШИБКА: Не удалось запустить бота с вашим токеном. Проверьте его корректность.")
    print(f"Текст ошибки: {e}\n")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)

class OrderForm(StatesGroup):
    waiting_for_type = State()       
    waiting_for_details = State()    
    waiting_for_reference = State()  

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎨 Заказать рисовку")],
            [KeyboardButton(text="📋 Прайс / Примеры")]
        ],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Я бот для заказа рисунков и иллюстраций.\n"
        "Нажми на кнопку ниже, чтобы оформить заказ.",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📋 Прайс / Примеры")
async def show_price(message: Message):
    price_text = (
        "💰 **Наш прайс-лист:**\n"
        "— Иташи: от 1000 руб.\n"
        "— Тимки под ключ: от 1500 руб.\n"
        "— Флеймы: 500 руб.\n\n"
    )
    await message.answer(price_text, parse_mode="Markdown")

@dp.message(F.text == "🎨 Заказать рисовку")
async def start_order(message: Message, state: FSMContext):
    type_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Иташи"), KeyboardButton(text="Тимка")],
            [KeyboardButton(text="Флейм"), KeyboardButton(text="Другое")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите тип работы, который вас интересует:", reply_markup=type_kb)
    await state.set_state(OrderForm.waiting_for_type)

@dp.message(OrderForm.waiting_for_type)
async def process_type(message: Message, state: FSMContext):
    await state.update_data(work_type=message.text)
    await message.answer(
        "Отлично! Теперь подробно опишите ваше ТЗ :\n"
        "— Что должно быть изображено?\n"
        "— В каких цветах и каком стиле?\n"
        "— Персонажи, фон, важные детали?",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True)
    )
    await state.set_state(OrderForm.waiting_for_details)

@dp.message(OrderForm.waiting_for_details)
async def process_details(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await state.clear()
        await message.answer("Заказ отменен.", reply_markup=get_main_keyboard())
        return
        
    await state.update_data(details=message.text)
    await message.answer(
        "Прикрепите референсы (картинки, фото), если они есть.\n"
        "Если референсов нет, просто напишите текст 'Нет референсов'."
    )
    await state.set_state(OrderForm.waiting_for_reference)

@dp.message(OrderForm.waiting_for_reference)
async def process_reference(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    client_info = f"👤 **Новый заказ!**\n" \
                  f"От: @{message.from_user.username or 'нет_юзернейма'} (ID: {message.from_user.id})\n" \
                  f"Имя: {message.from_user.full_name}\n\n" \
                  f"📦 **Тип работы:** {user_data['work_type']}\n" \
                  f"📝 **ТЗ:** {user_data['details']}\n"

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=client_info, parse_mode="Markdown")
        
        if message.photo:
            await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption="🖼 Референс от клиента")
        elif message.document:
            await bot.send_document(chat_id=ADMIN_ID, document=message.document.file_id, caption="📄 Файл-референс от клиента")
        elif message.text and message.text.lower() != "нет референсов":
            await bot.send_message(chat_id=ADMIN_ID, text=f"💬 Доп. комментарий к рефам: {message.text}")
    except Exception as e:
        print(f"\n❌ ОШИБКА ПРИ ОТПРАВКЕ АДМИНУ: Возможно, вы указали неверный ADMIN_ID или вы сами еще не запустили созданного бота. Напишите вашему боту /start в Telegram.")
        print(f"Текст ошибки: {e}\n")

    await state.clear()
    await message.answer(
        "✨ Спасибо! Ваш заказ успешно оформлен и отправлен художнику. "
        "Мы свяжемся с вами в ближайшее время для уточнения деталей и оплаты.",
        reply_markup=get_main_keyboard()
    )

async def main():
    print("\n🚀 Бот успешно запускается... Если ошибок ниже нет, значит он онлайн!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Бот остановлен.")
