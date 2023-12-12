from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Command
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import ChatNotFound

API_TOKEN = "TOKEN"
Admin = "ID"  # Replace with the actual user ID of the admin

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


class Form(StatesGroup):
    user_id = State()
    info = State()
    contact = State()
    answer = State()


class AdminAnswerState(StatesGroup):
    user_id = State()


@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await message.reply("Salom botga hush kelipsiz. Yordam kerak bo'lsa /help ni bosing")


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await message.reply("Muammoni kiriting:")
    await Form.info.set()
    await state.update_data(user_id=user_id)


@dp.message_handler(state=Form.info)
async def handle_info(message: types.Message, state: FSMContext):
    info_data = message.text

    await state.update_data(info=info_data)
    await Form.contact.set()
    await message.reply("Kontakt")


@dp.message_handler(state=Form.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    contact_data = message.text

    async with state.proxy() as data:
        data['contact'] = contact_data
        data['user_id'] = message.from_user.id
        data['user_name'] = message.from_user.full_name

    # Create a custom keyboard for the admin response
    keyword = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton('Javob Yozish', callback_data="send_answer"),
                types.InlineKeyboardButton('Bekor qilish', callback_data="cancel_answer")
            ]
        ],
    )

    await bot.send_message(
        chat_id=Admin,
        text=f"User_id: {data['user_id']}\n"
             f"Ism: {data['user_name']}\n"
             f"Matn: {data['info']}\n"
             f"Kontakt: {data['contact']}\n"
             f"Admin, javobingizni yozing:",
        reply_markup=keyword
    )

    await AdminAnswerState.user_id.set()


@dp.callback_query_handler(lambda call: call.data == "send_answer", state=AdminAnswerState.user_id)
async def get_user_id(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Javobni yozing")
    await Form.answer.set()  # Set the next state to collect the admin's answer


@dp.message_handler(state=Form.answer)
async def get_admin_answer(message: types.Message, state: FSMContext):
    answer = message.text
    user_data = await state.get_data()
    user_id = user_data.get('user_id')

    if user_id:
        # Sending the answer to the user who initiated the request
        await bot.send_message(chat_id=user_id, text=f"Admindan javob keldi:\n{answer}")
        await message.answer("Javob yuborildi")
    else:
        await message.answer("Error: User ID not found in state data.")

    await state.finish()


@dp.callback_query_handler(lambda call: call.data == "cancel_answer", state=AdminAnswerState.user_id)
async def cancel_admin_answer(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Javob bekor qilindi.")
    await state.finish()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
