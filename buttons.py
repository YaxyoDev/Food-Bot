from aiogram.utils.keyboard import ReplyKeyboardBuilder

"""
kok         primary
yashil      success
qizil       danger
"""

def start_button():
    tugma = ReplyKeyboardBuilder()
    tugma.button(text="🍽 Taomlar", style="success")
    tugma.button(text="🛒 Savatcha", style="primary")
    tugma.button(text="Ro'yxatdan o'tish", style="primary")
    tugma.adjust(2)
    return tugma.as_markup(resize_keyboard=True)

