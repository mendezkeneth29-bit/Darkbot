import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
import google.generativeai as genai
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. CONFIGURACIÓN PARA RENDER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky AI Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. CONFIGURACIÓN DE LA IA (GEMINI) ---
# Usando la API Key que proporcionaste
genai.configure(api_key="AIzaSyDN5wWuYbxn20ruuOR3Ad6AwAX-9BBcNr8")
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Comandos sincronizados.")

bot = MyBot()

# --- 4. COMANDO SAYME (INTELIGENCIA ARTIFICIAL) ---

async def obtener_respuesta_ia(pregunta):
    try:
        # Instrucción para que la respuesta sea coherente y breve
        prompt = f"Eres un asistente de Discord. Responde de forma breve a esto: {pregunta}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error IA: {e}")
        return "Hubo un error al procesar tu pregunta."

@bot.tree.command(name="sayme", description="Hazle una pregunta a la IA")
@app_commands.describe(pregunta="¿Qué quieres preguntar?")
async def sayme_slash(interaction: discord.Interaction, pregunta: str):
    await interaction.response.defer()
    respuesta = await obtener_respuesta_ia(pregunta)
    
    embed = discord.Embed(
        title="Chat IA",
        description=f"**Pregunta:** {pregunta}\n\n**Respuesta:** {respuesta}",
        color=0x010101
    )
    await interaction.followup.send(embed=embed)

@bot.command(name="sayme")
async def sayme_prefijo(ctx, *, pregunta: str):
    async with ctx.typing():
        respuesta = await obtener_respuesta_ia(pregunta)
        embed = discord.Embed(
            title="Chat IA",
            description=f"**Pregunta:** {pregunta}\n\n**Respuesta:** {respuesta}",
            color=0x010101
        )
        await ctx.send(embed=embed)

# --- 5. LÓGICA Y COMANDOS DE ROBLOX ---

async def buscar_roblox(usuario):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url_search = f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1"
        res_search = requests.get(url_search, headers=headers).json()
        
        user_id = None
        if 'data' in res_search and res_search['data']:
            user_id = res_search['data'][0]['id']
        else:
            url_exact = "https://users.roblox.com/v1/usernames/users"
            data = {"usernames": [usuario], "excludeBannedUsers": False}
            res_exact = requests.post(url_exact, json=data, headers=headers).json()
            if 'data' in res_exact and res_exact['data']:
                user_id = res_exact['data'][0]['id']

        if not user_id: return None

        info = requests.get(f"https://users.roblox.com/v1/users/{user_id}", headers=headers).json()
        
        url_foto = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
        res_foto = requests.get(url_foto, headers=headers).json()
        foto_url = res_foto['data'][0]['imageUrl'] if 'data' in res_foto and res_foto['data'] else ""

        embed = discord.Embed(
            title=f"Perfil de {info.get('displayName')}",
            description=f"**Usuario:** @{info.get('name')}\n**ID:** `{user_id}`",
            color=0x010101,
            url=f"https://www.roblox.com/users/{user_id}/profile"
        )
        embed.set_thumbnail(url=foto_url)
        return embed
    except: return "error"

@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
async def roblox_slash(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    resultado = await buscar_roblox(usuario)
    if isinstance(resultado, discord.Embed): await interaction.followup.send(embed=resultado)
    else: await interaction.followup.send("No encontrado.")

@bot.command(name="roblox")
async def roblox_prefijo(ctx, usuario: str):
    resultado = await buscar_roblox(usuario)
    if isinstance(resultado, discord.Embed): await ctx.send(embed=resultado)
    else: await ctx.send("No encontrado.")

# --- 6. COMANDOS DE ADMINISTRACIÓN (DELETE Y EMBED) ---

@bot.command()
@commands.has_permissions(manage_messages=True)
async def delete(ctx, cantidad: int):
    await ctx.channel.purge(limit=cantidad + 1)

@bot.tree.command(name="embed", description="Crea un embed")
async def embed_slash(interaction: discord.Interaction, titulo: str, descripcion: str, color: str):
    try: color_hex = int(color.replace("#", ""), 16)
    except: color_hex = 0x010101
    emb = discord.Embed(title=titulo, description=descripcion, color=color_hex)
    await interaction.channel.send(embed=emb)
    await interaction.response.send_message("Enviado", ephemeral=True)

# --- 7. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
