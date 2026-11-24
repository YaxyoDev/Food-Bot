from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext              # ketma ket malumot surash
from aiogram.fsm.state import State, StatesGroup        # malumotlarni vaqtincha saqlash uchun joy
from database import add_foydalanuvchi, get_one_user
from buttons import start_button

class Royxatdan_Otish_State(StatesGroup):
    telefon_raqam = State()
    rasm = State()

r_router = Router()

@r_router.message(F.text == "Ro'yxatdan o'tish")
async def royxatdan_otish_cmd(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = get_one_user(telegram_id)
    if user:
        xabar = "Siz oldin ro'yxatdan o'tgansiz!"
        return await message.answer(xabar, reply_markup=start_button())

    xabar = "Telefon raqam kiriting"
    await message.answer(xabar)
    await state.set_state(Royxatdan_Otish_State.telefon_raqam)

@r_router.message(Royxatdan_Otish_State.telefon_raqam)
async def telefon_saqlash_cmd(messsage: Message, state: FSMContext):
    telefon = messsage.text
    uzunligi = len(telefon)
    sonli_qism = telefon[1:]
    harf_tekshiruv = sonli_qism.isdigit()
    bosh_tekshiruv = telefon.startswith("+998")

    if uzunligi != 13 or harf_tekshiruv == False or bosh_tekshiruv == False:
        xabar = "Iltimos to'g'ri yozing."
        return await messsage.answer(xabar)

    await state.update_data(telefon_raqam=telefon)
    xabar = "Rasm yuboring"
    await messsage.answer(xabar)
    await state.set_state(Royxatdan_Otish_State.rasm)

@r_router.message(Royxatdan_Otish_State.rasm)
async def rasm_saqlash_cmd(message: Message, state: FSMContext):
    if not message.photo:
        xabar = "iltimos faqat rasm yuboring"
        return await message.answer(xabar)

    rasm = message.photo[-1].file_id
    await state.update_data(rasm=rasm)
    xabar = "Siz ro'yxatdan o'tdingiz!"
    await message.answer(xabar)

    malumotlar = await state.get_data()

    ism = message.from_user.full_name
    telefon_raqam = malumotlar.get("telefon_raqam")
    rasm = malumotlar.get("rasm")
    telegram_id = message.from_user.id
    username = message.from_user.username or "Yo'q"
    is_admin = False

    add_foydalanuvchi(ism, telefon_raqam, rasm, telegram_id, username, is_admin)
    await state.clear()
    
