import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
import yt_dlp
from flask import Flask
from threading import Thread

# --- 1. HOSTING (RENDER) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Music Edition Online"

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
        print("Comandos sincronizados.")

bot = MyBot()

# --- 3. LÓGICA DE MÚSICA ---
def buscar_y_descargar(nombre_cancion):
    # Nombre de archivo fijo para evitar caracteres raros
    archivo_destino = "audio_descargado.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
        'outtmpl': archivo_destino,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(nombre_cancion, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            return {
                'titulo': info.get('title'),
                'portada': info.get('thumbnail'),
                'archivo': archivo_destino
            }
        except Exception as e:
            print(f"Error en descarga: {e}")
            return None

# --- 4. COMANDOS SLASH ---

@bot.tree.command(name="play", description="Busca una canción y envía el audio con su portada")
@app_commands.describe(cancion="Nombre de la canción o artista")
async def play(interaction: discord.Interaction, cancion: str):
    await interaction.response.defer() # Da tiempo para descargar
    
    datos = buscar_y_descargar(cancion)
    
    if datos:
        embed = discord.Embed(
            title=f"🎶 {datos['titulo']}", 
            color=0x010101
        )
        embed.set_image(url=datos['portada'])
        
        archivo = discord.File(datos['archivo'], filename="musica.mp3")
        
        await interaction.followup.send(embed=embed, file=archivo)
        
        # Limpiar archivo después de enviar
        if os.path.exists(datos['archivo']):
            os.remove(datos['archivo'])
    else:
        await interaction.followup.send("No encontré la canción.")

@bot.tree.command(name="delete", description="Borra mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Borrados {cantidad} mensajes.", ephemeral=True)

@bot.tree.command(name="roblox", description="Busca perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    r = requests.get(f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1").json()
    if 'data' in r and r['data']:
        u = r['data'][0]
        emb = discord.Embed(title=f"Perfil de {u['displayName']}", url=f"https://www.roblox.com/users/{u['id']}/profile", color=0x010101)
        await interaction.followup.send(embed=emb)
    else:
        await interaction.followup.send("No encontrado.")

# --- 5. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    bot.run(token)
