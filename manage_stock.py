from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Filters
from yahoo_fin.stock_info import get_live_price
import sqlite3
from authenticate import get_config

TYPING_SYMBOL, TYPING_SHARES, CHOOSING_MARGIN = range(3)


def add_stock(update, context):
    # authenticate users and retrieve config
    # standard for all entry-point handlers
    if "config" not in context.user_data:
        user = update.message.from_user
        _, config = get_config(user.id, user.first_name)
        context.user_data["config"] = config
    # authentication complete
    update.message.reply_text(
        "Let's add a new stock, starting with the symbol:")
    context.user_data["new_stock"] = {}
    return TYPING_SYMBOL


def add_symbol(update, context):
    symbol = update.message.text
    try:
        get_live_price(symbol)
        context.user_data["new_stock"]["symbol"] = symbol
        update.message.reply_text("How many shares do you hold?")
        return TYPING_SHARES
    except:
        update.message.reply_text(
            "No data found, symbol may be delisted, let's try again.")
        return TYPING_SYMBOL


def add_shares(update, context):
    try:
        num_shares = update.message.text
        context.user_data["new_stock"]["num_shares"] = int(num_shares)
        symbol = context.user_data["new_stock"]["symbol"]
        update.message.reply_text('''Specify a margin to adjust the sensitvity of price alert
For example, if you set a margin=m, the stocks daily high = h, daily low = l,
then I will notify you when live price > (1-m)*h and when live price < (1+m)*l.
A margin of 0.01-0.03 is usually recommended, depending on the volatility of the stock.''')
        return CHOOSING_MARGIN
    except:
        update.message.reply_text(
            "Please enter a valid number of shares, let's try again.")
        return TYPING_SHARES


def add_margin(update, context):
    try:
        margin = update.message.text
        context.user_data["new_stock"]["margin"] = float(margin)
        conn = sqlite3.connect('stocker.db')
        conn.execute('''
        INSERT OR REPLACE INTO STOCK (USERID, SYMBOL, NUM_SHARES, MARGIN)
        VALUES ({}, "{}", {}, {});
        '''.format(
            context.user_data["config"]["id"],
            context.user_data["new_stock"]["symbol"],
            context.user_data["new_stock"]["num_shares"],
            context.user_data["new_stock"]["margin"]))
        conn.commit()
        conn.close()
        update.message.reply_text('''Symbol: {}
Number of shares: {}
Alert Margin: {}
has been successfully added to your portfolio.'''.format(
            context.user_data["new_stock"]["symbol"],
            context.user_data["new_stock"]["num_shares"],
            context.user_data["new_stock"]["margin"]))
        # refresh user config
        del(context.user_data["new_stock"])
        _, config = get_config(context.user_data["config"]["id"])
        context.user_data["config"] = config
        return ConversationHandler.END
    except:
        update.message.reply_text(
            "Please enter a valid margin, let's try again.")
        return CHOOSING_MARGIN


def done(update, context):
    context.user_data = "hello, this is a done"
    return ConversationHandler.END


mkstock_handler = ConversationHandler(
    entry_points=[CommandHandler('mkstock', add_stock)],
    states={
        TYPING_SYMBOL: [MessageHandler(Filters.text, add_symbol)],
        TYPING_SHARES: [MessageHandler(Filters.text, add_shares)],
        CHOOSING_MARGIN: [MessageHandler(Filters.text, add_margin)]
    },
    fallbacks=[MessageHandler(Filters.regex('^Done$'), done)]
)


def remove_stock(update, context):
    # authenticate users and retrieve config
    # standard for all entry-point handlers
    if "config" not in context.user_data:
        user = update.message.from_user
        _, config = get_config(user.id, user.first_name)
        context.user_data["config"] = config
    # authentication complete
    update.message.reply_text(
        "Which stock do you want to remove?")
    return TYPING_SYMBOL


def remove_symbol(update, context):
    symbol = update.message.text
    try:
        conn = sqlite3.connect('stocker.db')
        conn.execute('''
        DELETE FROM STOCK
        WHERE USERID = {} AND SYMBOL = "{}";
        '''.format(
            context.user_data["config"]["id"],
            symbol))
        conn.commit()
        conn.close()
        update.message.reply_text('''Symbol: {}
has been successfully removed from your portfolio.'''.format(symbol))
        # refresh user config
        _, config = get_config(context.user_data["config"]["id"])
        context.user_data["config"] = config
        return ConversationHandler.END
    except KeyError:
        update.message.reply_text(
            "Something went wrong, please try again later.")
        return ConversationHandler.END


rmstock_handler = ConversationHandler(
    entry_points=[CommandHandler('rmstock', remove_stock)],
    states={
        TYPING_SYMBOL: [MessageHandler(Filters.text, remove_symbol)]
    },
    fallbacks=[MessageHandler(Filters.regex('^Done$'), done)]
)
