import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. CONFIGURACIÓN PARA RENDER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Hybrid Edition 💜"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"¡Slash commands sincronizados! 💜🤣")

bot = MyBot()

# --- 3. LÓGICA DE BÚSQUEDA (La función que hace la magia) ---
async def buscar_roblox(usuario):
    try:
        # Buscamos el ID
        url_busqueda = f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1"
        res = requests.get(url_busqueda).json()

        if not res['data']:
            return None

        user_id = res['data'][0]['id']
        display_name = res['data'][0]['displayName']
        username = res['data'][0]['name']

        # Buscamos el Avatar
        url_foto = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        res_foto = requests.get(url_foto).json()
        foto_url = res_foto['data'][0]['imageUrl']

        # Creamos el Embed
        embed = discord.Embed(
            title=f"👤 Perfil de {display_name}",
            description=f"**Username:** @{username}\n**ID:** `{user_id}`",
            color=0x00FF00,
            url=f"https://www.roblox.com/users/{user_id}/profile"
        )
        embed.set_thumbnail(url=foto_url)
        embed.add_field(name="Link al Perfil", value=f"[Haz clic aquí](https://www.roblox.com/users/{user_id}/profile)")
        embed.set_footer(text="¡Ija! El DarkyBot te lo encontró. 💜🤣")
        
        return embed
    except:
        return "error"

# --- 4. COMANDO SLASH (/roblox) ---
@bot.tree.command(name="roblox", description="Busca el perfil de alguien en Roblox")
@app_commands.describe(usuario="El nombre de usuario de Roblox")
async def roblox_slash(interaction: discord.Interaction, usuario: str):
    resultado = await buscar_roblox(usuario)
    
    if resultado is None:
        await interaction.response.send_message(f"Ija ke dice... no encontré a '{usuario}'. 💜🤣", ephemeral=True)
    elif resultado == "error":
        await interaction.response.send_message("Ija, algo explotó con la API de Roblox. 💜🤣", ephemeral=True)
    else:
        await interaction.response.send_message(embed=resultado)

# --- 5. COMANDO PREFIJO (darky!roblox) ---
@bot.command(name="roblox")
async def roblox_prefijo(ctx, usuario: str):
    resultado = await buscar_roblox(usuario)
    
    if resultado is None:
        await ctx.send(f"Ija ke dice... no encontré a '{usuario}'. 💜🤣")
    elif resultado == "error":
        await ctx.send("Ija, algo explotó con la API de Roblox. 💜🤣")
    else:
        await ctx.send(embed=resultado)

# --- 6. ENCENDIDO ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: Falta el TOKEN.")
