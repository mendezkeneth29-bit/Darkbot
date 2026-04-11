import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
import random
import io
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (RENDER) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot v4.0 Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True # Necesario para ships y userinfo
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Todos los comandos sincronizados con Discord!")

bot = MyBot()

# --- 3. COMANDOS SLASH ---

@bot.tree.command(name="ship", description="Calcula el amor entre dos miembros 💜")
async def ship(interaction: discord.Interaction, miembro1: discord.Member, miembro2: discord.Member):
    await interaction.response.defer()
    
    porcentaje = random.randint(1, 100)
    
    # Descargar avatares
    av1_data = io.BytesIO(await miembro1.display_avatar.read())
    av2_data = io.BytesIO(await miembro2.display_avatar.read())
    
    # Procesar imagen con Pillow
    img1 = Image.open(av1_data).convert("RGBA").resize((200, 200))
    img2 = Image.open(av2_data).convert("RGBA").resize((200, 200))
    
    # Crear lienzo (Largo para poner los dos avatares)
    lienzo = Image.new("RGBA", (500, 200), (0, 0, 0, 0))
    lienzo.paste(img1, (0, 0))
    lienzo.paste(img2, (300, 0))
    
    # Guardar resultado
    img_byte_arr = io.BytesIO()
    lienzo.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    archivo = discord.File(img_byte_arr, filename="ship.png")
    
    emb = discord.Embed(
        title=f"💘 Ship: {miembro1.display_name} x {miembro2.display_name}",
        description=f"**Compatibilidad:** `{porcentaje}%`",
        color=0x010101
    )
    emb.set_image(url="attachment://ship.png")
    await interaction.followup.send(file=archivo, embed=emb)

@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        url_user = "https://users.roblox.com/v1/usernames/users"
        res_user = requests.post(url_user, json={"usernames": [usuario], "excludeBannedUsers": False}, headers=headers).json()
        
        if 'data' in res_user and res_user['data']:
            u = res_user['data'][0]
            uid = u['id']
            res_thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png", headers=headers).json()
            foto = res_thumb['data'][0]['imageUrl'] if 'data' in res_thumb else ""

            emb = discord.Embed(title=f"Perfil de {u['displayName']}", url=f"https://www.roblox.com/users/{uid}/profile", color=0x010101)
            emb.add_field(name="Usuario", value=f"@{u['name']}", inline=True)
            emb.add_field(name="ID", value=f"`{uid}`", inline=True)
            if foto: emb.set_image(url=foto)
            await interaction.followup.send(embed=emb)
        else:
            await interaction.followup.send(f"❌ No encontré a `{usuario}`.")
    except:
        await interaction.followup.send("❌ Error al conectar con Roblox.")

@bot.tree.command(name="userinfo", description="Info de un miembro")
async def userinfo(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    emb = discord.Embed(title=f"Info de {target.name}", color=0x010101)
    emb.set_thumbnail(url=target.display_avatar.url)
    emb.add_field(name="ID", value=f"`{target.id}`", inline=True)
    emb.add_field(name="Cuenta creada", value=target.created_at.strftime("%d/%m/%Y"), inline=False)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="avatar", description="Mira el avatar de alguien")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    emb = discord.Embed(title=f"Avatar de {target.name}", color=0x010101)
    emb.set_image(url=target.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="embed", description="Crea un embed")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str, color: Optional[str] = None):
    try: c = int(color.replace("#", ""), 16) if color else 0x010101
    except: c = 0x010101
    await interaction.channel.send(embed=discord.Embed(title=titulo, description=descripcion, color=c))
    await interaction.response.send_message("Enviado", ephemeral=True)

@bot.tree.command(name="delete", description="Borra mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Borrados {cantidad} mensajes.", ephemeral=True)

# --- 4. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
