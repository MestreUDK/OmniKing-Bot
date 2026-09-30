# OmniKing 0.1.0-dev1

Fundação de testes do ecossistema AniKing, de Vinícius Oliveira Moraes.
Este diretório é independente e pode ser a raiz do repositório `OmniKing`.

**Esta versão ainda não substitui os bots atuais.** Contém inicialização,
configuração, tratamento de erros, cache local e diagnóstico. Não contém
catálogo, player, perfil nem operações de gestão do acervo.
O OmniKing contém somente rotas iniciais públicas e diagnóstico privado do administrador. Nenhum comando de cadastro, edição ou broadcast é registrado.

## Executar localmente

Use Python 3.12. No terminal, dentro deste diretório:

```sh
python -m venv .venv
```

Linux/macOS:

```sh
.venv/bin/python -m pip install -r requirements.lock.txt
cp .env.example .env
.venv/bin/python diagnostics.py
.venv/bin/python bot.py
```

Windows (PowerShell):

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
Copy-Item .env.example .env
.venv\Scripts\python.exe diagnostics.py
.venv\Scripts\python.exe bot.py
```

**Antes de executar diagnostics.py e bot.py**, preencha `.env` com o BOT_TOKEN
de um bot novo de testes e seu ADMIN_IDS numérico. Cada projeto precisa de
um token próprio. Não execute uma segunda instância usando o token de um bot
ativo. Nenhuma mensagem é enviada automaticamente ao administrador na inicialização.

SUPABASE_URL e SUPABASE_KEY podem ficar vazios nesta etapa. Quando ambos
estiverem configurados, `/status` faz uma consulta sem retornar registros de
`animes`. O comando local `python diagnostics.py --database` também faz essa
consulta. Sem essa opção, diagnostics.py não se conecta a serviços externos.
Uma resposta da API não comprova acesso aos dados, RLS correta ou schema completo.

OmniKing rejeita chaves sb_secret_ e JWT com role service_role. Isso é somente uma barreira de configuração; a autorização real depende das políticas do banco. Uma chave publishable/anon não representa automaticamente o usuário do Telegram. Não afrouxe RLS para fazer o teste passar.

## Comandos presentes

- `/start`: tela inicial.
- `/ajuda` ou `/help`: orientações.
- `/health`: verifica resposta do processo, sem consultar Supabase.
- `/status`: diagnóstico apenas para administrador no privado.
- Payloads de `/start` são analisados, mas ainda não abrem animes ou episódios. A resposta deixa essa limitação explícita.

## Testes locais

```sh
python -m unittest discover -s tests -v
```

Execute com o Python do ambiente virtual. Os testes usam o roteador real da
biblioteca Telegram com transporte simulado. Não precisam de `.env`, tokens
reais, Telegram nem banco remoto.

## Discloud e GitHub

`discloud.config` aponta para `bot.py`, Python 3.12 e 180 MB como ponto de
partida; o consumo precisará ser medido após migrar os domínios. O perfil de
implantação ainda não foi exercitado na Discloud.

Envie o **conteúdo desta pasta** como raiz do novo repositório. `.env` fica
ignorado pelo Git. Para um pacote privado de implantação, inclua seu `.env`
configurado se a hospedagem não injetar as variáveis. `.discloudignore` permite
esse arquivo para a implantação, mas não o inclua no repositório ou em pacotes
públicos. O pacote entregue vem sem credenciais.

`kingcore/` é uma cópia versionada do núcleo desta etapa. Os dois repositórios
funcionam sem instalar um ao outro; correções no núcleo devem ser aplicadas aos
dois até que seja extraído como pacote comum. Nenhum código importa os bots legados.

## Próximo marco

Migrar busca, alfabeto, recentes, recomendação e visualização, mantendo as verificações VIP/ban/inscrição.

Consulte a pasta `docs/` do pacote principal para inventário, divergências do
plano, consulta SQL de diagnóstico e critérios de aceite.
