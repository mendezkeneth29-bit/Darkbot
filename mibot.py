import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import requests
import time
import io
from flask import Flask
from threading import Thread
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

# --- KEEP ALIVE ---
app = Flask('')

@app.route('/')
def home():
    return "DarkyBot Online"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- DATOS ---
cartera = {}
cooldowns = {}
COLOR = 0x000000
SEPARADOR = "━━━━━━━━━━━━━━━━━━━━"

# --- BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"DarkyBot activo como {self.user}")

bot = DarkyBot()

# --- DINERO POR MENSAJE ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    ahora = time.time()
    ultimo = cooldowns.get(uid, 0)

    if ahora - ultimo > 10:
        cartera[uid] = cartera.get(uid, 0) + 5
        cooldowns[uid] = ahora

    await bot.process_commands(message)

# --- CARTERA ---
@bot.tree.command(name="cartera", description="Ver dinero")
async def cartera_cmd(interaction: discord.Interaction, usuario: Optional[discord.Member]=None):
    u = usuario or interaction.user
    uid = str(u.id)
    money = cartera.get(uid, 0)

    embed = discord.Embed(title="SISTEMA FINANCIERO", color=COLOR)
    embed.set_thumbnail(url=u.display_avatar.url)

    embed.description = (
        f"Usuario: {u.mention}\n"
        f"Dinero: ${money:,}\n\n"
        f"{SEPARADOR}\n"
        f"+5 por mensaje cada 10 segundos."
    )

    await interaction.response.send_message(embed=embed)

# --- REGALAR ---
@bot.tree.command(name="regalar", description="Dar dinero (admin)")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
    uid = str(usuario.id)
    cartera[uid] = cartera.get(uid, 0) + cantidad

    embed = discord.Embed(title="TRANSACCIÓN COMPLETADA", color=COLOR)
    embed.set_thumbnail(url=usuario.display_avatar.url)

    embed.description = (
        f"Usuario: {usuario.mention}\n"
        f"Recibió: ${cantidad:,}\n"
        f"De: {interaction.user.mention}\n"
        f"Nuevo saldo: ${cartera[uid]:,}\n\n"
        f"{SEPARADOR}"
    )

    await interaction.response.send_message(embed=embed)

# --- TRANSFERIR ---
@bot.tree.command(name="transferir", description="Transferir dinero")
async def transferir(interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
    uid = str(interaction.user.id)
    uid2 = str(usuario.id)

    if cartera.get(uid, 0) < cantidad:
        return await interaction.response.send_message("No tienes suficiente dinero", ephemeral=True)

    cartera[uid] -= cantidad
    cartera[uid2] = cartera.get(uid2, 0) + cantidad

    embed = discord.Embed(title="TRANSFERENCIA", color=COLOR)
    embed.description = f"{interaction.user.mention} envió ${cantidad:,} a {usuario.mention}"

    await interaction.response.send_message(embed=embed)

# --- TRABAJO ---
@bot.tree.command(name="trabajo", description="Trabajar")
async def trabajo(interaction: discord.Interaction):
    dinero = random.randint(50, 300)
    uid = str(interaction.user.id)

    cartera[uid] = cartera.get(uid, 0) + dinero

    embed = discord.Embed(title="TRABAJO", color=COLOR)
    embed.description = f"Ganaste ${dinero:,}"

    await interaction.response.send_message(embed=embed)

# --- ROBLOX ---
@bot.tree.command(name="roblox", description="Perfil Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    try:
        res = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [usuario]}
        ).json()

        if not res["data"]:
            return await interaction.response.send_message("Usuario no encontrado", ephemeral=True)

        user_id = res["data"][0]["id"]

        avatar = requests.get(
            f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png"
        ).json()["data"][0]["imageUrl"]

        embed = discord.Embed(title="ROBLOX", color=COLOR)
        embed.description = f"Usuario: {usuario}\nID: {user_id}"
        embed.set_image(url=avatar)

        await interaction.response.send_message(embed=embed)

    except:
        await interaction.response.send_message("Error en Roblox", ephemeral=True)

# --- SHIP PRO ---
@bot.tree.command(name="ship", description="Shipear")
async def ship(interaction: discord.Interaction, u1: discord.Member, u2: discord.Member):
    porcentaje = random.randint(0, 100)

    if porcentaje < 30:
        msg = "Compatibilidad muy baja"
    elif porcentaje < 60:
        msg = "Relación inestable"
    elif porcentaje < 85:
        msg = "Buena conexión"
    else:
        msg = "Compatibilidad casi perfecta"

    img1 = Image.open(io.BytesIO(requests.get(u1.display_avatar.url).content)).convert("RGBA").resize((256,256))
    img2 = Image.open(io.BytesIO(requests.get(u2.display_avatar.url).content)).convert("RGBA").resize((256,256))

    final = Image.new("RGBA", (700, 256), (0, 0, 0, 0))
    final.paste(img1, (0, 0))
    final.paste(img2, (444, 0))

    draw = ImageDraw.Draw(final)

    texto = f"{porcentaje}%"

    try:
        font = ImageFont.truetype("arial.ttf", 90)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0,0), texto, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    x = 350 - (w // 2)
    y = (256 - h) // 2

    draw.text((x+3, y+3), texto, fill=(0,0,0), font=font)
    draw.text((x, y), texto, fill=(255,255,255), font=font)

    buffer = io.BytesIO()
    final.save(buffer, "PNG")
    buffer.seek(0)

    file = discord.File(buffer, "ship.png")

    embed = discord.Embed(title="ANÁLISIS DE COMPATIBILIDAD", color=COLOR)
    embed.description = (
        f"{msg}\n\n"
        f"Usuario 1: {u1.mention}\n"
        f"Usuario 2: {u2.mention}\n"
        f"Resultado: {porcentaje}%"
    )
    embed.set_image(url="attachment://ship.png")

    await interaction.response.send_message(embed=embed, file=file)

# --- DADO ---
@bot.tree.command(name="dado", description="Lanzar dado")
async def dado(interaction: discord.Interaction):
    num = random.randint(1, 6)

    embed = discord.Embed(title="LANZAMIENTO DE DADO", color=COLOR)
    embed.description = f"Resultado: {num}"

    await interaction.response.send_message(embed=embed)

# --- IQ ---
@bot.tree.command(name="iq", description="Medir IQ")
async def iq(interaction: discord.Interaction, usuario: Optional[discord.Member]=None):
    u = usuario or interaction.user
    iq_val = random.randint(50, 200)

    embed = discord.Embed(title="ANÁLISIS INTELECTUAL", color=COLOR)
    embed.description = f"{u.mention} tiene un IQ de {iq_val}"

    await interaction.response.send_message(embed=embed)

# --- EMBED ---
@bot.tree.command(name="embed", description="Crear embed")
async def embed_cmd(interaction: discord.Interaction, titulo: str, descripcion: str, color: str):
    try:
        color_int = int(color.replace("#",""),16)
    except:
        return await interaction.response.send_message("Color inválido", ephemeral=True)

    embed = discord.Embed(title=titulo, description=descripcion, color=color_int)
    await interaction.response.send_message(embed=embed)

# --- DELETE ---
@bot.tree.command(name="delete", description="Borrar mensajes")
@app_commands.checks.has_permissions(administrator=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)

    embed = discord.Embed(title="LIMPIEZA", color=COLOR)
    embed.description = f"{cantidad} mensajes eliminados"

    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- START ---
keep_alive()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN configurado")

bot.run(TOKEN)
