from authenticate import get_config
from monitor_stock import monitor

GREETING_MESSAGE = '''🖖🏻Greetings, {}.
Your portfolio: {} will be monitored.

You can control me by sending these commands:
Use /mkstock <SYMBOL> <ALERT-MARGIN> to add stock to your portfolio
Use /rmstock <SYMBOL> to remove stock from your portfolio
'''


def start(update, context):
    user = update.message.from_user
    _, config = get_config(user.id, user.first_name)
    context.user_data["config"] = config
    context.user_data["market_status"] = ""
    chat_id = update.message.chat_id
    update.message.reply_text(GREETING_MESSAGE.format(
        config["name"], config["portfolio"]))
    new_job = context.job_queue.run_once(
        monitor, 0, context={"chat_id": chat_id, "config": config})
