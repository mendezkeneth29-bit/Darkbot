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
def home(): return "Darky AI Online 💜"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. CONFIGURACIÓN DE LA IA (GEMINI) ---
# Aquí pegamos tu API KEY directamente para que no haya fallos
API_KEY_GEMINI = "AIzaSyDN5wWuYbxn20ruuOR3Ad6AwAX-9BBcNr8"
genai.configure(api_key=API_KEY_GEMINI)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        # Esto es lo que hace que aparezcan los comandos de "/"
        await self.tree.sync()
        print("Comandos sincronizados con Discord.")

bot = MyBot()

# --- 4. FUNCIÓN PARA RESPUESTA DE IA ---
async def obtener_respuesta_ia(pregunta):
    try:
        # Instrucción para que responda como tú quieres
        response = model.generate_content(f"Responde de forma breve: {pregunta}")
        return response.text
    except Exception as e:
        print(f"Error de IA: {e}")
        return f"Error técnico: {e}"

# --- 5. COMANDOS ---

# COMANDO SAYME (CHAT IA)
@bot.tree.command(name="sayme", description="Chatea con la inteligencia artificial")
@app_commands.describe(pregunta="¿Qué le quieres decir al bot?")
async def sayme_slash(interaction: discord.Interaction, pregunta: str):
    await interaction.response.defer()
    respuesta = await obtener_respuesta_ia(pregunta)
    embed = discord.Embed(title="Chat IA", description=f"**Tú:** {pregunta}\n\n**Respuesta:** {respuesta}", color=0x010101)
    await interaction.followup.send(embed=embed)

# COMANDO DELETE (AHORA SÍ APARECERÁ EN "/")
@bot.tree.command(name="delete", description="Borra una cantidad específica de mensajes")
@app_commands.describe(cantidad="¿Cuántos mensajes quieres borrar?")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete_slash(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Se han borrado {cantidad} mensajes.", ephemeral=True)

# COMANDO ROBLOX
async def buscar_roblox(usuario):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url_search = f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1"
        res_search = requests.get(url_search, headers=headers).json()
        user_id = res_search['data'][0]['id'] if 'data' in res_search and res_search['data'] else None
        
        if not user_id:
            url_exact = "https://users.roblox.com/v1/usernames/users"
            res_exact = requests.post(url_exact, json={"usernames": [usuario], "excludeBannedUsers": False}, headers=headers).json()
            user_id = res_exact['data'][0]['id'] if 'data' in res_exact and res_exact['data'] else None

        if not user_id: return None

        info = requests.get(f"https://users.roblox.com/v1/users/{user_id}", headers=headers).json()
        url_foto = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
        res_foto = requests.get(url_foto, headers=headers).json()
        foto_url = res_foto['data'][0]['imageUrl'] if 'data' in res_foto and res_foto['data'] else ""

        embed = discord.Embed(title=f"Perfil de {info.get('displayName')}", description=f"**Usuario:** @{info.get('name')}\n**ID:** `{user_id}`", color=0x010101, url=f"https://www.roblox.com/users/{user_id}/profile")
        embed.set_thumbnail(url=foto_url)
        return embed
    except: return None

@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
async def roblox_slash(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    res = await buscar_roblox(usuario)
    if res: await interaction.followup.send(embed=res)
    else: await interaction.followup.send("No se encontró el usuario.")

# COMANDO EMBED
@bot.tree.command(name="embed", description="Crea un embed personalizado")
async def embed_slash(interaction: discord.Interaction, titulo: str, descripcion: str, color: str):
    try: color_hex = int(color.replace("#", ""), 16)
    except: color_hex = 0x010101
    emb = discord.Embed(title=titulo, description=descripcion, color=color_hex)
    await interaction.channel.send(embed=emb)
    await interaction.response.send_message("Embed enviado.", ephemeral=True)

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
