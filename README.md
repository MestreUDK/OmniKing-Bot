# OmniKing 0.2.0-dev1

Bot público com catálogo inicial. Diretório independente para o novo repositório.
Não substitui ainda os bots de produção: player, sagas e funções sociais estão pendentes.

## Configuração e execução

Python 3.12. Crie ambiente virtual, instale requirements.lock.txt e copie
.env.example para .env. No Linux/macOS:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
cp .env.example .env
.venv/bin/python diagnostics.py
.venv/bin/python bot.py
```

No Windows use .venv\Scripts\python.exe e Copy-Item .env.example .env.
Preencha BOT_TOKEN de um novo bot de testes e ADMIN_IDS. Configure CATALOG_API_URL
como origem HTTPS do backend Hub e OMNIKING_API_SECRET igual ao segredo do servidor.
LEGACY_PLAYER_USERNAME recebe o username do player atual. Mantenha SUPABASE_URL/KEY
vazios; não coloque service_role no OmniKing. Sem a ponte configurada, /start e
/health respondem e o catálogo informa que precisa de configuração.

diagnostics.py não acessa serviços por padrão. --catalog faz uma leitura da API
como o primeiro administrador da lista; exige acesso ao Hub/canal, não altera dados.
--database permanece apenas como probe legado de leitura direta, sem validar RLS.
/status consulta a API de catálogo somente para admin no privado.

## Catálogo presente

/buscar (/busca), /alfabeto, /atalhos A|NUM|PROIBIDOS, /recentes, /recomendar [filtros]
e /anime ID. Deep links anime_, busca_/buscar_, atalhos_ e IDs legados de anime
abrem consultas. Cada consulta/callback verifica autorização no Hub. Nenhum comando
administrativo de cadastro, edição, exclusão ou comunicação em massa é registrado.

Filtros de busca: dub/leg, ano (=2024, >=2020) e classificação (=16, <=14). Termos
com acentos são normalizados; nome, AB/aliases, sinopse, tags e estúdio entram na
busca. Termos combinados exigem todos os termos. Busca fuzzy/inline, capas no bot,
botões extras e avaliações ainda pendentes. Ficha mantém links LEG/DUB e abertura
do player atual; não entrega episódios nem usa file_id de outro bot.

Recentes usa a data do ID legado; IDs customizados sem data vêm depois. AB define
nome curto da listagem, quando presente. Paginação de 8 itens; cache de sessões
limitado a 128 listas, TTL 10 minutos, sem persistência entre reinícios.

## Testes e implantação

```sh
python -m unittest discover -s tests -v
```

Banco/API/Telegram são simulados. README principal e docs/06_SCHEMA_E_TESTE_CATALOGO.md
explicam o aceite remoto. Discloud aponta para bot.py, Python 3.12; memória e carga
precisam de medição com o catálogo real. Envie o conteúdo desta pasta como raiz do
repositório. .env não vai para Git ou pacote público. Se a hospedagem não injeta
variáveis, inclua .env apenas no pacote privado de implantação.

kingcore é versionado em cópias idênticas nos dois bots. Não há import do legado.
O próximo marco inclui equivalência do catálogo e migração de social/player; a
dependência do backend Hub poderá ser extraída para serviço comum posteriormente.
