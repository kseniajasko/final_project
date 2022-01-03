import json
import logging
import os
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext, \
    MessageHandler, Filters
from telegram_bot_pagination import InlineKeyboardPaginator

import telegramcalendar
from html_parsing import *


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

token = os.environ.get('TELEGRAM_TOKEN')
updater = Updater(token)

dispatcher = updater.dispatcher

FIRST, SECOND, THIRD = range(3)


search_cities = dict()
search_dates = dict()

def start(update, context):
    user = update.message.from_user
    chat_id = user['id']
    logger.info(f'User  started {user.first_name} {user.last_name}, chat_id is {chat_id}')
    keyboard = [
        [InlineKeyboardButton('Івано-Франківськ', callback_data='Ivano-Frankovsk'),
         InlineKeyboardButton('Дніпро', callback_data='dnepropetr')],

        [InlineKeyboardButton('Київ', callback_data='Kiev'),
        InlineKeyboardButton('Львів', callback_data='Lviv')],

        [InlineKeyboardButton('Луцьк', callback_data='lutsk'),
        InlineKeyboardButton('Одеса', callback_data='Odessa')],

        # InlineKeyboardButton('Харків', callback_data='Kharkiv'),
        # InlineKeyboardButton('Луцьк', callback_data='lutsk'),

        [InlineKeyboardButton('Харків', callback_data='Kharkiv'),
        InlineKeyboardButton('Чернівці', callback_data='chernovtsyi')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        text="Будь ласка, виберіть місто зі списку:",
        reply_markup=reply_markup
    )
    #update.bot.send_message(chat_id=update.callback_query.from_user.id, text="Please, select a city", reply_markup=reply_markup)
    return FIRST


def on_calendar(update, context):
    query = update.callback_query
    query.answer()
    search_cities[update.effective_chat.id] = query.data
    reply_markup = telegramcalendar.create_calendar()
    #query.message.send_message(text='Please, select a date', reply_markup=reply_markup)
    query.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Будь ласка, виберіть дату:',
        reply_markup=reply_markup
    )

    return SECOND


def on_callback_query(update, context):
    query = update.callback_query
    query.answer()

    bot = context.bot

    selected, date = telegramcalendar.process_calendar_selection(bot, update)

    if selected:
        if date < datetime.now() - timedelta(days=1):
            logger.info(
                f'User {update.effective_chat.id} selected wrong date')

            query.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Ви вибрали невірну дату. \nЩоб продовжити натисніть на /start.'
            )
            return ConversationHandler.END

        else:
            search_dates[update.effective_chat.id] = date.strftime("%d.%m.%Y")

            logger.info(
                f'User {update.effective_chat.id} selected {search_cities[update.effective_chat.id]}, {search_dates[update.effective_chat.id]}')

            query.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Натисніть на /result, щоб побачити результат.',
                reply_markup=ReplyKeyboardRemove()
            )

            tmp_result = parsing_result(search_cities[update.effective_chat.id], search_dates[update.effective_chat.id])

            tmp_result_str = '\n'.join(str(', '.join(e)) for e in tmp_result)

            tmp_list = new_text_view(tmp_result)

            global pagination_list
            pagination_list = [str('\n'.join(e)) for e in tmp_list]

            # bot.send_message(
            #     chat_id=update.effective_chat.id,
            #     text='Введіть команду /result, щоб побачити результат.',
            # )

            # if len(tmp_result_str) > 4096:
            #     for x in range(0, len(tmp_result_str), 4096):
            #         bot.send_message(
            #             chat_id=update.effective_chat.id,
            #             text=tmp_result_str[x:x + 4096]
            #         )
            #
            # else:
            #     context.bot.send_message(
            #         chat_id=update.effective_chat.id,
            #         text=tmp_result_str
            #
            #     )

            return ConversationHandler.END


def result_first_page(update, context):

    query = update.callback_query

    # query.answer()

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
        text=f'Щоб вибрати місто та дату заново натисніть на /start \U0001F60A.'
    )

def result_page_callback(update, context):
    query = update.callback_query

    query.answer()

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
        text="Вибачте, я не знаю цієї команди."
    )

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

    updater.start_polling()
    updater.idle()