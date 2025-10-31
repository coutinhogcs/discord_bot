# Jobot — Bot de Discord com Google AI (Gemini)

Um bot de Discord focado em ajudar pessoas a encontrarem vagas de emprego no Brasil, dar dicas de currículo e compartilhar links úteis. Ele usa a API Google AI (Gemini) para gerar respostas e funciona **sem necessidade de Webhook**, respondendo diretamente em qualquer canal do servidor.

## ✨ Recursos
- Persona configurada para temas de emprego (vagas, currículo, sites de carreira)
- Comandos de barra (Slash Commands): `/serb` para conversar e `/resetar` para limpar histórico
- **Funciona sem Webhook** - responde diretamente no canal onde foi chamado
- Disponível em todos os canais do servidor onde o bot está
- Histórico de conversa individual por usuário (suporta múltiplos usuários simultaneamente)
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
# Token do bot do Discord (OBRIGATÓRIO)
DISCORD_BOT_TOKEN=coloque_seu_token_aqui

# Chave da Google AI (Gemini) (OBRIGATÓRIO)
GOOGLE_API_KEY=coloque_sua_chave_aqui

# URL do Webhook (OPCIONAL - pode deixar vazio ou remover esta linha)
# O bot funciona perfeitamente sem webhook, respondendo diretamente no canal
DISCORD_WEBHOOK_URL=
```

### 4) Executar
```bash
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python .\main.py
```
Você deve ver algo como: "Bot está logado como Jobot#XXXX e pronto para interagir como Agente Serb.".

## 💬 Como usar
- **Conversar com o bot**: Use o comando de barra `/serb` em qualquer canal
  - Ex.: `/serb Quais são os melhores sites de emprego?`
  - O bot responderá diretamente no canal onde você usou o comando
- **Limpar seu histórico**: Use `/resetar` para apagar seu histórico de conversa com o bot
- **Limpar mensagens do canal**: `!limpar [quantidade|tudo]` (apenas administradores)
  - `!limpar 25` apaga 25 mensagens recentes (+ a do comando)
  - `!limpar tudo` apaga todas as mensagens que a API do Discord permitir

> Observação: o Discord não permite apagar em massa mensagens mais antigas que 14 dias.

## ⚙️ Detalhes técnicos
- O bot cria um chat Gemini com `genai.Client().chats.create(...)` e mantém o histórico individual por usuário
- **O bot funciona sem Webhook** - responde diretamente no canal usando `channel.send()`
- Cada usuário tem seu próprio histórico de conversa (suporta múltiplos usuários simultaneamente)
- Comandos de barra (Slash Commands) são sincronizados automaticamente na inicialização

## 🧪 Solução de problemas
- **Bot não responde**: Verifique se os comandos `/serb` e `/resetar` aparecem ao digitar `/` no Discord
  - Se não aparecerem, aguarde alguns segundos após iniciar o bot (sincronização pode demorar)
  - Certifique-se de que o bot tem permissão para "Enviar Mensagens" no canal
- **"ImportError" de pacotes**:
  - Reinstale no `.venv`: `.\\.venv\\Scripts\\python -m pip install -r requirements.txt`
- **Token inválido**:
  - Verifique se `DISCORD_BOT_TOKEN` no `.env` está correto
  - Certifique-se de que o Intent "Message Content" está ativado no Discord Developer Portal

## 🔐 Segurança
- Nunca comite seu `.env` ou poste suas chaves publicamente
- As variáveis sensíveis são lidas via `python-dotenv`

## 📜 Licença
Projeto para uso pessoal/demonstrativo. Adapte conforme suas necessidades.
