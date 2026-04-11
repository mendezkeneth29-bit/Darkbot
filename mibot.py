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
# Nueva API KEY actualizada
genai.configure(api_key="AIzaSyCbgKH1WXr52AumroH7jZK_Le7fa32XOFY")
# Usamos 'gemini-1.5-flash' o 'gemini-pro' según compatibilidad
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        # Sincronización forzada de comandos "/"
        await self.tree.sync()
        print("¡Comandos sincronizados!")

bot = MyBot()

# --- 4. FUNCIÓN PARA RESPUESTA DE IA ---
async def obtener_respuesta_ia(pregunta):
    try:
        response = model.generate_content(f"Responde de forma breve y natural: {pregunta}")
        return response.text
    except Exception as e:
        print(f"Error de IA: {e}")
        return "Hubo un error al procesar tu pregunta con la nueva clave."

# --- 5. COMANDOS SLASH ---

@bot.tree.command(name="sayme", description="Habla con la inteligencia artificial")
@app_commands.describe(pregunta="Escribe tu pregunta")
async def sayme_slash(interaction: discord.Interaction, pregunta: str):
    await interaction.response.defer()
    respuesta = await obtener_respuesta_ia(pregunta)
    embed = discord.Embed(
        title="Chat IA", 
        description=f"**Tú:** {pregunta}\n\n**DarkyBot:** {respuesta}", 
        color=0x010101
    )
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="delete", description="Borra una cantidad de mensajes")
@app_commands.describe(cantidad="Mensajes a borrar")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete_slash(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Se borraron {cantidad} mensajes.", ephemeral=True)

@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
async def roblox_slash(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1"
    res = requests.get(url, headers=headers).json()
    
    if 'data' in res and res['data']:
        user = res['data'][0]
        id_u = user['id']
        emb = discord.Embed(
            title=f"Perfil de {user['displayName']}", 
            description=f"**Usuario:** @{user['name']}\n**ID:** `{id_u}`", 
            color=0x010101, 
            url=f"https://www.roblox.com/users/{id_u}/profile"
        )
        await interaction.followup.send(embed=emb)
    else:
        await interaction.followup.send("Usuario no encontrado.")

@bot.tree.command(name="embed", description="Crea un embed personalizado")
async def embed_slash(interaction: discord.Interaction, titulo: str, descripcion: str, color: str):
    try: c = int(color.replace("#", ""), 16)
    except: c = 0x010101
    emb = discord.Embed(title=titulo, description=descripcion, color=c)
    await interaction.channel.send(embed=emb)
    await interaction.response.send_message("Embed enviado.", ephemeral=True)

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
