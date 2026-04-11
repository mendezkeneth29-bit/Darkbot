import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time, datetime
from PIL import Image, ImageDraw
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (KEEP ALIVE) ---
app = Flask('')

@app.route('/')
def home(): 
    return "DarkyBot Professional System Online 💜"

def run(): 
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BASE DE DATOS Y ESTÉTICA ---
banco_datos = {}
tienda_roles = {}
COLOR_SISTEMA = 0x000001  # NEGRO PURO
SEPARADOR = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# --- 3. COMPONENTES DE INTERFAZ ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="🛒 Selecciona un producto del catálogo...", options=options)

    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        
        if banco_datos.get(uid, 0) < data['precio']:
            emb = discord.Embed(title="🚫 TRANSACCIÓN RECHAZADA", description=f"{SEPARADOR}\n**Motivo:** Fondos insuficientes.", color=COLOR_SISTEMA)
            return await interaction.response.send_message(embed=emb, ephemeral=True)
            
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("❌ Error: El rol ya no existe.", ephemeral=True)
        
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        emb = discord.Embed(title="✅ COMPRA COMPLETADA", description=f"{SEPARADOR}\nAdquirido: **{data['nombre']}**\nNuevo Saldo: **${banco_datos[uid]:,}**", color=COLOR_SISTEMA)
        await interaction.response.send_message(embed=emb, ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect(options))

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.participantes = []
    
    @discord.ui.button(label="Entrar 🎉", style=discord.ButtonStyle.green)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes:
            return await interaction.response.send_message("⚠️ Ya estás en la lista.", ephemeral=True)
        self.participantes.append(interaction.user)
        await interaction.response.send_message("✅ ¡Suerte! Estás participando.", ephemeral=True)

# --- 4. CLASE PRINCIPAL ---
class DarkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="darky!", intents=intents)
    
    async def setup_hook(self):
        await self.tree.sync()
    
    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        banco_datos[uid] = banco_datos.get(uid, 0) + 10 # Gana 10 por mensaje
        await self.process_commands(message)

bot = DarkyBot()

# --- 5. COMANDOS DE ECONOMÍA Y JUEGOS ---
@bot.tree.command(name="work", description="Trabajar para el imperio")
async def work(interaction: discord.Interaction):
    trabajos = ["desarrollador de software", "asesino a sueldo", "minero de criptos", "chef de lujo", "piloto de carreras"]
    ganancia = random.randint(200, 800)
    uid = str(interaction.user.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + ganancia
    emb = discord.Embed(title="💼 JORNADA LABORAL", description=f"Has trabajado como **{random.choice(trabajos)}** y recibiste **${ganancia:,}**.", color=COLOR_SISTEMA)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="crime", description="Intentar un crimen arriesgado")
async def crime(interaction: discord.Interaction):
    if random.randint(1, 100) > 40:
        ganancia = random.randint(1000, 3000)
        uid = str(interaction.user.id)
        banco_datos[uid] = banco_datos.get(uid, 0) + ganancia
        emb = discord.Embed(title="🥷 CRIMEN EXITOSO", description=f"Asaltaste un banco central y escapaste con **${ganancia:,}**.", color=0x2ecc71)
    else:
        perdida = random.randint(500, 1500)
        uid = str(interaction.user.id)
        banco_datos[uid] = max(0, banco_datos.get(uid, 0) - perdida)
        emb = discord.Embed(title="👮 ARRESTADO", description=f"Te atraparon y pagaste una fianza de **${perdida:,}**.", color=0xe74c3c)
    emb.color = COLOR_SISTEMA
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="bet", description="Apostar dinero en el casino")
async def bet(interaction: discord.Interaction, cantidad: int):
    uid = str(interaction.user.id)
    if cantidad <= 0 or banco_datos.get(uid, 0) < cantidad:
        return await interaction.response.send_message("❌ No tienes esa cantidad.", ephemeral=True)
    
    if random.randint(0, 1):
        banco_datos[uid] += cantidad
        msg = f"🎰 ¡GANASTE! Duplicaste tu apuesta a **${cantidad*2:,}**."
    else:
        banco_datos[uid] -= cantidad
        msg = f"💸 ¡PERDISTE! La casa se quedó con tus **${cantidad:,}**."
    
    emb = discord.Embed(title="🎰 CASINO DARKY", description=f"{SEPARADOR}\n{msg}\n{SEPARADOR}", color=COLOR_SISTEMA)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="banco", description="Consultar tu estado financiero")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="🏦 REGISTROS BANCARIOS", description=SEPARADOR, color=COLOR_SISTEMA)
    emb.add_field(name="Titular", value=f"> {t.mention}", inline=True)
    emb.add_field(name="Balance", value=f"> `${saldo:,} USD`", inline=True)
    emb.set_thumbnail(url=t.display_avatar.url)
    emb.set_footer(text=f"Solicitado por {interaction.user.name}")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="pay", description="Enviar dinero a alguien")
async def pay(interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
    uid, tid = str(interaction.user.id), str(usuario.id)
    if usuario.bot or usuario == interaction.user or cantidad <= 0:
        return await interaction.response.send_message("❌ Operación inválida.", ephemeral=True)
    if banco_datos.get(uid, 0) < cantidad:
        return await interaction.response.send_message("❌ Saldo insuficiente.", ephemeral=True)

    banco_datos[uid] -= cantidad
    banco_datos[tid] = banco_datos.get(tid, 0) + cantidad
    
    emb = discord.Embed(title="💸 TRANSFERENCIA PROCESADA", color=COLOR_SISTEMA)
    emb.description = f"{SEPARADOR}\nSe ha realizado el envío de capital correctamente.\n{SEPARADOR}"
    emb.add_field(name="📤 Remitente", value=interaction.user.mention, inline=True)
    emb.add_field(name="📥 Destinatario", value=usuario.mention, inline=True)
    emb.add_field(name="💰 Monto", value=f"
