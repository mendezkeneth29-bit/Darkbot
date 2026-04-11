import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (RENDER) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot v3.0 Online"

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
        print("Comandos sincronizados con Discord.")

bot = MyBot()

# --- 3. COMANDO ROBLOX (ARREGLADO) ---
@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
@app_commands.describe(usuario="Nombre de usuario de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Paso 1: Buscar ID por nombre de usuario (Búsqueda exacta)
        url_user = "https://users.roblox.com/v1/usernames/users"
        post_data = {"usernames": [usuario], "excludeBannedUsers": False}
        res_user = requests.post(url_user, json=post_data, headers=headers).json()
        
        if 'data' in res_user and len(res_user['data']) > 0:
            user_data = res_user['data'][0]
            uid = user_data['id']
            name = user_data['name']
            display_name = user_data['displayName']
            
            # Paso 2: Obtener miniatura del avatar
            url_thumb = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png&isCircular=false"
            res_thumb = requests.get(url_thumb, headers=headers).json()
            foto = res_thumb['data'][0]['imageUrl'] if 'data' in res_thumb and len(res_thumb['data']) > 0 else ""

            # Paso 3: Crear el Embed
            emb = discord.Embed(
                title=f"Perfil de {display_name}",
                url=f"https://www.roblox.com/users/{uid}/profile",
                color=0x010101 # Negro elegante
            )
            emb.add_field(name="Usuario", value=f"@{name}", inline=True)
            emb.add_field(name="ID", value=f"`{uid}`", inline=True)
            if foto:
                emb.set_image(url=foto) # Foto grande del avatar
            
            await interaction.followup.send(embed=emb)
        else:
            await interaction.followup.send(f"❌ No encontré al usuario `{usuario}`.")
    except Exception as e:
        print(f"Error Roblox: {e}")
        await interaction.followup.send("❌ Hubo un problema al conectar con Roblox.")

# --- 4. COMANDO EMBED ---
@bot.tree.command(name="embed", description="Crea un mensaje embed")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str, color: Optional[str] = None):
    try:
        c = int(color.replace("#", ""), 16) if color else 0x010101
    except:
        c = 0x010101
    emb = discord.Embed(title=titulo, description=descripcion, color=c)
    await interaction.channel.send(embed=emb)
    await interaction.response.send_message("Embed enviado.", ephemeral=True)

# --- 5. COMANDO DELETE ---
@bot.tree.command(name="delete", description="Limpia mensajes del canal")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"🧹 Se borraron {cantidad} mensajes.", ephemeral=True)

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    bot.run(token)
