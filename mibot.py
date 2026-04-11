import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. CONFIGURACIÓN DE HOSTING (PARA RENDER) ---
app = Flask('')

@app.route('/')
def home(): 
    return "DarkyBot Ultimate System Online 💜"

def run(): 
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BASE DE DATOS Y ESTÉTICA ---
banco_datos = {}
tienda_roles = {}
COLOR_BOT = 0x000001  # NEGRO SUPREMO
SEPARADOR = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# --- 3. COMPONENTES DE INTERFAZ ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="🛒 Selecciona un producto...", options=options)

    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        
        if banco_datos.get(uid, 0) < data['precio']:
            emb = discord.Embed(title="🚫 SALDO INSUFICIENTE", color=COLOR_BOT)
            return await interaction.response.send_message(embed=emb, ephemeral=True)
            
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("❌ El rol no existe.", ephemeral=True)
        
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        
        emb = discord.Embed(title="✅ COMPRA EXITOSA", description=f"Has adquirido: **{data['nombre']}**\nSaldo restante: **${banco_datos[uid]:,}**", color=COLOR_BOT)
        await interaction.response.send_message(embed=emb, ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect(options))

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.participantes = []
    
    @discord.ui.button(label="Participar 🎉", style=discord.ButtonStyle.green)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes:
            return await interaction.response.send_message("⚠️ Ya estás dentro.", ephemeral=True)
        self.participantes.append(interaction.user)
        await interaction.response.send_message("✅ ¡Registrado para el sorteo!", ephemeral=True)

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
        # Ganancia pasiva por actividad
        banco_datos[uid] = banco_datos.get(uid, 0) + 15 
        await self.process_commands(message)

bot = DarkyBot()

# --- 5. COMANDOS DE ECONOMÍA ---

@bot.tree.command(name="work", description="Trabajar para el bot")
async def work(interaction: discord.Interaction):
    ganancia = random.randint(300, 1000)
    uid = str(interaction.user.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + ganancia
    emb = discord.Embed(title="💼 TRABAJO", description=f"Ganaste **${ganancia:,}**.", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="banco", description="Ver tus fondos")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="🏦 CUENTA BANCARIA", description=f"{SEPARADOR}\n**Usuario:** {t.mention}\n**Saldo:** `${saldo:,} USD`", color=COLOR_BOT)
    emb.set_thumbnail(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="regalar", description="Regalar dinero (Admins infinito)")
async def regalar(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    uid, tid = str(interaction.user.id), str(miembro.id)
    es_admin = interaction.user.guild_permissions.administrator

    if miembro.bot or miembro == interaction.user or cantidad <= 0:
        return await interaction.response.send_message("❌ Operación denegada.", ephemeral=True)

    if not es_admin:
        if banco_datos.get(uid, 0) < cantidad:
            return await interaction.response.send_message(f"❌ No tienes suficiente dinero.", ephemeral=True)
        banco_datos[uid] -= cantidad
    
    banco_datos[tid] = banco_datos.get(tid, 0) + cantidad
    
    emb = discord.Embed(title="💠 TRANSFERENCIA", color=COLOR_BOT)
    emb.description = f"{SEPARADOR}\n**Emisor:** {interaction.user.mention}\n**Receptor:** {miembro.mention}\n**Monto:** `${cantidad:,}`\n{SEPARADOR}"
    emb.set_footer(text="Inyección administrativa" if es_admin else "Transferencia de usuario")
    await interaction.response.send_message(embed=emb)

# --- 6. COMANDOS SOCIALES ---

@bot.tree.command(name="roblox", description="Consultar perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        rid = r['data'][0]['id']
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={rid}&size=420x420&format=Png").json()
        emb = discord.Embed(title=f"👤 PERFIL: {usuario}", url=f"https://www.roblox.com/users/{rid}/profile", color=COLOR_BOT)
        emb.set_image(url=thumb['data'][0]['imageUrl'])
        await interaction.followup.send(embed=emb)
    except:
        await interaction.followup.send("❌ Usuario no encontrado.")

@bot.tree.command(name="avatar", description="Ver avatar de un usuario")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    emb = discord.Embed(title=f"Avatar de {t.name}", color=COLOR_BOT)
    emb.set_image(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

# --- 7. ADMINISTRACIÓN ---

@bot.tree.command(name="tienda_config", description="Configurar la tienda (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message(f"✅ Rol **{rol.name}** añadido.", ephemeral=True)

@bot.tree.command(name="tienda", description="Ver la tienda")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("🛒 Tienda vacía.", ephemeral=True)
    options = []
    emb = discord.Embed(title="🏪 DARKY STORE", description=SEPARADOR, color=COLOR_BOT)
    for rid, data in tienda_roles.items():
        if data['stock'] > 0:
            emb.add_field(name=data['nombre'], value=f"💰 `${data['precio']:,}` | 📦 `{data['stock']}`", inline=True)
            options.append(discord.SelectMenuOption(label=data['nombre'], value=str(rid)))
    if not options: return await interaction.response.send_message("🛒 Sin stock.", ephemeral=True)
    await interaction.response.send_message(embed=emb, view=TiendaView(options))

@bot.tree.command(name="clear", description="Limpiar chat")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"✅ Borrados {cantidad}.", ephemeral=True)

# --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: TOKEN NO ENCONTRADO.")
