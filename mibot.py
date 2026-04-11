import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. KEEP ALIVE PARA RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "DarkyBot Mega System Online 💜"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BASE DE DATOS TEMPORAL ---
banco_datos = {}
cartera_datos = {}

COLOR_SISTEMA = 0x000001

# --- 3. BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ DarkyBot encendido como {self.user}")

bot = DarkyBot()

# --- 4. COMANDO BALANCE ---
@bot.tree.command(name="balance", description="Consulta tus finanzas")
async def balance(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    uid = str(t.id)

    c = cartera_datos.get(uid, 0)
    b = banco_datos.get(uid, 0)

    emb = discord.Embed(
        title=f"🏦 BANCO CENTRAL: {t.name.upper()}",
        color=COLOR_SISTEMA
    )
    emb.add_field(name="💵 Cartera", value=f"${c:,}", inline=False)
    emb.add_field(name="🏦 Banco", value=f"${b:,}", inline=False)

    await interaction.response.send_message(embed=emb)

# --- 5. INICIO ---
keep_alive()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ No se encontró el TOKEN. Configúralo en Render.")

bot.run(TOKEN)
