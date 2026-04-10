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
        print(f"¡Comandos sincronizados! 💜🤣")

bot = MyBot()

# --- 3. LÓGICA DE BÚSQUEDA DE ROBLOX (MEJORADA) ---
async def buscar_roblox(usuario):
    try:
        # Identificación para que Roblox no nos bloquee
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        # Buscar ID del usuario
        url_busqueda = f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1"
        res = requests.get(url_busqueda, headers=headers).json()

        if 'data' not in res or not res['data']:
            return None

        user_id = res['data'][0]['id']
        display_name = res['data'][0]['displayName']
        username = res['data'][0]['name']

        # Buscar Foto de Perfil
        url_foto = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        res_foto = requests.get(url_foto, headers=headers).json()
        
        foto_url = "https://www.roblox.com/headshot-thumbnail/image?width=420&height=420&format=png"
        if 'data' in res_foto and res_foto['data']:
            foto_url = res_foto['data'][0]['imageUrl']

        # Crear el Embed
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
    except Exception as e:
        print(f"Error: {e}")
        return "error"

# --- 4. COMANDOS DE ROBLOX ---

@bot.tree.command(name="roblox", description="Busca un usuario de Roblox")
@app_commands.describe(usuario="El nombre de usuario")
async def roblox_slash(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer() # Para que no expire el tiempo
    resultado = await buscar_roblox(usuario)
    if resultado is None:
        await interaction.followup.send(f"Ija ke dice... no encontré a '{usuario}'. 💜🤣")
    elif resultado == "error":
        await interaction.followup.send("Ija, algo explotó con la API de Roblox. Intentemos luego. 💜🤣")
    else:
        await interaction.followup.send(embed=resultado)

@bot.command(name="roblox")
async def roblox_prefijo(ctx, usuario: str):
    resultado = await buscar_roblox(usuario)
    if resultado is None:
        await ctx.send(f"Ija ke dice... no encontré a '{usuario}'. 💜🤣")
    elif resultado == "error":
        await ctx.send("Ija, algo explotó con la API de Roblox. 💜🤣")
    else:
        await ctx.send(embed=resultado)

# --- 5. OTROS COMANDOS (DELETE Y EMBED) ---

@bot.tree.command(name="delete", description="Borra mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete_slash(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"✅ Borré {cantidad} mensajes, ija. 💜", ephemeral=True)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def delete(ctx, cantidad: int):
    await ctx.channel.purge(limit=cantidad + 1)

@bot.tree.command(name="embed", description="Crea un embed")
async def embed_slash(interaction: discord.Interaction, titulo: str, descripcion: str, color: str, canal: Optional[discord.TextChannel] = None):
    destino = canal or interaction.channel
    color_hex = int(color.replace("#", ""), 16)
    emb = discord.Embed(title=titulo, description=descripcion, color=color_hex)
    await destino.send(embed=emb)
    await interaction.response.send_message("✅ Enviado", ephemeral=True)

# --- 6. ENCENDIDO ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: No hay TOKEN en las variables de entorno.")
