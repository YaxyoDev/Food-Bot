from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from database import (
    get_one_user,
    change_admin_status,
    add_taom,
    taom_ochirish,
    get_all_taomlar
)
from inline_buttons import admin_button

a_router = Router()


class AdminState(StatesGroup):
    admin_add = State()
    admin_delete = State()
    taom_name = State()
    taom_price = State()
    taom_delete = State()


# ADMIN HUQUQINI TEKSHIRISH

def is_admin(telegram_id):
    user = get_one_user(telegram_id)
    return user is not None and user.is_admin


# ADMIN PANEL

@a_router.message(F.text == "/admin")
async def admin_cmd(message: Message, state: FSMContext):
    user = get_one_user(message.from_user.id)

    if not user:
        return await message.answer(
            "Siz hali ro'yxatdan o'tmagansiz!"
        )

    if not user.is_admin:
        return await message.answer("Siz admin emassiz!")

    await state.clear()

    await message.answer(
        "Salom Admin!",
        reply_markup=admin_button()
    )


# ADMIN QO'SHISH

@a_router.callback_query(F.data == "admin_add")
async def admin_add_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q!", show_alert=True)

    await callback.answer()
    await callback.message.answer("Telegram ID raqamini kiriting:")
    await state.set_state(AdminState.admin_add)


@a_router.message(AdminState.admin_add)
async def admin_add_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await state.clear()

    if not message.text or not message.text.isdigit():
        return await message.answer("Telegram ID raqam bo'lishi kerak!")

    telegram_id = int(message.text)
    user = get_one_user(telegram_id)

    if not user:
        return await message.answer("Foydalanuvchi topilmadi!")

    if user.is_admin:
        return await message.answer("Bu foydalanuvchi allaqachon admin!")

    change_admin_status(telegram_id, True)

    await state.clear()
    await message.answer(
        f"✅ {user.ism} admin qilindi!",
        reply_markup=admin_button()
    )


# ADMIN O'CHIRISH

@a_router.callback_query(F.data == "admin_delete")
async def admin_delete_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q!", show_alert=True)

    await callback.answer()
    await callback.message.answer("Admin Telegram ID raqamini kiriting:")
    await state.set_state(AdminState.admin_delete)


@a_router.message(AdminState.admin_delete)
async def admin_delete_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await state.clear()

    if not message.text or not message.text.isdigit():
        return await message.answer("Faqat raqam kiriting!")

    telegram_id = int(message.text)
    user = get_one_user(telegram_id)

    if not user:
        return await message.answer("Foydalanuvchi topilmadi!")

    if telegram_id == message.from_user.id:
        return await message.answer("O'zingizni adminlikdan o'chira olmaysiz!")

    if not user.is_admin:
        return await message.answer("Bu foydalanuvchi admin emas!")

    change_admin_status(telegram_id, False)

    await state.clear()
    await message.answer(
        f"✅ {user.ism} adminlikdan olindi!",
        reply_markup=admin_button()
    )


# TAOM QO'SHISH

@a_router.callback_query(F.data == "taom_add")
async def taom_add_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q!", show_alert=True)

    await callback.answer()
    await callback.message.answer("Taom nomini kiriting:")
    await state.set_state(AdminState.taom_name)


@a_router.message(AdminState.taom_name)
async def taom_name_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await state.clear()

    uzunligi = len(message.text)
    if uzunligi < 3:
        return await message.answer("Taom nomi qisqa yozildi iltimos uzunroq yozing")

    if not message.text or not message.text.strip():
        return await message.answer("Taom nomini matn ko'rinishida kiriting!")

    await state.update_data(name=message.text.strip())

    await message.answer("Taom narxini kiriting:")
    await state.set_state(AdminState.taom_price)


@a_router.message(AdminState.taom_price)
async def taom_price_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await state.clear()

    if not message.text or not message.text.isdigit():
        return await message.answer("Narx raqam bo'lishi kerak!")

    price = int(message.text)

    if price <= 0:
        return await message.answer("Narx 0 dan katta bo'lishi kerak!")

    data = await state.get_data()
    name = data["name"]

    add_taom(name, price)

    await state.clear()

    await message.answer(
        f"✅ Taom qo'shildi!\n\n"
        f"Nomi: {name}\n"
        f"Narxi: {price} so'm",
        reply_markup=admin_button()
    )


# TAOM O'CHIRISH

@a_router.callback_query(F.data == "taom_delete")
async def taom_delete_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Ruxsat yo'q!", show_alert=True)

    await callback.answer()

    taomlar = get_all_taomlar()

    if not taomlar:
        return await callback.message.answer("Taomlar mavjud emas!")

    xabar = "📋 Taomlar ro'yxati:\n\n"

    for taom in taomlar:
        xabar += f"{taom.id}. {taom.name} - {taom.price} so'm\n"

    xabar += "\nO'chirmoqchi bo'lgan taom ID raqamini kiriting:"

    await callback.message.answer(xabar)
    await state.set_state(AdminState.taom_delete)


@a_router.message(AdminState.taom_delete)
async def taom_delete_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await state.clear()

    if not message.text or not message.text.isdigit():
        return await message.answer("ID raqam bo'lishi kerak!")

    taom_id = int(message.text)

    taomlar = get_all_taomlar()

    if not any(taom.id == taom_id for taom in taomlar):
        return await message.answer("Taom topilmadi!")

    taom_ochirish(taom_id)

    await state.clear()
    await message.answer(
        "✅ Taom muvaffaqiyatli o'chirildi!",
        reply_markup=admin_button()
    )