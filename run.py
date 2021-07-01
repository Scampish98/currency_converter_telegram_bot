from typing import Any, Callable

import decorator
import telebot  # type: ignore

from config import config
from extensions import APIException, Converter

INSTRUCTION = (
    "Ты можешь использовать следующие команды:\n"
    "/start - для получения приветственного сообщения и инструкции по использованию бота\n"
    "/help - для получения инструкции по использованию бота\n"
    "/values - для получения списка доступных валют\n"
    "\nДля конвертации одной валюты в другую нужно просто отправить мне сообщение вида:\n"
    "_<из какой валюты> <в какую валюту> <количество>_\n"
    "*Пример*: евро рубль 10"
)

bot = telebot.TeleBot(config["telebot"]["token"])
converter = Converter.from_config(config["converter"])


@decorator.decorator
def handler_wrapper(handler: Callable[..., Any], *args, **kwargs) -> Any:
    message: telebot.types.Message = args[0] if args else kwargs["message"]
    try:
        return handler(*args, **kwargs)
    except APIException as e:
        bot.reply_to(message, f"Ошибка пользователя:\n{type(e).__name__}: {e}")
    except Exception as e:
        bot.reply_to(
            message, f"Не удалось обработать команду:\n{type(e).__name__}: {e}"
        )


@bot.message_handler(commands=["start"])
def greet(message: telebot.types.Message) -> None:
    bot.send_message(message.chat.id, "Привет! Я бот для конвертации валют!")
    help_(message)


@bot.message_handler(commands=["help"])
def help_(message: telebot.types.Message) -> None:
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton(
            text="Доступные валюты", callback_data="/values"
        )
    )
    bot.send_message(
        message.chat.id, INSTRUCTION, parse_mode="Markdown", reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data == "/values")
def values_button(call: telebot.types.CallbackQuery) -> None:
    available_currencies(call.message)
    bot.answer_callback_query(call.id)


@bot.message_handler(commands=["values"])
def available_currencies(message: telebot.types.Message) -> None:
    currencies_list = "\n".join(
        (f"- {currency}" for currency in config["currencies"].keys())
    )
    bot.send_message(
        message.chat.id,
        f"""
Доступные для конвертации валюты:
{currencies_list}
    """,
    )


@bot.message_handler(content_types=["text"])
@handler_wrapper
def convert(message: telebot.types.Message) -> None:
    command = message.text.strip().split()
    if len(command) != 3:
        raise APIException("Неверное количество аргументов команды")
    source, target, amount = command
    if not is_number(amount) or float(amount) < 0:
        raise APIException("Количество валюты должно быть неотрицательным числом")
    source = source.lower()
    target = target.lower()
    bot.send_message(
        message.chat.id,
        f"Цена {amount} {source} в {target} - {converter.convert(source, target, float(amount))}",
    )


def is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


bot.polling(none_stop=True)
