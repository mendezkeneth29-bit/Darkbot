import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (Mantiene el bot vivo 24/7) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot Mega System Online 💜"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. BASES DE DATOS TEMPORALES ---
banco_datos = {}
tienda_roles = {} 

# --- 3. VISTAS INTERACTIVAS ---

class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Selecciona un rol para comprar...", options=options, custom_id="select_tienda")

    async def callback(self, interaction: discord.Interaction):
        role_id = self.values[0]
        if role_id == "none": return
        data = tienda_roles.get(int(role_id))
        user_id = str(interaction.user.id)
        user_money = banco_datos.get(user_id, 0)

        if user_money < data['precio']:
            return await interaction.response.send_message(f"Fondos insuficientes para esta adquisición. 🤣", ephemeral=True)
        
        role = interaction.guild.get_role(int(role_id))
        banco_datos[user_id] -= data['precio']
        tienda_roles[int(role_id)]['stock'] -= 1
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ Transacción completada: **{data['nombre']}** ha sido asignado.", ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        options = []
        for rid, data in tienda_roles.items():
            if data['stock'] > 0:
                options.append(discord.SelectMenuOption(label=data['nombre'], value=str(rid), description=f"Precio: ${data['precio']}"))
        if not options: options.append(discord.SelectMenuOption(label="Sin stock", value="none"))
        self.add_item(TiendaSelect(options))

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout); self.participantes = []
    @discord.ui.button(label="Participar 🎉", style=discord.ButtonStyle.green)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes: return await interaction.response.send_message("Ya estás registrado en el sorteo. 🤣", ephemeral=True)
        self.participantes.append(interaction.user); await interaction.response.send_message("Registro confirmado. 💜", ephemeral=True)

# --- 4. BOT CORE ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True; intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Sincronización Total! 💜🤣")

    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        # Sistema de recompensa por actividad ($5 por mensaje)
        banco_datos[uid] = banco_datos.get(uid, 0) + 5
        await self.process_commands(message)

bot = MyBot()

# --- 5. COMANDOS DE ECONOMÍA (DECORADOS) ---

@bot.tree.command(name="banco", description="Visualiza tu estado de cuenta")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="🏦 REGISTRO BANCARIO", description=f"Estado financiero de **{t.name}**", color=0x2b2d31)
    emb.add_field(name="💰 Capital Disponible", value=f"
