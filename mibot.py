import discord
from discord import app_commands
from discord.ext import commands
import os
import requests # <-- ¡Asegúrate de que esto esté en tus imports!
from flask import Flask
from threading import Thread
from typing import Optional

# --- CONFIGURACIÓN PARA RENDER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Roblox Edition 💜"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"¡Slash commands sincronizados! 💜🤣")

bot = MyBot()

# --- NUEVO COMANDO /ROBLOX ---
@bot.tree.command(name="roblox", description="Busca el perfil de alguien en Roblox")
@app_commands.describe(usuario="El nombre de usuario de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    try:
        # 1. Buscamos el ID del usuario por su nombre
        url_busqueda = f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1"
        res = requests.get(url_busqueda).json()

        if not res['data']:
            await interaction.response.send_message(f"Ija ke dice... no encontré a ningún '{usuario}' en Roblox. 💜🤣", ephemeral=True)
            return

        user_id = res['data'][0]['id']
        display_name = res['data'][0]['displayName']
        username = res['data'][0]['name']

        # 2. Buscamos la foto de perfil (Avatar)
        url_foto = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        res_foto = requests.get(url_foto).json()
        foto_url = res_foto['data'][0]['imageUrl']

        # 3. Armamos el Embed pro
        embed = discord.Embed(
            title=f"👤 Perfil de {display_name}",
            description=f"**Username:** @{username}\n**ID:** `{user_id}`",
            color=0x00FF00, # Color verde Roblox
            url=f"https://www.roblox.com/users/{user_id}/profile"
        )
        embed.set_thumbnail(url=foto_url)
        embed.add_field(name="Link al Perfil", value=f"[Haz clic aquí](https://www.roblox.com/users/{user_id}/profile)")
        embed.set_footer(text="¡Ija! El DarkyBot te lo encontró. 💜🤣")

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"Ija 💜🤣 Algo salió mal con la API: {e}", ephemeral=True)

# --- (Aquí irían tus otros comandos como embed y delete...) ---

if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: Falta el TOKEN.")
