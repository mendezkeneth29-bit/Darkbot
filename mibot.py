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

# --- 1. HOSTING PARA RENDER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot Admin Edition Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BASE DE DATOS DEL BANCO ---
banco_datos = {}

# --- 3. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Comandos sincronizados! Incluyendo el poder de Admin. 💜🤣")

    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        if uid not in banco_datos: banco_datos[uid] = 0
        banco_datos[uid] += 5
        await self.process_commands(message)

bot = MyBot()

# --- 4. COMANDOS DE BANCO & ADMIN ---

@bot.tree.command(name="banco", description="Mira tu saldo bancario")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    uid = str(target.id)
    saldo = banco_datos.get(uid, 0)
    emb = discord.Embed(title=f"🏦 Banco de {target.display_name}", description=f"Saldo: **${saldo}**", color=0x010101)
    emb.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="transferir", description="Pásale dinero a un amigo")
async def transferir(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    aid = str(interaction.user.id)
    mid = str(miembro.id)
    if cantidad <= 0 or banco_datos.get(aid, 0) < cantidad:
        return await interaction.response.send_message("No tienes dinero suficiente, ija. 🤣", ephemeral=True)
    banco_datos[aid] -= cantidad
    banco_datos[mid] = banco_datos.get(mid, 0) + cantidad
    await interaction.response.send_message(f"✅ Has enviado **${cantidad}** a {miembro.mention}.")

# --- COMANDO DE REGALAR (SOLO ADMINS) ---
@bot.tree.command(name="regalar", description="Genera dinero infinito para alguien (Solo Admins)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(miembro="A quién le darás el regalo", cantidad="Monto a generar")
async def regalar(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    mid = str(miembro.id)
    if cantidad <= 0:
        return await interaction.response.send_message("No puedes regalar deudas, ija. 🤣", ephemeral=True)
    
    # Sumamos el dinero sin quitarle al admin
    banco_datos[mid] = banco_datos.get(mid, 0) + cantidad
    
    emb = discord.Embed(
        title="🎁 ¡Regalo de la Administración!",
        description=f"Se han generado **${cantidad}** dólares para {miembro.mention}.",
        color=0x010101
    )
    emb.set_footer(text="Cortesía del dueño del bot. 💜🤣")
    await interaction.response.send_message(embed=emb)

# --- 5. COMANDOS SOCIALES ---

@bot.tree.command(name="ship", description="Amor entre dos miembros")
async def ship(interaction: discord.Interaction, miembro1: discord.Member, miembro2: discord.Member):
    await interaction.response.defer()
    porcent = random.randint(1, 100)
    av1 = io.BytesIO(await miembro1.display_avatar.read())
    av2 = io.BytesIO(await miembro2.display_avatar.read())
    img1 = Image.open(av1).convert("RGBA").resize((200, 200))
    img2 = Image.open(av2).convert("RGBA").resize((200, 200))
    lienzo = Image.new("RGBA", (500, 200), (0, 0, 0, 0))
    lienzo.paste(img1, (0, 0))
    lienzo.paste(img2, (300, 0))
    out = io.BytesIO()
    lienzo.save(out, format='PNG')
    out.seek(0)
    emb = discord.Embed(title=f"💘 Ship: {porcent}%", color=0x010101)
    emb.set_image(url="attachment://ship.png")
    await interaction.followup.send(file=discord.File(out, filename="ship.png"), embed=emb)

@bot.tree.command(name="roblox", description="Perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario], "excludeBannedUsers": False}, headers=headers).json()
        if 'data' in r and r['data']:
            u = r['data'][0]
            uid = u['id']
            thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png", headers=headers).json()
            foto = thumb['data'][0]['imageUrl'] if 'data' in thumb else ""
            emb = discord.Embed(title=f"Perfil de {u['displayName']}", url=f"https://www.roblox.com/users/{uid}/profile", color=0x010101)
            if foto: emb.set_image(url=foto)
            await interaction.followup.send(embed=emb)
        else: await interaction.followup.send("No lo encontré.")
    except: await interaction.followup.send("Error en Roblox.")

@bot.tree.command(name="avatar", description="Mira un avatar")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    emb = discord.Embed(title=f"Avatar de {target.name}", color=0x010101)
    emb.set_image(url=target.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="userinfo", description="Info del miembro")
async def userinfo(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    emb = discord.Embed(title=f"Info de {target.name}", color=0x010101)
    emb.set_thumbnail(url=target.display_avatar.url)
    emb.add_field(name="ID", value=f"`{target.id}`")
    await interaction.response.send_message(embed=emb)

# --- 6. UTILIDAD ---

@bot.tree.command(name="embed", description="Crea un embed")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str, color: Optional[str] = None):
    try: c = int(color.replace("#", ""), 16) if color else 0x010101
    except: c = 0x010101
    await interaction.channel.send(embed=discord.Embed(title=titulo, description=descripcion, color=c))
    await interaction.response.send_message("Enviado. 💜", ephemeral=True)

@bot.tree.command(name="delete", description="Borra mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Borrados {cantidad}.", ephemeral=True)

# --- 7. INICIO ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
