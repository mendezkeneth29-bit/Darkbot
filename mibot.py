import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time, datetime
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. CONFIGURACIÓN DE HOSTING (PARA RENDER) ---
app = Flask('')

@app.route('/')
def home(): 
    return "DarkyBot Elite System Online 💜"

def run(): 
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BASE DE DATOS Y ESTÉTICA ---
# Nota: En producción real, usarías una base de datos persistente.
banco_datos = {}
cartera_datos = {} # Dinero que se puede robar
tienda_roles = {}
COLOR_BOT = 0x000001  # NEGRO SUPREMO
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
        
        saldo = banco_datos.get(uid, 0)
        if saldo < data['precio']:
            emb = discord.Embed(title="🚫 TRANSACCIÓN RECHAZADA", description=f"{SEPARADOR}\n**Motivo:** Fondos insuficientes en el banco.", color=COLOR_BOT)
            return await interaction.response.send_message(embed=emb, ephemeral=True)
            
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("❌ El rol ya no existe en el servidor.", ephemeral=True)
        
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        
        emb = discord.Embed(title="✅ ADQUISICIÓN EXITOSA", color=COLOR_BOT)
        emb.description = f"{SEPARADOR}\nHas obtenido: **{data['nombre']}**\nCargo: **${data['precio']:,}**\nNuevo Saldo: **${banco_datos[uid]:,}**"
        await interaction.response.send_message(embed=emb, ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect(options))

# --- 4. CLASE DEL BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="darky!", intents=intents)
    
    async def setup_hook(self):
        await self.tree.sync()
    
    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        # Ganancia pasiva pequeña en cartera
        cartera_datos[uid] = cartera_datos.get(uid, 0) + 5
        await self.process_commands(message)

bot = DarkyBot()

# --- 5. COMANDOS DE ECONOMÍA AVANZADA ---

@bot.tree.command(name="banco", description="Consulta tu balance financiero detallado")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    uid = str(t.id)
    cartera = cartera_datos.get(uid, 0)
    banco = banco_datos.get(uid, 0)
    
    emb = discord.Embed(title=f"🏦 ESTADO DE CUENTA: {t.name.upper()}", color=COLOR_BOT)
    emb.description = SEPARADOR
    emb.add_field(name="💵 Cartera", value=f"

    # --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: TOKEN NO ENCONTRADO.")
