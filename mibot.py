import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
import yt_dlp
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (PARA QUE RENDER NO SE APAGUE) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot v2.0 Online"

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
        # Sincroniza los comandos para que aparezcan en Discord
        await self.tree.sync()
        print("Comandos sincronizados con Discord.")

bot = MyBot()

# --- 3. COMANDOS SLASH ---

# --- COMANDO MÚSICA (PLAY) ---
@bot.tree.command(name="play", description="Busca una canción y muestra su portada")
@app_commands.describe(cancion="¿Qué canción quieres?")
async def play(interaction: discord.Interaction, cancion: str):
    await interaction.response.defer() # Da tiempo para buscar
    
    ydl_opts = {'format': 'best', 'quiet': True, 'default_search': 'ytsearch1', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(cancion, download=False)
            if 'entries' in info: info = info['entries'][0]
            
            emb = discord.Embed(
                title=info.get('title'),
                url=info.get('webpage_url'),
                description=f"🎶 **[Escuchar en YouTube]({info.get('webpage_url')})**",
                color=0x010101
            )
            emb.set_image(url=info.get('thumbnail'))
            await interaction.followup.send(embed=emb)
        except Exception as e:
            await interaction.followup.send("❌ No encontré esa canción.")

# --- COMANDO ROBLOX (REPARADO) ---
@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
@app_commands.describe(usuario="Nombre de usuario de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    
    # Usamos headers para que Roblox no nos bloquee
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # 1. Buscamos el ID del usuario
        url_id = f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1"
        res_id = requests.get(url_id, headers=headers).json()
        
        if 'data' in res_id and res_id['data']:
            user = res_id['data'][0]
            uid = user['id']
            
            # 2. Buscamos la miniatura (avatar)
            url_thumb = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png"
            res_thumb = requests.get(url_thumb, headers=headers).json()
            foto = res_thumb['data'][0]['imageUrl'] if 'data' in res_thumb else ""

            emb = discord.Embed(
                title=f"Perfil de {user['displayName']}",
                url=f"https://www.roblox.com/users/{uid}/profile",
                color=0x010101
            )
            emb.add_field(name="Usuario", value=f"@{user['name']}", inline=True)
            emb.add_field(name="ID", value=f"`{uid}`", inline=True)
            if foto: emb.set_thumbnail(url=foto)
            
            await interaction.followup.send(embed=emb)
        else:
            await interaction.followup.send("❌ No encontré a ese usuario en Roblox.")
    except:
        await interaction.followup.send("❌ Error al conectar con Roblox.")

# --- COMANDO EMBED ---
@bot.tree.command(name="embed", description="Crea un mensaje embed")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str, color: Optional[str] = None):
    try:
        c = int(color.replace("#", ""), 16) if color else 0x010101
    except:
        c = 0x010101
    emb = discord.Embed(title=titulo, description=descripcion, color=c)
    await interaction.channel.send(embed=emb)
    await interaction.response.send_message("Embed enviado.", ephemeral=True)

# --- COMANDO DELETE ---
@bot.tree.command(name="delete", description="Limpia mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Se borraron {cantidad} mensajes.", ephemeral=True)

# --- 4. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
