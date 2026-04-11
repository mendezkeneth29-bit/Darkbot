import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import requests
from flask import Flask
from threading import Thread
from typing import Optional

# --- KEEP ALIVE ---
app = Flask('')

@app.route('/')
def home():
    return "DarkyBot Online 💜"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- DATOS ---
banco = {}
cartera = {}

COLOR = 0x000000

# --- BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"🔥 DarkyBot activo como {self.user}")

bot = DarkyBot()

# --- BALANCE ---
@bot.tree.command(name="cartera", description="Ver dinero")
async def cartera_cmd(interaction: discord.Interaction, usuario: Optional[discord.Member]=None):
    u = usuario or interaction.user
    uid = str(u.id)

    money = cartera.get(uid, 0)

    embed = discord.Embed(title="💰 CARTERA", color=COLOR)
    embed.description = f"Usuario: {u.mention}\nDinero disponible: **${money:,}**"
    embed.set_footer(text="Sistema financiero Darky")

    await interaction.response.send_message(embed=embed)

# --- REGALAR (ADMIN) ---
@bot.tree.command(name="regalar", description="Dar dinero (admin)")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
    uid = str(usuario.id)

    cartera[uid] = cartera.get(uid, 0) + cantidad

    embed = discord.Embed(title="🎁 REGALO", color=COLOR)
    embed.description = f"{interaction.user.mention} regaló **${cantidad:,}** a {usuario.mention}"
    await interaction.response.send_message(embed=embed)

# --- TRANSFERIR ---
@bot.tree.command(name="transferir", description="Dar dinero a otro usuario")
async def transferir(interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
    uid = str(interaction.user.id)
    uid2 = str(usuario.id)

    if cartera.get(uid, 0) < cantidad:
        return await interaction.response.send_message("❌ No tienes suficiente dinero", ephemeral=True)

    cartera[uid] -= cantidad
    cartera[uid2] = cartera.get(uid2, 0) + cantidad

    embed = discord.Embed(title="💸 TRANSFERENCIA", color=COLOR)
    embed.description = f"{interaction.user.mention} envió **${cantidad:,}** a {usuario.mention}"
    await interaction.response.send_message(embed=embed)

# --- TRABAJO ---
@bot.tree.command(name="trabajo", description="Ganar dinero")
async def trabajo(interaction: discord.Interaction):
    dinero = random.randint(50, 300)
    uid = str(interaction.user.id)

    cartera[uid] = cartera.get(uid, 0) + dinero

    embed = discord.Embed(title="💼 TRABAJO COMPLETADO", color=COLOR)
    embed.description = f"Trabajaste duro...\nGanaste: **${dinero:,}** 💸"
    await interaction.response.send_message(embed=embed)

# --- ROBLOX ---
@bot.tree.command(name="roblox", description="Ver perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    url = f"https://api.roblox.com/users/get-by-username?username={usuario}"
    data = requests.get(url).json()

    if "Id" not in data:
        return await interaction.response.send_message("❌ Usuario no encontrado", ephemeral=True)

    user_id = data["Id"]
    avatar = f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png"

    embed = discord.Embed(title="🧱 ROBLOX PROFILE", color=COLOR)
    embed.description = f"Usuario: **{usuario}**"
    embed.set_image(url=avatar)

    await interaction.response.send_message(embed=embed)

# --- SHIP ---
@bot.tree.command(name="ship", description="Shipear usuarios")
async def ship(interaction: discord.Interaction, u1: discord.Member, u2: discord.Member):
    porcentaje = random.randint(0, 100)

    embed = discord.Embed(title="💜 SHIP", color=COLOR)
    embed.description = f"{u1.mention} 💕 {u2.mention}\nCompatibilidad: **{porcentaje}%**"

    embed.set_thumbnail(url=u1.display_avatar.url)
    embed.set_image(url=u2.display_avatar.url)

    await interaction.response.send_message(embed=embed)

# --- EMBED PERSONALIZADO ---
@bot.tree.command(name="embed", description="Crear embed")
async def embed_cmd(interaction: discord.Interaction, titulo: str, descripcion: str, color: str):
    try:
        color_int = int(color.replace("#",""), 16)
    except:
        return await interaction.response.send_message("❌ Color inválido", ephemeral=True)

    embed = discord.Embed(title=titulo, description=descripcion, color=color_int)
    await interaction.response.send_message(embed=embed)

# --- DELETE (ADMIN) ---
@bot.tree.command(name="delete", description="Eliminar mensajes")
@app_commands.checks.has_permissions(administrator=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)

    embed = discord.Embed(title="🗑 LIMPIEZA", color=COLOR)
    embed.description = f"Se eliminaron {cantidad} mensajes"
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- INICIO ---
keep_alive()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN")

bot.run(TOKEN)
