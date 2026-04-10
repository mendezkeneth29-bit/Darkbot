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
def home(): return "Darky Bot Online"

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
        print(f"Comandos sincronizados.")

bot = MyBot()

# --- 3. LÓGICA DE BÚSQUEDA DE ROBLOX ---
async def buscar_roblox(usuario):
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        user_id = None

        url_search = f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1"
        res_search = requests.get(url_search, headers=headers).json()

        if 'data' in res_search and res_search['data']:
            user_id = res_search['data'][0]['id']
        else:
            url_exact = "https://users.roblox.com/v1/usernames/users"
            data_exact = {"usernames": [usuario], "excludeBannedUsers": False}
            res_exact = requests.post(url_exact, json=data_exact, headers=headers).json()
            if 'data' in res_exact and res_exact['data']:
                user_id = res_exact['data'][0]['id']

        if not user_id:
            return None

        info = requests.get(f"https://users.roblox.com/v1/users/{user_id}", headers=headers).json()
        display_name = info.get('displayName', usuario)
        username = info.get('name', usuario)

        url_foto = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        res_foto = requests.get(url_foto, headers=headers).json()
        foto_url = res_foto['data'][0]['imageUrl'] if 'data' in res_foto and res_foto['data'] else "https://www.roblox.com/headshot-thumbnail/image?width=420&height=420&format=png"

        embed = discord.Embed(
            title=f"Perfil de {display_name}",
            description=f"**Usuario:** @{username}\n**ID:** `{user_id}`",
            color=0x2ecc71,
            url=f"https://www.roblox.com/users/{user_id}/profile"
        )
        embed.set_thumbnail(url=foto_url)
        embed.add_field(name="Enlace", value=f"[Ver perfil](https://www.roblox.com/users/{user_id}/profile)")
        
        return embed
    except Exception as e:
        print(f"Error: {e}")
        return "error"

# --- 4. COMANDOS DE ROBLOX ---

@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
@app_commands.describe(usuario="Nombre de usuario")
async def roblox_slash(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    resultado = await buscar_roblox(usuario)
    if resultado is None:
        await interaction.followup.send(f"No se encontró al usuario '{usuario}'.")
    elif resultado == "error":
        await interaction.followup.send("Hubo un error con la API de Roblox.")
    else:
        await interaction.followup.send(embed=resultado)

@bot.command(name="roblox")
async def roblox_prefijo(ctx, usuario: str):
    resultado = await buscar_roblox(usuario)
    if resultado is None:
        await ctx.send(f"No se encontró al usuario '{usuario}'.")
    elif resultado == "error":
        await ctx.send("Error al conectar con Roblox.")
    else:
        await ctx.send(embed=resultado)

# --- 5. COMANDO DELETE ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def delete(ctx, cantidad: int):
    await ctx.channel.purge(limit=cantidad + 1)

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("Falta el TOKEN.")
