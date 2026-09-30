import random
import re
import secrets
import time
from telegram import InlineKeyboardButton as Button, InlineKeyboardMarkup as Markup
from modules.catalog import card, display, letter, ordered, recent, safe_url, search
from modules.catalog_client import CatalogError
from kingcore.security import is_private_admin

PAGE_SIZE=8
SESSION_TTL=600

async def snapshot(update,context):
    user=update.effective_user
    if not user or user.is_bot:raise CatalogError('Abra o bot com sua conta Telegram.')
    return await context.application.bot_data['catalog'].read(user.id)

async def fail(update,message):
    if update.effective_message:await update.effective_message.reply_text(message)

def save_session(update,context,rows,title):
    key=secrets.token_hex(4)
    actor=update.effective_user.id
    context.application.bot_data['catalog_sessions'].put((actor,key),{'created':time.monotonic(),'ids':[r['id'] for r in rows],'title':title[:150]})
    return key

async def page(update,context,key,number,rows):
    state=context.application.bot_data['catalog_sessions'].get((update.effective_user.id,key))
    if not state or time.monotonic()-state['created']>=SESSION_TTL:
        return await fail(update,'Esta lista expirou. Faça a busca novamente.')
    available={r['id']:r for r in rows}
    ids=[i for i in state['ids'] if i in available]
    pages=max(1,(len(ids)+PAGE_SIZE-1)//PAGE_SIZE)
    number=min(max(0,number),pages-1)
    visible=ids[number*PAGE_SIZE:(number+1)*PAGE_SIZE]
    buttons=[]
    for i in visible:
        # Tokens are per verified user; a forwarded button cannot expose another user's result.
        buttons.append([Button(display(available[i])[:55],callback_data=f'ok:c:{key}:{state["ids"].index(i)}')])
    navigation=[]
    if number>0:navigation.append(Button('⬅️',callback_data=f'ok:p:{key}:{number-1}'))
    if number+1<pages:navigation.append(Button('➡️',callback_data=f'ok:p:{key}:{number+1}'))
    if navigation:buttons.append(navigation)
    text=f'{state["title"]}\n{len(ids)} resultado(s) · Página {number+1}/{pages}'
    if not ids:text+='\nNenhum anime disponível para esta consulta.'
    await update.effective_message.reply_text(text,reply_markup=Markup(buttons) if buttons else None)

async def results(update,context,rows,title):
    await page(update,context,save_session(update,context,rows,title),0,rows)

async def show_card(update,context,rows,anime_id):
    row=next((r for r in rows if r['id']==anime_id),None)
    if not row:return await fail(update,'Anime não encontrado ou indisponível para esta conta.')
    buttons=[]
    for field,label in [('link_leg','LEG'),('link_dub','DUB')]:
        url=safe_url(row.get(field))
        if url:buttons.append(Button(label,url=url))
    player=context.application.bot_data['catalog'].config.player_username
    if re.fullmatch(r'[A-Za-z0-9_-]{1,64}',row['id']):
        buttons.append(Button('Abrir player atual',url=f'https://t.me/{player}?start={row["id"]}'))
    await update.effective_message.reply_text(card(row),parse_mode='HTML',
        reply_markup=Markup([buttons]) if buttons else None,disable_web_page_preview=True)

async def browse(update,context,mode='search',value=None):
    try:
        rows=await snapshot(update,context)
        text=' '.join(context.args) if value is None else value
        if mode=='search':
            if not text:return await fail(update,'Use /buscar nome, tag, estúdio, dub, leg ou ano. Ex.: /buscar ação dub >=2020')
            await results(update,context,search(rows,text),'Busca: '+text[:100])
        elif mode=='recent':await results(update,context,recent(rows),'Recentes · data codificada no ID legado')
        elif mode=='recommend':
            matches=search(rows,text) if text else rows
            if not matches:return await fail(update,'Nenhum anime disponível para recomendar com esses filtros.')
            await show_card(update,context,rows,random.choice(matches)['id'])
        elif mode=='anime':await show_card(update,context,rows,text)
        elif mode=='shortcut':
            key=text.upper()
            if key not in tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')+('NUM','PROIBIDOS'):
                return await fail(update,'Use /atalhos A, /atalhos NUM ou /atalhos PROIBIDOS.')
            matches=[r for r in rows if (r.get('proibido') in (1,True,'1') if key=='PROIBIDOS' else letter(r)==key)]
            await results(update,context,ordered(matches),'Atalho: '+key)
        else:await results(update,context,ordered(rows),'Catálogo · ordem alfabética')
    except CatalogError as exc:await fail(update,str(exc))

async def search_command(update,context):await browse(update,context)
async def alphabet(update,context):await browse(update,context,'alphabet')
async def shortcut(update,context):await browse(update,context,'shortcut')
async def recent_command(update,context):await browse(update,context,'recent')
async def recommend(update,context):await browse(update,context,'recommend')
async def anime(update,context):await browse(update,context,'anime')

async def callback(update,context):
    query=update.callback_query
    await query.answer()
    if not update.effective_message:return
    try:
        _,action,key,value=query.data.split(':')
        state=context.application.bot_data['catalog_sessions'].get((update.effective_user.id,key))
        if not state or time.monotonic()-state['created']>=SESSION_TTL:
            return await fail(update,'Esta lista expirou. Faça a busca novamente.')
        rows=await snapshot(update,context)
        number=int(value)
        if action=='p':await page(update,context,key,number,rows)
        elif action=='c' and 0<=number<len(state['ids']):await show_card(update,context,rows,state['ids'][number])
        else:await fail(update,'Botão inválido. Faça a busca novamente.')
    except CatalogError as exc:await fail(update,str(exc))
    except (ValueError,KeyError):await fail(update,'Botão inválido. Faça a busca novamente.')

async def catalog_status(update,context):
    settings=context.application.bot_data['settings']
    if not is_private_admin(update,settings):return await fail(update,'Diagnóstico disponível somente ao administrador no privado.')
    try:
        rows=await snapshot(update,context)
        message=f'API do Hub: disponível · {len(rows)} animes visíveis para sua conta.'
    except CatalogError as exc:message=str(exc)
    await fail(update,'OmniKing 0.2.0-dev1\nTelegram: conectado\n'+message+'\nCatálogo: migrado para testes. Player e gestão: pendentes.')
