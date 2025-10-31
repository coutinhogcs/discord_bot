import os
import discord
import requests
import aiohttp
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
import asyncio # MUDANÇA: Importado para o !limpar funcionar corretamente

# --- Configuração de Variáveis de Ambiente ---
load_dotenv() # Carrega o .env (incluindo GOOGLE_API_KEY)
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GOOGLE_API_KEY_LOADED = os.getenv("GOOGLE_API_KEY") # MUDANÇA: Lendo a chave correta para verificação

# --- Configuração Global da LLM (Usando SUA configuração do AI Studio) ---

# 1. Definição da Persona/Instrução do Sistema
SYSTEM_INSTRUCTION_TEXT = """
Você é um agente de uma comunidade digital que passa informações sobre sites de emprego no brasil. O nome dessa comunidade é Serb.
Você vai dar informações sobre vaga, informações de como melhorar o curriculo e tudo que ajude a uma pessoa conseguir o seu emprego.
Você poderá responder enviando links de sites que publicam vagas como gupy, linkedin, glassdor, programathor entre outros.
Você irá procurar na internet como e formar currículos que esses próprios sites leem e colocam em primeiro lugar.
Você vai tirar qualquer dúvida de vaga sempre que possivel.
Você deve responder de forma agradável sempre que alguem perguntar de forma neutra ou agradável. E sempre que houver agressividade você deve responder de forma empática. Nos dos casos deve sempre adicionar emoji as resposta.
Sempre que for solicitado que você encontre vaga de algo, como back end você deve enviar um link onde já ache a página com vagas backend do site requisitado.
Você deve apenas se ater no quesito emprego.
Você deve ler pdfs e montar em forma de texto melhorias para o currículos das pessoas.
"""

# 2. Definição da Configuração de Geração (temperatura, tools, system_instruction)
GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=2,
    tools=[types.Tool(googleSearch=types.GoogleSearch())],
    system_instruction=[types.Part.from_text(text=SYSTEM_INSTRUCTION_TEXT)],
)



# --- Inicialização da API ---
client_ai = genai.Client()


# --- MUDANÇA: Gerenciamento de Histórico (Escalável) ---
# Dicionário global para armazenar chats. A chave é o user_id.
# Substitui o 'global gemini_chat' para que 100 pessoas possam falar ao mesmo tempo
chat_histories = {}

def get_or_create_chat(user_id: int):
    """
    Pega o histórico de chat de um usuário. Se não existir, cria um novo.
    """
    if user_id not in chat_histories:
        print(f"Criando novo histórico de chat para o usuário {user_id}")
        # MUDANÇA: Corrigido para usar a sua sintaxe de criação de chat
        chat_histories[user_id] = client_ai.chats.create(model='gemini-2.5-pro', config=GENERATION_CONFIG)
    
    return chat_histories[user_id]

def reset_chat(user_id: int):
    """
    Apaga o histórico de chat de um usuário.
    """
    if user_id in chat_histories:
        del chat_histories[user_id]
        print(f"Histórico de chat resetado para o usuário {user_id}")
        return True
    return False

# --- Funções Auxiliares de Discord e Webhook (Seu código, sem alteração) ---

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

# --- Configuração do Discord Bot (Nova Estrutura) ---

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

# MUDANÇA: ...e ligamos ele a uma 'CommandTree'
# Esta 'tree' é o que gerencia os comandos de barra
tree = discord.app_commands.CommandTree(client)


# --- MUDANÇA: Evento de Inicialização (Sincroniza os comandos de barra) ---
@client.event
async def on_ready():
    # Sincroniza a árvore de comandos com o Discord
    await tree.sync() 
    print(f'Bot está logado como {client.user} e pronto para interagir como Agente Serb.')
    print(f'Comandos de barra sincronizados. ({len(await tree.fetch_commands())} comandos)')


# --- MUDANÇA: NOVOS Comandos de Barra (/serb e /resetar) ---

