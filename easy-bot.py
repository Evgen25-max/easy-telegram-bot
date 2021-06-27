import logging
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SCAN_IP = os.getenv('SCAN_IP')
IP_LIST = SCAN_IP.split(', ')
PASSWORD = os.getenv('PASSWORD')
URL_STATUS = os.getenv('URL_STATUS')

BOT_MESSAGE = {
    'start': """Hello. Valid command:
     /ip,
     /status_ip,
     """
}
wait_pass = {}

logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def my_logger(function_name, **kwargs):
    """Write to log: function, the named parameters of the exception.."""

    params = ''
    for name, value in kwargs.items():
        params += f', {name}: {value}'
    logging.error(
        f'Error function: "{function_name}", {params} "'
    )
    return True


def is_admin(chat_id):
    """Returns whether the admin user has unblocked."""

    return wait_pass.get(str(chat_id)) == 'admin'


def give_pass(chat_id, context):
    """Message for admin password."""

    context.bot.send_message(chat_id=chat_id, text='give me password')


def get_ip(update, context):
    """Return ip-list servers (if admin)."""

    chat_id = update.effective_chat.id
    if is_admin(chat_id):
        return context.bot.send_message(chat_id=chat_id, text=f'{IP_LIST}')
    wait_pass.update({str(chat_id): True})
    give_pass(chat_id, context)


def status(update, context):
    """Return status server in ip-list(if admin)."""

    chat_id = update.effective_chat.id
    if is_admin(chat_id):
        resp = requests.get(URL_STATUS)
        if resp.status_code != 200:
            my_logger(
                status(status.__name__),
                message=f'{URL_STATUS} return {resp.status_code}.'
            )
        soup = BeautifulSoup(resp.text, 'lxml')
        text = soup.text
        rezult = ''.join([
            f'{ip}: OK\n' if text.find(ip) != -1 else f'{ip}: BAD\n' for ip in IP_LIST
        ])
        return context.bot.send_message(chat_id=chat_id, text=f'{rezult}')

    wait_pass.update({str(chat_id): True})
    give_pass(chat_id, context)


COMMAND_LIST = {
    '/ip': get_ip,
    '/status_ip': status,
}

updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher


def start(update, context):
    """Message for /start command."""

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=BOT_MESSAGE['start']
    )


def echo(update, context):
    """Repeat message (not command)."""

    if (
            update.message.text == PASSWORD and
            wait_pass.get(str(update.effective_chat.id)) is True
    ):
        wait_pass.update({str(update.effective_chat.id): 'admin'})
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Unlock_admin, retry command.'
        )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.text
    )


def command(update, context):
    """Familiar/unfamiliar commands."""

    action = COMMAND_LIST.get(update.message.text)
    if action:
        action(update, context)
    else:
        unknown(update, context)


def unknown(update, context):
    """Message for unfamiliar command."""

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command."
    )


start_handler = CommandHandler('start', start)
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
command_handler = MessageHandler(Filters.command, command)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(echo_handler)
dispatcher.add_handler(command_handler)

if __name__ == '__main__':
    updater.start_polling()
