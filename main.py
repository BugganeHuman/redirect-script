import asyncio
import os
from hydrogram import Client, filters
from hydrogram.types import Message
from dotenv import load_dotenv
from cachetools import TTLCache

load_dotenv()


TARGET_CHANNEL = int(os.getenv('TARGET_CHANNEL'))
SOURCE_CHANNEL_1 = int(os.getenv('SOURCE_CHANNEL_1'))
SOURCE_CHANNEL_2 = int(os.getenv('SOURCE_CHANNEL_2'))
TARGET_GROUP_1_TEST = int(os.getenv('TEST_TARGET_GROUP_1'))
TARGET_GROUP_2_TEST = int(os.getenv('TEST_TARGET_GROUP_2'))
MY = int(os.getenv('LOGS_CHANNEL'))
PHONE_NUMBER = str(os.getenv('PHONE_NUMBER'))


asyncio.set_event_loop(asyncio.new_event_loop())
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')


app = Client(
    name="tg_usa_session",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER,
    device_model="Windows 11 PC",
    system_version="Hydrogram Client"
)

processed_messages_cache = TTLCache(maxsize=5000, ttl=50000)

#@app.on_message(filters.all)
async def check_chat_id(client : Client, message : Message):
    print(message.chat.id)


SOURCE_CHANNELS = [SOURCE_CHANNEL_1, SOURCE_CHANNEL_2]


#@app.on_message(filters.chat(chats=SOURCE_CHANNELS))
async def redirect_script(client : Client, message : Message):
    try:
        msg_key = f"{message.chat.id}_{message.id}"
        if msg_key in processed_messages_cache:
            print(f"Дубль заблокирован (по ID): {msg_key}")
            return

        text = message.text or message.caption or ''
        text_lower = text.lower().strip()

        if text_lower:
            if text_lower in processed_messages_cache:
                await client.send_message(chat_id=MY, text='Сообщение скипнуто: дубликат текста')
                print(f"Дубль заблокирован (по тексту): '{text_lower}'")
                return
            processed_messages_cache[text_lower] = True
        processed_messages_cache[msg_key] = True

        VIP_WORDS = ["дмитри", "кабанов", "гордеев", "шукуров", "основатель", "директор",
                        "ceo", "амбассадор", 'ярослав', "фаррух", 'polymarket', 'крипт', 'торг',
                        'virus2027', 'pulse', 'листинг', 'конспирологи', 'мир', '2027'
                    ]
        if message.video:
            width = message.video.width
            height = message.video.height
            if height > width:
                await client.send_message(chat_id=MY, text='сообщение скипнуто ибо это вертикалка')
                print('сообщение скипнуто ибо это вертикалка')
                return

        if message.media_group_id:
            album_key = f"album_{message.media_group_id}"
            if album_key in processed_messages_cache:
                print(f"Кусок альбома {message.id} пропущен, так как альбом уже в работе.")
                return
            processed_messages_cache[album_key] = True

            try:
                print(f"Собираем альбом {message.media_group_id}...")
                album_messages = await client.get_media_group(chat_id=message.chat.id, message_id=message.id)
                await client.copy_media_group(chat_id=TARGET_CHANNEL, from_chat_id=message.chat.id, message_id=message.id)
                await client.send_message(chat_id=MY, text=f"Альбом {message.media_group_id} успешно переслан.")
            except Exception as album_err:
                print(f"Ошибка при отправке альбома: {album_err}")
                if album_key in processed_messages_cache:
                    del processed_messages_cache[album_key]
            return

        if message.video_note:
            await client.send_message(chat_id=MY, text='сообщение скипнуто ибо это кружок')
            print('сообщение скипнуто ибо это кружок')
            return

        if message.forward_date:
            text = message.text or message.caption or ''
            text_lower = text.lower()
            if text_lower:
                is_vip = any(vip in text_lower for vip in VIP_WORDS)
                if is_vip:
                    await message.copy(chat_id=TARGET_CHANNEL)
                    await client.send_message(chat_id=MY, text=f'сообщение - {message.id} отправлено')
                    return

            await client.send_message(chat_id=MY, text='сообщение скипнуто ибо это пересланное')
            print('сообщение скипнуто ибо это пересланное')
            return

        if message.sticker:
            await client.send_message(chat_id=MY, text='сообщение скипнуто ибо это стикер')
            print('сообщение скипнуто ибо это стикер')
            return

        if message.poll:
            await client.send_message(chat_id=MY, text='сообщение скипнуто ибо это опросс')
            print('сообщение скипнуто ибо это опросс')
            return

        STOP_WORDS = ["реклам", "подписывайтесь", "переходи по ссылке", "закаж", 'vip',
                        "идеального момента", "окна возможностей", "стабильной работой", "изменить свою жизнь",
                        "мотиваци", "тренд", 'доход', 'промо', 'жизн', "толп", "quiz", "свер",
                        "выбирай", 'упуст', 'мин', 'айдар', 'ислямов', 'zoom'
                    ]

        text = message.text or message.caption or ''
        text_lower = text.lower()
        if text_lower:
            is_vip = any(vip in text_lower for vip in VIP_WORDS)
            if not is_vip:
                for word in STOP_WORDS:
                    if word in text_lower:
                        await client.send_message(chat_id=MY, text=f" Пост ЗАБЛОКИРОВАН! Найдено стоп-слово: '{word}'")
                        print(f" Пост ЗАБЛОКИРОВАН! Найдено стоп-слово: '{word}'")
                        return

        await message.copy(chat_id=TARGET_CHANNEL)
        #await message.copy(chat_id=TARGET_GROUP_2_TEST)
        #await message.copy(chat_id=TARGET_GROUP_1_TEST)

        for group_name, group_id in os.environ.items():
            if group_name.startswith('TARGET_GROUP_'):
                await message.copy(chat_id=int(group_id))
                print(f'message send to group {group_name}')

        """
        теперь группы моэно удобно добавлять, код не надо менять совсем
        просто дописываешь в .env файл переменную TARGET_GROUP_(и ее номер) = ее id
        """


        await client.send_message(chat_id=MY, text=f'сообщение - {message.id} отправлено')
    except Exception as e:
        print(e)



async def monitor_history(client: Client):
    last_ids = {}

    for ch in SOURCE_CHANNELS:
        try:
            async for msg in client.get_chat_history(ch, limit=1):
                last_ids[ch] = msg.id
        except Exception as e:
            print(f"Ошибка при стартовой проверке истории канала {ch}: {e}")
            last_ids[ch] = 0

    print("--- SCANNING GET_CHAT_HISTORY STARTED ---")

    while True:
        await asyncio.sleep(15)
        for ch in SOURCE_CHANNELS:
            try:
                async for message in client.get_chat_history(ch, limit=10):
                    if message.id > last_ids.get(ch, 0):
                        print(f"Найдено новое сообщение {message.id} в канале-доноре {ch}!")
                        last_ids[ch] = max(last_ids.get(ch, 0), message.id)
                        await redirect_script(client, message)
                        await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Ошибка при активном опросе канала {ch}: {e}")


async def main():
    await app.start()
    await monitor_history(app)


if __name__ == "__main__":
    print("userbot is starting ")
    app.run(main())