import sqlite3

from logging import getLogger

from telegram import Bot
from telegram import Update
from telegram import ReplyKeyboardRemove

from telegram.ext import Updater
from telegram.ext import MessageHandler
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters

from request.validators import ACTION_MAP1, ACTION_MAP2, PROBLEM_MAP
from request.validators import validate_problem, validate_action, problem_res, action_res

token = '1475780423:AAFHb8gARaYQI-3y3owAGcVfUXeIpET73Bs'

conn = sqlite3.connect('example.db')

logger = getLogger(__name__)

PROBLEM, ACTION, FILE = range(3)


def start_handler(bot: Bot, update: Update):
    # ask problem
    problems = [f'{key} - {value}' for key, value in PROBLEM_MAP.items()]
    problems = '\n'.join(problems)
    update.message.reply_text(f'''
    Привет, {update.message.from_user.first_name} {update.message.from_user.last_name}!
Меня зовут EnterpreNeural и я интерактивный помощник предпринимателей. 
Готов провести для вас персональную консультацию.\nНачнем!
\nЕсть ли среди предложенных проблем ваша?\n 
{problems}
    ''')
    return PROBLEM


def problem_handler(bot: Bot, update: Update, user_data: dict):
    # get problem
    problem = validate_problem(text=update.message.text)
    if problem is None:
        update.message.reply_text('Пожалуйста, укажите корректный номер проблемы!')
        return PROBLEM

    user_data[PROBLEM] = problem
    logger.info('user_data: %s', user_data)

    # ask action
    if problem == 1:

        actions = [f'{key} - {value}' for key, value in ACTION_MAP1.items()]
        actions = '\n'.join(actions)
        update.message.reply_text(f'''
Выберите нарушение:
{actions}
''')
        return ACTION

    elif problem == 2:
        actions = [f'{key} - {value}' for key, value in ACTION_MAP2.items()]
        actions = '\n'.join(actions)
        update.message.reply_text(f'''
Выберите нарушение:
{actions}
''')
        return ACTION

    else:
        return 'бот еще в доработке'


def action_handler(bot: Bot, update: Update, user_data: dict):
    # get action
    action = validate_action(text=update.message.text)
    if action is None:
        update.message.reply_text('Пожалуйста, укажите корректный номер нарушения!')
        return ACTION

    user_data[ACTION] = action
    logger.info('user_data: %s', user_data)

    # ask files
    update.message.reply_text('''
У вас есть заключение из Росреестра? Пожалуйста, загрузите файл.
''')
    return FILE


def finish_handler(bot: Bot, update: Update, user_data: dict):
    # get file
    file = update.message
    if file is None:
        update.message.reply_text('Пожалуйста, загрузите файл!')
        return FILE

    user_data[FILE] = file.getFileName()
    logger.info('user_data: %s', user_data)

    # result
    update.message.reply_text(f'''
Все данные успешно сохранены! 
Проблема: {problem_res(user_data[ACTION])};\nНарушение: {action_res(user_data[ACTION])};\nФайл: {user_data[FILE]} 
''')
    return ConversationHandler.END


def cancel_handler(update: Update):
    update.message.reply_text('Отмена. Для того, чтобы начать сначала нажмите: /start')
    return ConversationHandler.END


def echo_handler(update: Update):
    update.message.reply_text(
        'Нажмите /start для работы с консультантом!',
        reply_markup=ReplyKeyboardRemove(),
    )


def main():
    logger.info('Start working')
    bot = Bot(
        token=token,
    )
    updater = Updater(
        bot=bot,
    )

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start_handler),
        ],
        states={
            PROBLEM: [
                MessageHandler(Filters.all, problem_handler, pass_user_data=True),
            ],
            ACTION: [
                MessageHandler(Filters.all, action_handler, pass_user_data=True),
            ],
            FILE: [
                MessageHandler(Filters.all, finish_handler, pass_user_data=True),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_handler),
        ],
    )
    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(MessageHandler(Filters.all, echo_handler))

    updater.start_polling()
    updater.idle()
    logger.info('Finish working')


if __name__ == '__main__':
    main()
