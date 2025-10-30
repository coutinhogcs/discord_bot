# Jobot — Bot de Discord com Google AI (Gemini)

Um bot de Discord focado em ajudar pessoas a encontrarem vagas de emprego no Brasil, dar dicas de currículo e compartilhar links úteis. Ele usa a API Google AI (Gemini) para gerar respostas e pode responder no canal diretamente ou via Webhook (opcional).

## ✨ Recursos
- Persona configurada para temas de emprego (vagas, currículo, sites de carreira)
- Comando de conversa por menção ao bot (padrão); opcionalmente pode ser alterado para prefixo
- Envio da resposta no canal; Webhook opcional com fallback automático
- Comando de moderação para limpar mensagens: `!limpar [quantidade|tudo]`
  - Requer permissões de administrador ou "Gerenciar Mensagens"
  - O bot também precisa de "Gerenciar Mensagens" no canal
- Divisão automática de mensagens longas (2000+ caracteres)

## 📁 Estrutura
- `main.py`: código do bot
- `.venv/`: ambiente virtual Python (local)
- `requirements.txt`: dependências com versões

## 🚀 Começando

### 1) Pré‑requisitos
- Python 3.11+ (recomendado 3.13 já suportado neste projeto)
- Uma aplicação/bot no Discord com o Intent "Message Content" ativado
- Uma chave da Google AI (Gemini)

### 2) Criar o ambiente
```bash
# Windows PowerShell (no diretório do projeto)
py -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 3) Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto com os campos abaixo. Não compartilhe suas chaves.
```env
# Token do bot do Discord
DISCORD_BOT_TOKEN=coloque_seu_token_aqui

# URL do Webhook (opcional). Se não definir, o bot responde no canal.
DISCORD_WEBHOOK_URL=coloque_sua_url_de_webhook_ou_deixe_vazio

# Chave da Google AI (Gemini)
GOOGLE_API_KEY=coloque_sua_chave_aqui
```

> Dica: se não quiser usar Webhook, basta deixar `DISCORD_WEBHOOK_URL` vazio. O bot responderá usando `message.channel.send(...)`.

### 4) Executar
```bash
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python .\main.py
```
Você deve ver algo como: "Bot está logado como Jobot#XXXX e pronto para interagir como Agente Serb.".

## 💬 Como usar
- Conversa: mencione o bot no canal e faça sua pergunta
  - Ex.: `@Jobot Quais são os melhores sites de emprego?`
- Resetar contexto: `!reset`
- Limpar mensagens: `!limpar [quantidade|tudo]`
  - `!limpar 25` apaga 25 mensagens recentes (+ a do comando)
  - `!limpar tudo` apaga todas as mensagens que a API do Discord permitir

> Observação: o Discord não permite apagar em massa mensagens mais antigas que 14 dias.

## ⚙️ Detalhes técnicos
- O bot cria um chat Gemini com `genai.Client().chats.create(...)` e mantém o histórico.
- Envio por Webhook é assíncrono (aiohttp) e possui fallback: se ocorrer erro, a resposta é enviada diretamente no canal.

## 🧪 Solução de problemas
- 400 Bad Request no Webhook:
  - Verifique se o Webhook não foi revogado e se pertence ao canal/threads corretos
  - O conteúdo não pode ser vazio e tem limite de 2000 caracteres (o bot já divide)
  - Se persistir, deixe `DISCORD_WEBHOOK_URL` vazio e use envio direto no canal
- "Heartbeat blocked":
  - O envio por Webhook é assíncrono para não travar o loop; use esta versão do código
- ImportError de pacotes:
  - Reinstale no `.venv`: `.\\.venv\\Scripts\\python -m pip install -r requirements.txt`

## 🔐 Segurança
- Nunca comite seu `.env` ou poste suas chaves publicamente
- As variáveis sensíveis são lidas via `python-dotenv`

## 📜 Licença
Projeto para uso pessoal/demonstrativo. Adapte conforme suas necessidades.
