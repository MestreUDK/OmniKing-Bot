import html
import operator
import re
import unicodedata
from datetime import date
from urllib.parse import urlsplit

def folded(value):
    value=unicodedata.normalize('NFKD',str(value or '').casefold())
    return ''.join(c for c in value if not unicodedata.combining(c))

def display(row):return str(row.get('nome_exibicao') or row.get('nome') or row['id'])
def ordered(rows):return sorted(rows,key=lambda r:(folded(display(r)),r['id']))
def letter(row):
    first=folded(display(row))[:1].upper()
    return 'NUM' if first.isdigit() else first

def search(rows,text):
    tokens=folded(text).split()
    terms=[];filters=[]
    compare={'=':operator.eq,'>':operator.gt,'<':operator.lt,'>=':operator.ge,'<=':operator.le}
    for token in tokens:
        if token in {'dub','dublado','leg','legendado'}:
            filters.append(('audio',token[:3]));continue
        match=re.fullmatch(r'(>=|<=|>|<|=)?(\d{4}|1[0-8]|0|[0-9])',token)
        if match:
            number=int(match[2]);field='ano' if len(match[2])==4 else 'classificacao'
            filters.append((field,compare[match[1] or '='],number));continue
        terms.append(token.lstrip('#'))
    result=[]
    for row in rows:
        bag=folded(' '.join(str(row.get(k) or '') for k in ('nome','nome_exibicao','descricao','apelidos','tags','estudio')))
        if not all(term in bag for term in terms):continue
        valid=True
        for item in filters:
            if item[0]=='audio':
                audio=folded(row.get('audio'))
                if item[1] not in audio and not row.get('link_'+item[1]):valid=False
            else:
                value=row.get(item[0]);m=re.search(r'\d+',str(value))
                if not m or not item[1](int(m[0]),item[2]):valid=False
        if valid:result.append(row)
    return ordered(result)

def recent(rows):
    def key(row):
        match=re.fullmatch(r'[A-Za-z](\d{2})-(\d{2})(\d{2})\d?',row['id'])
        try:d=date(2000+int(match[1]),int(match[2]),int(match[3])) if match else date.min
        except ValueError:d=date.min
        return d,row['id']
    return sorted(rows,key=key,reverse=True)

def safe_url(value):
    if not isinstance(value,str) or len(value)>2048 or any(c.isspace() or ord(c)<32 for c in value):return None
    try:p=urlsplit(value)
    except ValueError:return None
    if p.scheme not in {'http','https'} or not p.hostname or p.username or p.password:return None
    if p.hostname=='api.telegram.org':return None
    return value

def card(row):
    esc=lambda x:html.escape(str(x or ''),quote=False)
    lines=[f'<b>{esc(display(row)[:200])}</b>',f'ID: <code>{esc(row["id"][:200])}</code>']
    if display(row)!=str(row.get('nome') or '') and row.get('nome'):lines.append(esc(row['nome'][:200]))
    for field,label in [('ano','Ano'),('classificacao','Classificação'),('temporadas','Temporadas'),('audio','Áudio')]:
        if row.get(field) is not None and row.get(field)!='':lines.append(f'{label}: {esc(str(row[field])[:100])}')
    for field,label in [('estudio','Estúdio'),('tags','Tags')]:
        value=row.get(field)
        if value:lines.append(label+': '+esc((', '.join(map(str,value)) if isinstance(value,list) else str(value))[:300]))
    if row.get('proibido') in (1,True,'1'):lines.append('🔒 Acervo VIP')
    if row.get('descricao'):lines.append('\n'+esc(str(row['descricao'])[:1800]))
    return '\n'.join(lines)