# Comando /serb (Esta é a mudança que você pediu de @jobot para /serb)
@tree.command(name="serb", description="Faça qualquer pergunta para o Agente Serb (Gemini AI)")
async def chat_command(interaction: discord.Interaction, *, pergunta: str):
    """
    Este é o comando principal que substitui a @menção.
    'pergunta' é o argumento obrigatório que o usuário digita.
    """
    
    # Resposta inicial ("thinking...") - 'ephemeral=True' (só o usuário vê)
    await interaction.response.defer(thinking=True, ephemeral=True)
    
    user_id = interaction.user.id
    
    try:
        # Pega o histórico correto (ou cria um novo)
        gemini_chat = get_or_create_chat(user_id)
        
        # Envia a pergunta para o Gemini
        response = gemini_chat.send_message(pergunta)
        gemini_text = response.text
        
        # Envia a resposta diretamente no canal (sem webhook necessário)
        for part in _split_discord_message(gemini_text):
            await interaction.channel.send(part)

        # Avisa o usuário que a resposta foi enviada
        await interaction.followup.send("✅ Sua pergunta foi respondida no canal.", ephemeral=True)

    except APIError as e:
        print(f"Erro da API Gemini: {e}")
        await interaction.followup.send("❌ Desculpe, houve um erro ao processar sua solicitação no Gemini.", ephemeral=True)
    except Exception as e:
        print(f"Erro geral: {e}")
        await interaction.followup.send("⚠️ Ocorreu um erro inesperado. Verifique os logs.", ephemeral=True)


# Comando /resetar
@tree.command(name="resetar", description="Limpa seu histórico de conversa com o Agente Serb")
async def reset_command(interaction: discord.Interaction):
    
    user_id = interaction.user.id
    if reset_chat(user_id):
        await interaction.response.send_message("✅ Seu histórico de conversa foi limpo!", ephemeral=True)
    else:
        await interaction.response.send_message("ℹ️ Você não tinha um histórico de conversa ativo.", ephemeral=True)


# --- MUDANÇA: on_message agora cuida APENAS do !limpar ---
@client.event
async def on_message(message):
    
    if message.author == client.user:
        return

    # 0. Comando de moderação: !limpar (Seu código original, sem alteração)
    if message.content.lower().startswith("!limpar"):
        if message.guild is None:
            await message.channel.send("Este comando só pode ser usado em servidores.")
            return
        
        author_perms = message.author.guild_permissions
        if not (author_perms.administrator or author_perms.manage_messages):
            await message.channel.send("❌ Você não tem permissão para apagar mensagens.")
            return

        me = message.guild.me
        if me is None:
            me = await message.guild.fetch_member(client.user.id)
        bot_perms = message.channel.permissions_for(me)
        
        if not bot_perms.manage_messages:
            await message.channel.send("❌ Eu não tenho permissão de 'Gerenciar Mensagens' neste canal.")
            return

        parts = message.content.split()
        limit_to_use = None
        if len(parts) > 1:
            arg = parts[1].lower()
            if arg not in ("tudo", "all", "*"):
                try:
                    qty = int(arg)
                    limit_to_use = (qty + 1) if qty >= 1 else 2
                except ValueError:
                    await message.channel.send("Uso: !limpar [quantidade|tudo]")
                    return
        
        try:
            deleted = await message.channel.purge(limit=limit_to_use)
            confirm_text = f"🧹 Apaguei {max(len(deleted) - 1, 0)} mensagem(ns)."
            notice = await message.channel.send(confirm_text)
            await asyncio.sleep(3)
            await notice.delete()
        except Exception as e:
            print(f"Erro ao limpar mensagens: {e}")
        return

    # MUDANÇA: Toda a lógica de "!reset" e "@menção" foi REMOVIDA daqui
    # Isso evita que o bot responda duas vezes (pela menção e pelo /comando)
    # E centraliza a lógica nos novos comandos de barra.


# --- Iniciar o Bot ---
# WEBHOOK_URL é opcional - o bot funciona sem ele, respondendo diretamente no canal
if DISCORD_TOKEN and GOOGLE_API_KEY_LOADED:
    try:    
        client.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("ERRO: O Token do Discord é inválido. Verifique o seu .env.")
    except Exception as e:
        print(f"Ocorreu um erro ao iniciar o bot: {e}")
else:
    print("ERRO: Uma das chaves obrigatórias (.env) está faltando:")
    if not DISCORD_TOKEN: 
        print("- DISCORD_BOT_TOKEN não encontrada.")
    if not GOOGLE_API_KEY_LOADED: 
        print("- GOOGLE_API_KEY não encontrada.")
    print("\nNota: DISCORD_WEBHOOK_URL é opcional. Se não configurar, o bot responderá diretamente no canal.")