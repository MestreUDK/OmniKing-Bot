from telegram.ext import CallbackQueryHandler, CommandHandler
from handlers.public import start, help_command
from handlers.catalog import alphabet, anime, callback, catalog_status, recent_command, recommend, search_command, shortcut
from kingcore.commands import health

def register_handlers(app):
    for names,handler in [(['start'],start),(['ajuda','help'],help_command),(['health'],health),
            (['status'],catalog_status),(['buscar','busca'],search_command),(['alfabeto'],alphabet),
            (['atalhos'],shortcut),(['recentes'],recent_command),(['recomendar'],recommend),(['anime'],anime)]:
        app.add_handler(CommandHandler(names,handler))
    app.add_handler(CallbackQueryHandler(callback,pattern=r'^ok:'))
