from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_all_taomlar

def ovqatlar_button():
    tugma = InlineKeyboardBuilder()
    taomlar = get_all_taomlar()
    for i in taomlar:
        tugma.button(
            text=i.name,
            callback_data=f"taom:{i.id}"
        )
    tugma.adjust(1)
    return tugma.as_markup()

def admin_button():
    tugma = InlineKeyboardBuilder()

    tugma.button(
        text="➕ Admin qo'shish",
        callback_data="admin_add"
    )
    tugma.button(
        text="❌ Admin o'chirish",
        callback_data="admin_delete"
    )
    tugma.button(
        text="🍔 Taom qo'shish",
        callback_data="taom_add"
    )
    tugma.button(
        text="🗑 Taom o'chirish",
        callback_data="taom_delete"
    )

    tugma.adjust(2)

    return tugma.as_markup()


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def savatcha_button():
    tugma = InlineKeyboardBuilder()

    tugma.button(
        text="✅ Buyurtmani tasdiqlash",
        callback_data="cart:confirm"
    )
    tugma.button(
        text="❌ Savatchani tozalash",
        callback_data="cart:clear"
    )

    tugma.adjust(1)
    return tugma.as_markup()


def phone_button():
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="📱 Telefon raqamni yuborish",
                request_contact=True
            )
        ]],
        resize_keyboard=True
    )


def location_button():
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="📍 Joylashuvni yuborish",
                request_location=True
            )
        ]],
        resize_keyboard=True
    )


def admin_order_button(order_id):
    tugma = InlineKeyboardBuilder()

    tugma.button(
        text="✅ Qabul qilish",
        callback_data=f"order:accept:{order_id}"
    )
    tugma.button(
        text="❌ Bekor qilish",
        callback_data=f"order:cancel:{order_id}"
    )

    tugma.adjust(2)
    return tugma.as_markup()