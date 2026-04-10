import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. CONFIGURACIÓN PARA RENDER (KEEP ALIVE) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Roblox Pro Edition 💜"

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
        print(f"¡Slash commands sincronizados con éxito! 💜🤣")

bot = MyBot()

# --- 3. LÓGICA DE BÚSQUEDA DE ROBLOX (MÉTODO DIRECTO) ---
async def buscar_roblox(usuario):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        # PASO 1: Obtener ID por nombre exacto (POST para evitar fallos)
        url_id = "https://users.roblox.com/v1/usernames/users"
        data = {"usernames": [usuario], "excludeBannedUsers": False}
        res_id = requests.post(url_id, json=data, headers=headers).json()

        if 'data' not in res_id or not res_id['data']:
            return None # No encontró al usuario

        user_id = res_id['data'][0]['id']
        display_name = res_id['data'][0]['displayName']
        username = res_id['data'][0]['name']

        # PASO 2: Buscar la Foto de Perfil
        url_foto = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        res_foto = requests.get(url_foto, headers=headers).json()
        
        foto_url = "https://www.roblox.com/headshot-thumbnail/image?width=420&height=420&format=png"
        if 'data' in res_foto and res_foto['data']:
            foto_url = res_foto['data'][0]['imageUrl']

        # PASO 3: Crear el Embed épico
        embed = discord.Embed(
            title=f"👤 Perfil de {display_name}",
            description=f"**Username:** @{username}\n**ID:** `{user_id}`",
            color=0x00FF00, # Verde Roblox
            url=f"https://www.roblox.com/users/{user_id}/profile"
        )
        embed.set_thumbnail(url=foto_url)
        embed.add_field(name="🔗 Enlace Directo", value=f"[Ver perfil en Roblox](https://www.roblox.com/users/{user_id}/profile)")
        embed.set_footer(text="¡Ija ke dice! El DarkyBot te lo encontró. 💜🤣")
        
        return embed
    except Exception as e:
        print(f"Error detallado: {e}")
        return "error"

# --- 4. COMANDOS DE ROBLOX (SLASH Y PREFIJO) ---

@bot.tree.command(name="roblox", description="Busca un usuario de Roblox por su nombre")
@app_commands.describe(usuario="El nombre de usuario exacto")
async def roblox_slash(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer() # Para que Discord no se canse de esperar
    resultado = await buscar_roblox(usuario)
    if resultado is None:
        await interaction.followup.send(f"Ija... no encontré a ningún '{usuario}'. Revisa que esté bien escrito. 💜🤣")
    elif resultado == "error":
        await interaction.followup.send("¡Ija! Algo explotó en los servidores de Roblox. 💜🤣")
    else:
        await interaction.followup.send(embed=resultado)

@bot.command(name="roblox")
async def roblox_prefijo(ctx, usuario: str):
    resultado = await buscar_roblox(usuario)
    if resultado is None:
        await ctx.send(f"Ija... no encontré a '{usuario}'. 💜🤣")
    elif resultado == "error":
        await ctx.send("Algo salió mal, ija. 💜🤣")
    else:
        await ctx.send(embed=resultado)

# --- 5. COMANDOS DE ADMINISTRACIÓN ---

@bot.tree.command(name="delete", description="Borra una cantidad de mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete_slash(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"✅ Limpieza terminada: {cantidad} mensajes borrados. 💜", ephemeral=True)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def delete(ctx, cantidad: int):
    await ctx.channel.purge(limit=cantidad + 1)

# --- 6. ENCENDIDO ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: No se encontró el TOKEN en Render.")
