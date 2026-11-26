import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from buttons import start_button
from inline_buttons import ovqatlar_button
from database import Base, engine
from register import r_router
from admin import a_router

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# kommandlar

@dp.message(Command('start'))
async def start_kommand(message: Message):
    xabar = "Welcome to my Bot"
    await message.answer(xabar, reply_markup=start_button())

@dp.message(F.text == "Ortga")
async def ortga_qaytish(message: Message):
    xabar = "Asosiy menuga qaytdingiz"
    await message.answer(xabar, reply_markup=start_button())

# Taomlar
@dp.message(F.text == "🍽 Taomlar")
async def taomlar_cmd(message: Message):
    xabar = "Marhamat Taomlar menusi"
    await message.answer(
        xabar, reply_markup=ovqatlar_button()
    )

import logging
from html import escape

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ChatMemberStatus

from database import (
    add_to_cart, get_cart, clear_cart,
    create_order, get_order, change_order_status
)
from inline_buttons import (
    savatcha_button, phone_button,
    location_button, admin_order_button
)

ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))


class OrderState(StatesGroup):
    phone = State()
    location = State()


# TAOMNI SAVATCHAGA QO'SHISH
@dp.callback_query(F.data.startswith("taom:"))
async def add_cart_handler(callback: CallbackQuery):
    if callback.message.chat.type != "private":
        await callback.answer()
        return

    taom_id = int(callback.data.split(":")[1])

    success = add_to_cart(callback.from_user.id, taom_id)

    await callback.answer(
        "✅ Savatchaga qo'shildi!" if success
        else "❌ Taom topilmadi!"
    )


# SAVATCHANI KO'RISH
@dp.message(F.text == "🛒 Savatcha")
async def cart_handler(message: Message):
    if message.chat.type != "private":
        return

    items = get_cart(message.from_user.id)

    if not items:
        await message.answer("🛒 Savatchangiz bo'sh.")
        return

    total = 0
    xabar = "🛒 <b>Savatchangiz:</b>\n\n"

    for item in items:
        summa = item["price"] * item["quantity"]
        total += summa

        xabar += (
            f"🍽 {escape(item['name'])}\n"
            f"{item['quantity']} × {item['price']:,} "
            f"= {summa:,} so'm\n\n"
        )

    xabar += f"💰 <b>Jami: {total:,} so'm</b>"

    await message.answer(
        xabar,
        parse_mode="HTML",
        reply_markup=savatcha_button()
    )


# SAVATCHANI TOZALASH
@dp.callback_query(F.data == "cart:clear")
async def clear_cart_handler(callback: CallbackQuery):
    if callback.message.chat.type != "private":
        await callback.answer()
        return

    clear_cart(callback.from_user.id)

    await callback.message.edit_text("❌ Savatcha tozalandi.")
    await callback.answer()


# BUYURTMANI RASMIYLASHTIRISH
@dp.callback_query(F.data == "cart:confirm")
async def confirm_cart(callback: CallbackQuery, state: FSMContext):
    if callback.message.chat.type != "private":
        await callback.answer()
        return

    if not get_cart(callback.from_user.id):
        await callback.answer("Savatcha bo'sh!", show_alert=True)
        return

    await state.set_state(OrderState.phone)

    await callback.message.answer(
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=phone_button()
    )
    await callback.answer()


# TELEFON RAQAM
@dp.message(OrderState.phone, F.contact)
async def receive_phone(message: Message, state: FSMContext):
    if message.contact.user_id != message.from_user.id:
        await message.answer("O'zingizning raqamingizni yuboring.")
        return

    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(OrderState.location)

    await message.answer(
        "📍 Yetkazib berish manzilini yuboring:",
        reply_markup=location_button()
    )


# LOKATSIYA VA BUYURTMA
@dp.message(OrderState.location, F.location)
async def receive_location(message: Message, state: FSMContext):
    data = await state.get_data()

    phone = data.get("phone")
    if not phone:
        await state.clear()
        await message.answer("Qaytadan buyurtma bering.")
        return

    order_id = create_order(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        phone=phone,
        latitude=message.location.latitude,
        longitude=message.location.longitude
    )

    await state.clear()

    if not order_id:
        await message.answer("Savatchangiz bo'sh.")
        return

    order = get_order(order_id)

    xabar = (
        f"🔔 <b>Yangi buyurtma #{order_id}</b>\n\n"
        f"👤 {escape(order['full_name'])}\n"
        f"🆔 {order['telegram_id']}\n"
        f"📱 {escape(order['phone'])}\n\n"
        "🍽 <b>Taomlar:</b>\n"
    )

    for item in order["items"]:
        xabar += (
            f"• {escape(item['name'])} — "
            f"{item['quantity']} × {item['price']:,} so'm\n"
        )

    xabar += (
        f"\n💰 <b>Jami: {order['total_price']:,} so'm</b>"
    )

    try:
        await bot.send_message(
            ADMIN_GROUP_ID,
            xabar,
            parse_mode="HTML",
            reply_markup=admin_order_button(order_id)
        )

        await bot.send_location(
            ADMIN_GROUP_ID,
            latitude=order["latitude"],
            longitude=order["longitude"]
        )

    except Exception:
        logging.exception("Admin guruhiga yuborishda xatolik")
        await message.answer(
            f"⚠️ Buyurtma #{order_id} saqlandi, "
            "lekin admin guruhiga yuborishda xatolik yuz berdi.",
            reply_markup=start_button()
        )
        return

    await message.answer(
        f"✅ Buyurtma #{order_id} yuborildi!\n"
        "Admin javobini kuting.",
        reply_markup=start_button()
    )


# FAQAT GURUH ADMINLARI UCHUN
async def is_group_admin(user_id):
    try:
        member = await bot.get_chat_member(
            ADMIN_GROUP_ID, user_id
        )
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        )
    except Exception:
        logging.exception("Admin tekshiruvida xatolik")
        return False


# ADMIN BUYURTMANI BOSHQARADI
@dp.callback_query(F.data.startswith("order:"))
async def manage_order(callback: CallbackQuery):
    if (
        not callback.message
        or callback.message.chat.id != ADMIN_GROUP_ID
    ):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    if not await is_group_admin(callback.from_user.id):
        await callback.answer("Siz admin emassiz!", show_alert=True)
        return

    _, action, order_id = callback.data.split(":")
    order_id = int(order_id)

    if action not in ("accept", "cancel"):
        await callback.answer("Noto'g'ri amal!")
        return

    status = "accepted" if action == "accept" else "cancelled"

    success = change_order_status(order_id, status)

    if not success:
        await callback.answer(
            "Bu buyurtma allaqachon ko'rib chiqilgan!",
            show_alert=True
        )
        return

    order = get_order(order_id)

    if action == "accept":
        status_text = "✅ QABUL QILINDI"
        user_text = (
            f"✅ Buyurtmangiz #{order_id} qabul qilindi!\n"
            "🍽 Buyurtmangiz tayyorlanmoqda."
        )
    else:
        status_text = "❌ BEKOR QILINDI"
        user_text = (
            f"❌ Buyurtmangiz #{order_id} "
            "admin tomonidan bekor qilindi."
        )

    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.reply(
        f"Buyurtma #{order_id}: {status_text}\n"
        f"👤 Admin: {escape(callback.from_user.full_name)}",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            order["telegram_id"],
            user_text
        )
    except Exception:
        logging.exception(
            "Mijozga xabar yuborilmadi: order=%s",
            order_id
        )

    await callback.answer(status_text)

async def main():
    Base.metadata.create_all(engine)

    dp.include_router(a_router)
    dp.include_router(r_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
