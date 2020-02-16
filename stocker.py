import logging
from telegram.ext import Updater, CommandHandler
from manage_stock import mkstock_handler, rmstock_handler
from monitor_stock import startmonitor_handler, snoozemonitor_handler, cancelmonitor_handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def help(update, context):
    update.message.reply_text("Use /start to test this bot.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    f = open("token.txt", "r")
    token = f.read()
    updater = Updater(token, use_context=True)

    # manage_stock.py handlers
    updater.dispatcher.add_handler(mkstock_handler)
    updater.dispatcher.add_handler(rmstock_handler)
    # monitor_stock.py handlers
    updater.dispatcher.add_handler(startmonitor_handler)
    updater.dispatcher.add_handler(snoozemonitor_handler)
    updater.dispatcher.add_handler(cancelmonitor_handler)
    # misc handlers
    updater.dispatcher.add_handler(CommandHandler('help', help))
    # updater.dispatcher.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
