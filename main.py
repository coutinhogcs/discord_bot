import os
import discord
import requests
import aiohttp
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

# --- Configuração de Variáveis de Ambiente ---
load_dotenv() # Carrega o .env (incluindo GOOGLE_API_KEY)
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# A GOOGLE_API_KEY é lida automaticamente pela biblioteca genai

# --- Configuração Global da LLM (Usando SUA configuração do AI Studio) ---

# 1. Definição da Persona/Instrução do Sistema
SYSTEM_INSTRUCTION_TEXT = """
Você é um agente de uma comunidade digital que passa informações sobre sites de emprego no brasil. O nome dessa comunidade é Serb.
Você vai dar informações sobre vaga, informações de como melhorar o curriculo e tudo que ajude a uma pessoa conseguir o seu emprego.
Você poderá responder enviando links de sites que publicam vagas como gupy, linkedin, glassdor, programathor entre outros.
Você irá procurar na internet como e formar currículos que esses próprios sites leem e colocam em primeiro lugar.
Você vai tirar qualquer dúvida de vaga sempre que possivel.
Você deve responder de forma agradável sempre que alguem perguntar de forma neutra ou agradável. E sempre que houver agressividade você deve responder de forma empática. Nos dois casos deve sempre adicionar emoji as resposta.
Sempre que for solicitado que você encontre vaga de algo, como back end você deve enviar um link onde já ache a página com vagas backend do site requisitado.
Você deve apenas se ater no quesito emprego.
"""

# 2. Definição da Configuração de Geração (temperatura, tools, system_instruction)
GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=2,
    tools=[types.Tool(googleSearch=types.GoogleSearch())],
    system_instruction=[types.Part.from_text(text=SYSTEM_INSTRUCTION_TEXT)],
)



# --- Inicialização da API e Chat ---
# O Client lê a GOOGLE_API_KEY do ambiente
client_ai = genai.Client()

# Variável Global para Manter o Contexto (Histórico)
global gemini_chat

# Criar chat usando o client com modelo e config
gemini_chat = client_ai.chats.create(model='gemini-2.5-pro', config=GENERATION_CONFIG)


# --- Funções Auxiliares de Discord e Webhook ---

def _split_discord_message(text: str, chunk_size: int = 2000):
    if text is None:
        return []
    s = str(text)
    return [s[i:i+chunk_size] for i in range(0, len(s), chunk_size)] or [""]


async def send_webhook_message(webhook_url: str, content: str, username: str = "Agente Serb (Gemini AI)", avatar_url: str = None):
    """Envia mensagem via Webhook de forma assíncrona; retorna True se ok."""
    safe_content = (content or "").strip()
    if not safe_content:
        print("Aviso: conteúdo vazio; envio via Webhook ignorado.")
        return False

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            for chunk in _split_discord_message(safe_content):
                payload = {
                    "content": chunk,
                    "username": username,
                    "avatar_url": avatar_url,
                }
                async with session.post(webhook_url, json=payload) as resp:
                    if resp.status < 200 or resp.status >= 300:
                        text = await resp.text()
                        print(f"Erro Webhook HTTP {resp.status}: {text}")
                        return False
    except Exception as e:
        print(f"Erro ao enviar mensagem via Webhook (async): {e}")
        return False
    return True

# --- Configuração e Eventos do Discord Bot ---

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot está logado como {client.user} e pronto para interagir como Agente Serb.')

@client.event
async def on_message(message):
    global gemini_chat

    if message.author == client.user:
        return

    # 0. Comando de moderação: limpar mensagens (admins)
    if message.content.lower().startswith("!limpar"):
        # Bloqueia DMs
        if message.guild is None:
            await message.channel.send("Este comando só pode ser usado em servidores.")
            return

        # Verifica permissões do autor (admin ou gerenciar mensagens)
        author_perms = message.author.guild_permissions
        if not (author_perms.administrator or author_perms.manage_messages):
            await message.channel.send("❌ Você não tem permissão para apagar mensagens.")
            return

        # Verifica permissões do bot
        me = message.guild.me
        if me is None:
            me = await message.guild.fetch_member(client.user.id)
        bot_perms = message.channel.permissions_for(me)
        if not bot_perms.manage_messages:
            await message.channel.send("❌ Eu não tenho permissão de 'Gerenciar Mensagens' neste canal.")
            return

        # Parse da quantidade
        parts = message.content.split()
        limit_to_use = None  # None = apagar todas as mensagens disponíveis
        if len(parts) > 1:
            arg = parts[1].lower()
            if arg in ("tudo", "all", "*"):
                limit_to_use = None
            else:
                try:
                    qty = int(arg)
                except ValueError:
                    await message.channel.send("Uso: !limpar [quantidade|tudo]")
                    return
                # Limites básicos (se número fornecido)
                if qty < 1:
                    qty = 1
                limit_to_use = qty + 1  # inclui a mensagem do comando

        # Executa o purge (None = tudo, número = quantidade)
        deleted = await message.channel.purge(limit=limit_to_use)
        # Confirmação rápida
        confirm_text = f"🧹 Apaguei {max(len(deleted) - 1, 0)} mensagem(ns)."
        notice = await message.channel.send(confirm_text)
        # Remove a confirmação após alguns segundos para não poluir
        try:
            import asyncio
            await asyncio.sleep(3)
            await notice.delete()
        except Exception:
            pass
        return

    # 1. Comando de Reset
    if message.content.lower().strip() == "!reset":
        # Recriar chat com a mesma configuração
        gemini_chat = client_ai.chats.create(model='gemini-2.5-pro', config=GENERATION_CONFIG)
        await message.channel.send("✅ Histórico de conversa com o Agente Serb limpo! Podemos começar um novo tópico sobre empregos.")
        return

    # 2. Comando de Conversação (só se for mencionado)
    if client.user.mentioned_in(message):
        
        prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
        
        if not prompt:
            await message.channel.send("👋 Olá! Sou o Agente Serb. Pergunte-me sobre vagas de emprego, currículos ou sites de carreira.")
            return

        async with message.channel.typing():
            try:
                response = gemini_chat.send_message(prompt)
                gemini_text = response.text
                
                sent = False
                if WEBHOOK_URL:
                    sent = await send_webhook_message(WEBHOOK_URL, gemini_text)
                if not sent:
                    for part in _split_discord_message(gemini_text):
                        await message.channel.send(part)

            except APIError as e:
                print(f"Erro da API Gemini: {e}")
                await message.channel.send("❌ Desculpe, houve um erro ao processar sua solicitação no Gemini.")
            except Exception as e:
                print(f"Erro geral: {e}")
                await message.channel.send("⚠️ Ocorreu um erro inesperado. Verifique os logs.")


# --- Iniciar o Bot ---
# CORREÇÃO DO BUG 2: Verificar as chaves corretas
GOOGLE_API_KEY_LOADED = os.getenv("GOOGLE_API_KEY")

if DISCORD_TOKEN and WEBHOOK_URL and GOOGLE_API_KEY_LOADED:
    try:
        client.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("ERRO: O Token do Discord é inválido. Verifique o seu .env.")
    except Exception as e:
        print(f"Ocorreu um erro ao iniciar o bot: {e}")
else:
    print("ERRO: Uma das chaves (.env) está faltando. Verifique se todas existem:")
    if not DISCORD_TOKEN: print("- DISCORD_BOT_TOKEN não encontrada.")
    if not WEBHOOK_URL: print("- DISCORD_WEBHOOK_URL não encontrada.")
    if not GOOGLE_API_KEY_LOADED: print("- GOOGLE_API_KEY não encontrada (lembre-se, o nome mudou!).")