import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

# Токен берем из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_BOT_USERNAME = "frishguardbot"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище состояния в памяти (по умолчанию включена фильтрация)
# active_chats = {chat_id: True/False}
# True = /bots off (удалять сообщения ботов)
# False = /bots on (пропускать сообщения ботов)
chat_settings: dict[int, bool] = {}


async def is_admin(message: types.Message) -> bool:
  """Проверка прав: только админы и создатель могут переключать режим."""
  if not message.from_user:
    return False
  member = await message.chat.get_member(message.from_user.id)
  return member.status in ["administrator", "creator"]


@dp.message(Command("bots"))
async def handle_bots_command(message: types.Message):
  if not await is_admin(message):
    return

  args = message.text.split()[1:] if message.text else []
  if not args:
    await message.reply("Использование: `/bots off` или `/bots on`")
    return

  action = args[0].lower()
  chat_id = message.chat.id

  if action == "off":
    chat_settings[chat_id] = True
    await message.reply(
        "🛡 Удаление сообщений от сторонних ботов и inline-ботов **включено**."
    )
  elif action == "on":
    chat_settings[chat_id] = False
    await message.reply(
        "🔓 Удаление сообщений от ботов **отключено** (режим по умолчанию)."
    )
  else:
    await message.reply("Неизвестный параметр. Используйте `off` или `on`.")


@dp.message()
async def monitor_messages(message: types.Message):
  chat_id = message.chat.id

  # Если фильтрация для чата не включена через /bots off — ничего не трогаем
  if not chat_settings.get(chat_id, False):
    return

  # 1. Проверка на отправку через inline-бота (@botname в начале/шапке)
  if message.via_bot:
    via_username = (message.via_bot.username or "").lower()
    if via_username != TARGET_BOT_USERNAME.lower():
      try:
        await message.delete()
      except Exception:
        pass
      return

  # 2. Проверка, если сообщение отправлено напрямую ботом-участником
  if message.from_user and message.from_user.is_bot:
    sender_username = (message.from_user.username or "").lower()
    if sender_username != TARGET_BOT_USERNAME.lower():
      try:
        await message.delete()
      except Exception:
        pass
      return


async def main():
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())