from modules.deeplinks import parse_payload
from handlers.catalog import browse, fail

async def start(update,context):
    if not update.effective_message:return
    if context.args:
        try:target=parse_payload(' '.join(context.args))
        except ValueError:return await fail(update,'Link inválido. Use /start para abrir o menu.')
        if target.kind in {'anime','legacy_lookup'}:return await browse(update,context,'anime',target.value)
        if target.kind=='search':return await browse(update,context,'search',target.value)
        if target.kind=='shortcut':return await browse(update,context,'shortcut',target.value)
        return await fail(update,'Este link pertence a uma etapa ainda não migrada. Player, sagas e feedback continuam nos bots atuais; esta é uma fundação de testes com catálogo.')
    await fail(update,'👑 OmniKing | Catálogo de testes\n\n/buscar nome — buscar no acervo\n/alfabeto — catálogo completo\n/recentes — inclusões pelo ID legado\n/recomendar — sugestão\n/ajuda — comandos e filtros')

async def help_command(update,context):
    await fail(update,'/buscar ou /busca — nome, tag ou estúdio\nFiltros: dub, leg, ano (2024, >=2020), classificação (=16, <=14). Termos combinados usam E.\n'
        '/alfabeto — lista paginada pelo nome de exibição\n/atalhos A, NUM ou PROIBIDOS — listas filtradas\n/recentes — data codificada no ID legado\n/recomendar [filtros] — sugestão aleatória\n/anime ID — ficha\n'
        '/health — bot ativo\n/status — diagnóstico privado do administrador\n\nVIP e banimento são conferidos no servidor. Player, sagas, favoritos e perfil do bot serão migrados nas próximas etapas. O Hub mantém suas funções atuais.')
