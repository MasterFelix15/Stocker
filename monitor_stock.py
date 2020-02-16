from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
import time
from datetime import datetime
from yahoo_fin.stock_info import get_data, get_live_price
from authenticate import get_config


# interval to refresh stock info in seconds
REFRESH_INTERVAL = 1
# market open and close hour, time-zone dependent
PRE_MARKET_OPEN = 800
PRE_MARKET_MESSAGE = '''🕗Pre-Market is now open.
Stock monitoring is now online. 
However, your trading institute may not allow trading at this time.'''
NORMAL_MARKET_OPEN = 930
NORMAL_MARKET_MESSAGE = '''🕥Market is now open.
Stock monitoring online'''
NORMAL_MARKET_CLOSE = 1600
POST_MARKET_MESSAGE = '''🕓It is now after hours. 
Stock monitoring is still online. 
However, your trading institute may not allow trading at this time.
'''
POST_MARKET_CLOSE = 1800

MONITOR_KEYBOARD = [
    [InlineKeyboardButton("⏰Snooze for 5 Minutes",
                          callback_data="SNZ5")],
    [InlineKeyboardButton("⏰Snooze for 20 Minutes",
                          callback_data="SNZ20")],
    [InlineKeyboardButton("🌓Sleep for the day",
                          callback_data="CCL1D")],
    [InlineKeyboardButton("❕Acknowledge", callback_data="SNZ0"),
     InlineKeyboardButton("❌Stop Service", callback_data="CCL")]
]


def monitor(context):
    job = context.job
    chat_id = job.context["chat_id"]
    config = job.context["config"]
    if "market_status" not in job.context:
        market_status = "closed"
    else:
        market_status = job.context["market_status"]

    reply_markup = InlineKeyboardMarkup(MONITOR_KEYBOARD)

    # check market hours
    now = datetime.now()
    time = now.hour*100 + now.minute
    if time < PRE_MARKET_OPEN:
        market_status = "closed"
        context.bot.send_message(
            chat_id=chat_id, text='Market is not yet open, please come back later.')
        return
    elif time < NORMAL_MARKET_OPEN:
        if market_status != "pre-market":
            market_status = "pre-market"
            context.bot.send_message(chat_id=chat_id, text=PRE_MARKET_MESSAGE)
    elif time < NORMAL_MARKET_CLOSE:
        if market_status != "normal-market":
            market_status = "normal-market"
            context.bot.send_message(
                chat_id=chat_id, text=NORMAL_MARKET_MESSAGE)
    elif time < POST_MARKET_CLOSE:
        if market_status != "post-market":
            market_status = "post-market"
            context.bot.send_message(chat_id=chat_id, text=POST_MARKET_MESSAGE)
    else:
        market_status = "closed"
        context.bot.send_message(
            chat_id=chat_id, text='Market is closed, see you tomorrow.')
        return

    date = now.strftime("%Y-%m-%d")
    for stock in config["portfolio"]:
        alert_margin = config["portfolio"][stock]
        try:
            stock_td = get_data(stock, start_date=date)
            price_1dmax = stock_td["high"][date]
            price_1dmin = stock_td["low"][date]
            price_live = get_live_price(stock)
            # give stock alert
            # TO-DO: differentiate between low and high
            if price_live > price_1dmax*(1-alert_margin):
                context.bot.send_message(chat_id=chat_id, text=stock+" price approaching daily high:" +
                                         str(price_live)+"/"+str(price_1dmax), reply_markup=reply_markup)
                return
            if price_live < price_1dmin*(1+alert_margin):
                context.bot.send_message(chat_id=chat_id, text=stock+" price approaching daily low:"+str(
                    price_live)+"/"+str(price_1dmin), reply_markup=reply_markup)
                return
        except KeyError:
            context.bot.send_message(
                chat_id=chat_id, text='Market data not available currently, please come back later.')
            return
    # schedule next refresh
    new_job = context.job_queue.run_once(monitor, REFRESH_INTERVAL*60, context={
                                         "chat_id": chat_id, "market_status": market_status, "config": config})


GREETING_MESSAGE = '''🖖🏻*Greetings*, {}.
Your portfolio💼: 
{}will be monitored.'''

FIRST_TIME_GREET_MESSAGE = '''🖖🏻*Greetings*, {}.
Your portfolio is currently empty. You can use /mkstock command to add a stock to your portfolio.
Use /help for other commands.'''


def start(update, context):
    # authenticate users and retrieve config
    # standard for all entry-point handlers
    if "config" not in context.user_data:
        user = update.message.from_user
        _, config = get_config(user.id, user.first_name)
        context.user_data["config"] = config
    # authentication complete
    chat_id = update.message.chat_id
    if len(context.user_data["config"]["portfolio"]) == 0:
        update.message.reply_text(FIRST_TIME_GREET_MESSAGE.format(
            context.user_data["config"]["name"]), parse_mode=ParseMode.MARKDOWN)
    else:
        portfolio_str = ""
        for symbol in context.user_data["config"]["portfolio"]:
            portfolio_str += "\t*{}* {} share(s)\n".format(
                symbol, context.user_data["config"]["portfolio"][symbol]["num_shares"])
        update.message.reply_text(GREETING_MESSAGE.format(
            context.user_data["config"]["name"], portfolio_str), parse_mode=ParseMode.MARKDOWN)
        new_job = context.job_queue.run_once(
            monitor, 0, context={"chat_id": chat_id, "config": context.user_data["config"]})


def snooze(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    time_to_snooze = int(str(query.data).split('SNZ')[1])
    query.edit_message_text(
        text="Next monitoring session will start in {} minutes".format(time_to_snooze))
    new_job = context.job_queue.run_once(
        monitor, time_to_snooze*60, context={"chat_id": chat_id, "config": context.user_data["config"]})


def cancel(update, context):
    query = update.callback_query
    query.edit_message_text(text="See you next time")


startmonitor_handler = CommandHandler('start', start)
snoozemonitor_handler = CallbackQueryHandler(snooze, pattern='^SNZ.+$')
cancelmonitor_handler = CallbackQueryHandler(cancel, pattern='^CCL.*$')
