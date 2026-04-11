import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
import yt_dlp
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (RENDER) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot Final Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Todos los comandos han sido sincronizados.")

bot = MyBot()

# --- 3. LÓGICA DE BÚSQUEDA DE MÚSICA ---
def buscar_musica(nombre):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(nombre, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            return {
                'titulo': info.get('title'),
                'url': info.get('webpage_url'),
                'portada': info.get('thumbnail')
            }
        except:
            return None

# --- 4. COMANDOS SLASH ---

# --- COMANDO: PLAY (MÚSICA) ---
@bot.tree.command(name="play", description="Busca una canción y muestra su portada")
@app_commands.describe(cancion="Nombre de la canción")
async def play(interaction: discord.Interaction, cancion: str):
    await interaction.response.defer()
    datos = buscar_musica(cancion)
    if datos:
        embed = discord.Embed(
            title=datos['titulo'],
            url=datos['url'],
            description=f"✅ [Haz clic aquí para escuchar en YouTube]({datos['url']})",
            color=0x010101
        )
        embed.set_image(url=datos['portada'])
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("No encontré la canción.")

# --- COMANDO: EMBED (PERSONALIZADO) ---
@bot.tree.command(name="embed", description="Crea un mensaje embed elegante")
@app_commands.describe(
    titulo="El título del embed", 
    descripcion="El texto del mensaje", 
    color="Color en HEX (ej: #FF5733 o deja vacío para negro)"
)
async def embed_slash(interaction: discord.Interaction, titulo: str, descripcion: str, color: Optional[str] = None):
    # Si no pones color, se pone negro (0x010101)
    try:
        if color:
            color_hex = int(color.replace("#", ""), 16)
        else:
            color_hex = 0x010101
    except:
        color_hex = 0x010101

    emb = discord.Embed(title=titulo, description=descripcion, color=color_hex)
    await interaction.channel.send(embed=emb)
    await interaction.response.send_message("¡Embed enviado!", ephemeral=True)

# --- COMANDO: DELETE ---
@bot.tree.command(name="delete", description="Borra una cantidad de mensajes")
@app_commands.describe(cantidad="Número de mensajes a eliminar")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Se han borrado {cantidad} mensajes.", ephemeral=True)

# --- COMANDO: ROBLOX ---
@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    r = requests.get(f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1").json()
    if 'data' in r and r['data']:
        u = r['data'][0]
        id_u = u['id']
        emb = discord.Embed(
            title=f"Perfil de {u['displayName']}", 
            url=f"https://www.roblox.com/users/{id_u}/profile", 
            color=0x010101
        )
        emb.add_field(name="Usuario", value=f"@{u['name']}")
        emb.add_field(name="ID", value=f"`{id_u}`")
        await interaction.followup.send(embed=emb)
    else:
        await interaction.followup.send("Usuario de Roblox no encontrado.")

# --- 5. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    bot.run(token)
