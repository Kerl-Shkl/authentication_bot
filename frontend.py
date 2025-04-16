import asyncio
import uuid
import logging
import aiogram.types as atypes
from config import config
from controller import controller, Request
from aiogram import Bot, Dispatcher, html, Router
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.formatting import Bold, as_list, as_key_value
from aiogram import F

logging.basicConfig(level=logging.INFO)
bot = Bot(
    token=config.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

my_router = Router()
USER_ID = int(config.user_id.get_secret_value())
my_router.message.filter(F.from_user.id == USER_ID)

another_router = Router()
another_router.message.filter(F.from_user.id != USER_ID)

BTN_TEXT_ENABLE = "Enable edit mode"
BTN_TEXT_DISABLE = "Disable edit mode"


def getModeButton() -> atypes.KeyboardButton:
    if controller.editMode():
        return atypes.KeyboardButton(text=BTN_TEXT_DISABLE)
    else:
        return atypes.KeyboardButton(text=BTN_TEXT_ENABLE)


def getKeyboard() -> atypes.ReplyKeyboardMarkup:
    kb = [[getModeButton()]]
    return atypes.ReplyKeyboardMarkup(
        keyboard=kb, resize_keyboard=True, input_field_placeholder="Control edit mode"
    )


def getAcceptRejectKeyboard(id: uuid.UUID) -> atypes.InlineKeyboardMarkup:
    buttons = [
        [
            atypes.InlineKeyboardButton(
                text="accept", callback_data=("accept_" + str(id))
            ),
            atypes.InlineKeyboardButton(
                text="reject", callback_data=("reject_" + str(id))
            ),
        ],
    ]
    keyboard = atypes.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@my_router.message(CommandStart())
async def cmdStart(message: atypes.Message):
    await message.answer("Hello, Kerl!", reply_markup=getKeyboard())


@my_router.message(F.text == BTN_TEXT_ENABLE)
async def turnOnEditMode(message: atypes.Message):
    controller.turnOnEdit()
    await message.reply(text="Edit mode enabled", reply_markup=getKeyboard())


@my_router.message(F.text == BTN_TEXT_DISABLE)
async def turnOffEditMode(message: atypes.Message):
    controller.turnOffEdit()
    await message.reply(text="Edit mode disabled", reply_markup=getKeyboard())


@my_router.message(Command("ask_request"))
async def askRequestCmd(message: atypes.Message):
    await askRequest(Request(uuid.uuid4(), 1, "hype"))


async def askRequest(req: Request):
    content = as_list(
        "New request",
        as_key_value("Name", req.name),
        as_key_value("Id", req.id),
        sep="\n\n",
    )
    await bot.send_message(
        config.user_id.get_secret_value(),
        reply_markup=getAcceptRejectKeyboard(req.id),
        **content.as_kwargs()
    )


@my_router.callback_query(F.data.startswith("accept_"))
async def acceptHandler(callback: atypes.CallbackQuery):
    id = uuid.UUID(callback.data.split("_")[1])
    controller.acceptRequest(id)
    await callback.message.edit_text(
        text=(callback.message.html_text + "\n<b>accepted</b>"), reply_markup=None
    )
    await callback.answer()


@my_router.callback_query(F.data.startswith("reject_"))
async def rejectHandler(callback: atypes.CallbackQuery):
    id = uuid.UUID(callback.data.split("_")[1])
    controller.rejectRequest(id)
    await callback.message.edit_text(
        text=(callback.message.html_text + "\n<b>rejected</b>"), reply_markup=None
    )
    await callback.answer()


@my_router.message()
async def defaultMyHandler(message: atypes.Message):
    await message.answer("I don't understand you, Kerl", reply_markup=getKeyboard())


@another_router.message()
async def defaultStrangerHandler(message: atypes.Message):
    await message.answer("I don't talk with strangers")


async def run() -> None:
    dp = Dispatcher()
    dp.include_routers(my_router, another_router)
    await dp.start_polling(bot)
