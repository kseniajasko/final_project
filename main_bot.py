
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram_bot_pagination import InlineKeyboardPaginator
from datetime import timedelta, datetime
import logging, os, telegramcalendar
from html_parsing import *


logging.basicConfig(filename='data/bot_info.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

token = os.environ.get('TELEGRAM_TOKEN')
updater = Updater(token, use_context=True)

dispatcher = updater.dispatcher

FIRST, SECOND = range(2)


search_cities = dict()
search_dates = dict()
parsing_dict = dict()

def start(update, context):
    user = update.message.from_user
    chat_id = user['id']
    logger.info(f'User  started {user.first_name} {user.last_name}, chat_id is {chat_id}')
    keyboard = [
        [InlineKeyboardButton('Івано-Франківськ', callback_data='ivano-frankovsk'),
         InlineKeyboardButton('Дніпро', callback_data='dnepropetr')],

        [InlineKeyboardButton('Київ', callback_data='kiev'),
        InlineKeyboardButton('Львів', callback_data='lviv')],

        [InlineKeyboardButton('Луцьк', callback_data='lutsk'),
        InlineKeyboardButton('Одеса', callback_data='odessa')],

        [InlineKeyboardButton('Полтава', callback_data='poltava'),
         InlineKeyboardButton('Ужгород', callback_data='ujgorod')],

        [InlineKeyboardButton('Харків', callback_data='kharkiv'),
        InlineKeyboardButton('Чернівці', callback_data='chernovtsyi')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Будь ласка, виберіть місто \U00002B07",
        reply_markup=reply_markup
    )

    return FIRST


def on_calendar(update, context):
    query = update.callback_query
    query.answer()
    search_cities[update.effective_chat.id] = query.data
    reply_markup = telegramcalendar.create_calendar()

    query.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Будь ласка, виберіть дату \U00002B07',
        reply_markup=reply_markup
    )

    return SECOND


def on_callback_query(update, context):
    query = update.callback_query
    query.answer()

    bot = context.bot

    selected, date = telegramcalendar.process_calendar_selection(bot, update)

    if selected:
        if date < datetime.now() - timedelta(days=1) or date - datetime.now() > timedelta(days=59):
            logger.info(
                f'User {update.effective_chat.id} selected wrong date ')

            query.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Ви вибрали невірну дату \U0000274C. \nЩоб продовжити натисніть на /start.'
            )
            return ConversationHandler.END

        else:
            search_dates[update.effective_chat.id] = date.strftime("%d.%m.%Y")

            logger.info(
                f'User {update.effective_chat.id} selected {search_cities[update.effective_chat.id]}, {search_dates[update.effective_chat.id]}')

            query.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Ви вибрали дату: {search_dates[update.effective_chat.id]} \U00002705. \nНатисніть на /result, щоб побачити результат та почекайте \U0000270F.',
                reply_markup=ReplyKeyboardRemove()
            )

            tmp_result = parsing_result(search_cities[update.effective_chat.id], search_dates[update.effective_chat.id])
            tmp_list = new_text_view(tmp_result)
            tmp_pagination_list = [str('\n'.join(e)) for e in tmp_list]
            parsing_dict[update.effective_chat.id] = tmp_pagination_list

            return ConversationHandler.END

def result_first_page(update, context):
    query = update.callback_query
    logger.info(f'User {update.effective_chat.id} have got result')

    pagination_list = parsing_dict[update.effective_chat.id]

    paginator = InlineKeyboardPaginator(
        len(pagination_list),
        data_pattern='page#{page}'
    )

    update.message.reply_text(
        text=pagination_list[0],
        reply_markup=paginator.markup,
        parse_mode='Markdown'
    )

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Переключайте сторінки для того, щоб побачити весь розклад \U000023EA \U000025C0 \t \U000020E3 \t \U000025B6 \U000023E9   \nЩоб вибрати місто та дату заново натисніть на /start \U0001F60A.'
    )

def result_page_callback(update, context):
    query = update.callback_query

    query.answer()

    pagination_list = parsing_dict[update.effective_chat.id]

    page = int(query.data.split('#')[1])

    paginator = InlineKeyboardPaginator(
        len(pagination_list),
        current_page=page,
        data_pattern='page#{page}'
    )

    query.edit_message_text(
        text=pagination_list[page - 1],
        reply_markup=paginator.markup,
        parse_mode='Markdown'
    )

def unknown(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Вибачте, я не знаю цієї команди \U0001F613'
    )

def echo(update, context):
    text = 'ECHO: ' + update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Я Вас не розумію \U0001F613 \nБудь ласка, використовуйте лише запропоновані команди \U0001F60A')

if __name__ == '__main__':

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST: [
                CallbackQueryHandler(on_calendar),

            ],
            SECOND: [
                CallbackQueryHandler(on_callback_query),
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler)

    updater.dispatcher.add_handler(CommandHandler('result', result_first_page))
    updater.dispatcher.add_handler(CallbackQueryHandler(result_page_callback, pattern='^page#'))

    unknown_handler = MessageHandler(Filters.command, unknown)
    updater.dispatcher.add_handler(unknown_handler)

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    updater.start_polling()
    updater.idle()