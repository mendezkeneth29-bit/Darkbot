import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (Para que Render no lo mate) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot Ultimate Online 💜"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. BASE DE DATOS TEMPORAL ---
banco_datos = {}
tienda_roles = {} 

# --- 3. VISTAS (BOTONES Y SELECTORES) ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Elige un rol para comprar...", options=options, custom_id="sel_t")
    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        if banco_datos.get(uid, 0) < data['precio']:
            return await interaction.response.send_message("No tienes dinero suficiente, ija. 🤣", ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("Error: No encuentro ese rol. 🤣", ephemeral=True)
        
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ ¡Compraste **{data['nombre']}**! ¡YIPIEEE! 💜", ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        options = []
        for rid, data in tienda_roles.items():
            if data['stock'] > 0:
                options.append(discord.SelectMenuOption(label=data['nombre'], value=str(rid), description=f"Precio: ${data['precio']} | Stock: {data['stock']}"))
        if not options: options.append(discord.SelectMenuOption(label="Sin stock", value="none"))
        self.add_item(TiendaSelect(options))

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout); self.participantes = []
    @discord.ui.button(label="Participar 🎉", style=discord.ButtonStyle.green)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes: return await interaction.response.send_message("¡Ya estás participando! 🤣", ephemeral=True)
        self.participantes.append(interaction.user); await interaction.response.send_message("¡Ok mañana! Te has anotado. 💜", ephemeral=True)

# --- 4. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True; intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)
    async def setup_hook(self):
        await self.tree.sync()
        print("¡Sincronización Total Lista! 💜🤣")
    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        # Ganancia automática de $5 por mensaje
        banco_datos[uid] = banco_datos.get(uid, 0) + 5
        await self.process_commands(message)

bot = MyBot()

# --- 5. COMANDOS DE ADMINISTRACIÓN Y TIENDA ---

@bot.tree.command(name="tienda_config", description="Configura un rol en la tienda (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message(f"✅ Configurado: {rol.name} a ${precio}. 💜", ephemeral=True)

@bot.tree.command(name="tienda", description="Abre la tienda de roles")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("La tienda está vacía. 🤣", ephemeral=True)
    emb = discord.Embed(title="🏪 DARKY STORE", color=0x010101)
    for rid, data in tienda_roles.items():
        emb.add_field(name=data['nombre'], value=f"💰 `${data['precio']}` | 📦 `{data['stock']}`")
    await interaction.response.send_message(embed=emb, view=TiendaView())

@bot.tree.command(name="giveaway", description="Sorteo de dinero automático")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(unidad=[app_commands.Choice(name="Minutos", value="m"), app_commands.Choice(name="Horas", value="h")])
async def giveaway(interaction: discord.Interaction, tiempo: int, unidad: str, premio: int, canal_ganador: discord.TextChannel):
    seg = tiempo * 60 if unidad == "m" else tiempo * 3600
    final = int(time.time() + seg); view = GiveawayView(timeout=seg)
    emb = discord.Embed(title="🎊 SORTEO ACTIVO 🎊", description=f"💰 **Premio:** `${premio}`\n⏰ **Termina:** <t:{final}:R>", color=0x010101)
    await interaction.response.send_message("Sorteo lanzado. 🚀", ephemeral=True)
    msg = await interaction.channel.send(embed=emb, view=view)
    await asyncio.sleep(seg)
    if not view.participantes: return await canal_ganador.send("Nadie participó en el sorteo. 🤣")
    g = random.choice(view.participantes); banco_datos[str(g.id)] = banco_datos.get(str(g.id), 0) + premio
    await canal_ganador.send(f"🏆 ¡{g.mention} ganó **${premio}**! Depositados en su cuenta. 💜🤣")

# --- 6. COMANDOS DE ECONOMÍA ---

@bot.tree.command(name="banco", description="Mira tu saldo bancario")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="🏦 SISTEMA BANCARIO CENTRAL", description=f"Registros financieros de **{t.name}**", color=0x2b2d31)
    emb.add_field(name="💰 Capital Disponible", value=f"
