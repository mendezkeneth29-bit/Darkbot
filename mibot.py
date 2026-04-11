import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot Professional Edition Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. CONFIGURACIÓN VISUAL ---
COLOR_BOT = 0x2b2d31
LINEA = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# --- 3. BASE DE DATOS ---
banco_datos = {}
tienda_roles = {} 

# --- 4. VISTAS ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Seleccione un artículo del catálogo...", options=options, custom_id="sel_t")
    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        if banco_datos.get(uid, 0) < data['precio']:
            return await interaction.response.send_message("Transacción denegada: Fondos insuficientes.", ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("Error: El rol solicitado no existe.", ephemeral=True)
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"Compra confirmada: **{data['nombre']}** ha sido añadido.", ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        options = []
        for rid, data in tienda_roles.items():
            if data['stock'] > 0:
                options.append(discord.SelectMenuOption(label=data['nombre'], value=str(rid), description=f"Precio: ${data['precio']} | Existencias: {data['stock']}"))
        if not options: options.append(discord.SelectMenuOption(label="Inventario agotado", value="none"))
        self.add_item(TiendaSelect(options))

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout); self.participantes = []
    @discord.ui.button(label="Inscribirse", style=discord.ButtonStyle.secondary, emoji="🎟️")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes: return await interaction.response.send_message("Su participación ya está registrada.", ephemeral=True)
        self.participantes.append(interaction.user); await interaction.response.send_message("Se ha inscrito correctamente al sorteo.", ephemeral=True)

# --- 5. SETUP DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True; intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)
    async def setup_hook(self):
        await self.tree.sync()
    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        banco_datos[uid] = banco_datos.get(uid, 0) + 5
        await self.process_commands(message)

bot = MyBot()

# --- 6. COMANDOS DE ADMINISTRACIÓN Y ECONOMÍA ---
@bot.tree.command(name="tienda_config", description="Registrar artículo en la tienda")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message(f"Configuración establecida para: **{rol.name}**.", ephemeral=True)

@bot.tree.command(name="tienda", description="Ver catálogo de artículos")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("El catálogo está vacío actualmente.", ephemeral=True)
    emb = discord.Embed(title="CATÁLOGO DE PRODUCTOS", description=LINEA, color=COLOR_BOT)
    for rid, data in tienda_roles.items():
        emb.add_field(name=f"📦 {data['nombre']}", value=f"
http://googleusercontent.com/immersive_entry_chip/0

¡Maldita sea, Kereth! Ahí tienes el código blindado, decorado y directo al mensaje. ¡Ok mañana! 💜🤣 **YIPIEEE!** 💜🤣
