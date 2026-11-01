"""/start /help /book /mybookings /support commands (spec section 4).

The bot's only real job is to get the customer into the Mini App — all
actual booking logic lives in apps/web talking to apps/api. There is no
bot-side database access and no duplicated business logic here.

`settings: Settings` on each handler is injected by aiogram's dispatcher:
whatever is passed as a keyword to `dp.start_polling(...)` (see main.py) is
made available to any handler that declares a parameter of that name —
no need to thread it through manually or stash it on the Bot instance.
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.config import Settings
from app.keyboards import CONTACT_SUPPORT, HOW_IT_WORKS, main_menu_keyboard

router = Router(name="bookflow")


@router.message(CommandStart())
async def cmd_start(message: Message, settings: Settings) -> None:
    await message.answer(
        "Welcome to <b>BookFlow</b> — bookings made effortless.\n\n"
        "Tap below to browse services and book your next appointment in seconds.",
        reply_markup=main_menu_keyboard(settings),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Commands</b>\n"
        "/book — open BookFlow and start a new booking\n"
        "/mybookings — view your upcoming and past appointments\n"
        "/support — contact the business\n\n"
        "You can also just use the menu buttons below."
    )


@router.message(Command("book"))
async def cmd_book(message: Message, settings: Settings) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Open BookFlow", web_app=WebAppInfo(url=settings.mini_app_url))]
        ]
    )
    await message.answer("Let's get you booked in:", reply_markup=kb)


@router.message(Command("mybookings"))
async def cmd_my_bookings(message: Message, settings: Settings) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗓 My Appointments",
                    web_app=WebAppInfo(url=f"{settings.mini_app_url.rstrip('/')}/appointments"),
                )
            ]
        ]
    )
    await message.answer("Here's your appointments:", reply_markup=kb)


@router.message(Command("support"))
async def cmd_support(message: Message, settings: Settings) -> None:
    await message.answer(f"Need help? Reach the team at {settings.support_contact}.")


@router.message(lambda m: m.text == HOW_IT_WORKS)
async def on_how_it_works(message: Message) -> None:
    await message.answer(
        "1️⃣ Pick a service\n"
        "2️⃣ Choose a specialist (or 'any available')\n"
        "3️⃣ Pick a date & time that works for you\n"
        "4️⃣ Confirm — that's it. We'll remind you before it's time."
    )


@router.message(lambda m: m.text == CONTACT_SUPPORT)
async def on_contact_support(message: Message, settings: Settings) -> None:
    await cmd_support(message, settings)
