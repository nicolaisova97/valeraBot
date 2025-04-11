import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

API_TOKEN = '7686941028:AAHm7uILztAuUq4Zd51AtzNkqGnEQasehbU'
ADMIN_ID = 123456789  # Замените на свой Telegram ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Состояния
class Booking(StatesGroup):
    master = State()
    service = State()
    datetime = State()
    name = State()
    phone = State()

# Данные
masters = ["Максим", "Игорь", "Сергей"]
services = [
    "Стрижка бровей",
    "Мытье головы шампунем и кондиционирование",
    "Детские стрижки",
    "Стрижка бритвой",
    "Мужская эпиляция",
    "Стрижка длинных волос",
    "Стрижка ножницами",
    "Стрижка машинкой",
    "Уход за бородой",
    "Бритье",
    "Эпиляция воском",
    "Коррекция бороды"
]

# Старт
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    for m in masters:
        keyboard.add(InlineKeyboardButton(text=m, callback_data=f"master_{m}"))
    await message.answer("Привет! Выбери мастера:", reply_markup=keyboard)
    await Booking.master.set()

# Выбор мастера
@dp.callback_query_handler(Text(startswith="master_"), state=Booking.master)
async def select_master(call: types.CallbackQuery, state: FSMContext):
    master = call.data.split("_", 1)[1]
    await state.update_data(master=master)

    keyboard = InlineKeyboardMarkup()
    for s in services:
        keyboard.add(InlineKeyboardButton(text=s, callback_data=f"service_{s}"))
    await call.message.edit_text("Отлично! Теперь выбери услугу:", reply_markup=keyboard)
    await Booking.next()

# Выбор услуги
@dp.callback_query_handler(Text(startswith="service_"), state=Booking.service)
async def select_service(call: types.CallbackQuery, state: FSMContext):
    service = call.data.split("_", 1)[1]
    await state.update_data(service=service)
    await call.message.edit_text("Укажи желаемую дату и время (например: 13 апреля, 15:00)")
    await Booking.next()

# Дата и время
@dp.message_handler(state=Booking.datetime)
async def input_datetime(message: types.Message, state: FSMContext):
    await state.update_data(datetime=message.text)
    await message.answer("Как вас зовут?")
    await Booking.next()

# Имя
@dp.message_handler(state=Booking.name)
async def input_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Укажите номер телефона:")
    await Booking.next()

# Телефон и финал
@dp.message_handler(state=Booking.phone)
async def input_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()

    # Отправка админу
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Подтвердить", callback_data="confirm_yes"),
        InlineKeyboardButton("Отклонить", callback_data="confirm_no")
    )
    text = (
        f"\u2709\ufe0f Новая заявка:\n"
        f"Мастер: {data['master']}\n"
        f"Услуга: {data['service']}\n"
        f"Дата и время: {data['datetime']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}"
    )
    await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
    await message.answer("Заявка отправлена! Мы свяжемся с вами после подтверждения.")
    await state.finish()

# Ответ от админа
@dp.callback_query_handler(Text(startswith="confirm_"))
async def confirm_booking(call: types.CallbackQuery):
    action = call.data.split("_")[1]
    text = "\u2705 Запись подтверждена!" if action == "yes" else "\u274C Запись отклонена."
    await call.message.reply(text)
    await call.message.edit_reply_markup()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
