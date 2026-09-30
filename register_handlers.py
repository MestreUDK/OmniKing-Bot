from telegram.ext import CommandHandler
from handlers.public import start, help_command
from kingcore.commands import health, status

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["ajuda", "help"], help_command))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("status", status))
