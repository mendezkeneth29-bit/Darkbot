import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time, datetime
from PIL import Image, ImageDraw, ImageFont
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (KEEP ALIVE PARA RENDER) ---
app = Flask('')
@app.route('/')
def home(): return "DarkyBot Professional System Online 💜"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. CONFIGURACIÓN VISUAL Y BASE DE DATOS ---
COLOR_BOT = 0x000001
LINEA = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
banco_datos = {}
tienda_roles = {}
advertencias = {}

# --- 3. COMPONENTES DE INTERFAZ (UI) ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="🛒 Seleccione un artículo del catálogo...", options=options)

    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        
        if banco_datos.get(uid, 0) < data['precio']:
            emb = discord.Embed(title="🚫 TRANSACCIÓN DENEGADA", description=f"{LINEA}\n**Motivo:** Fondos insuficientes.", color=COLOR_BOT)
            return await interaction.response.send_message(embed=emb, ephemeral=True)
            
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("❌ El rol ya no existe.", ephemeral=True)
        
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        emb = discord.Embed(title="✅ COMPRA CONFIRMADA", description=f"{LINEA}\nAdquirido: **{data['nombre']}**\nSaldo: **${banco_datos[uid]:,}**", color=COLOR_BOT)
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
            return await interaction.response.send_message("⚠️ Ya estás en la lista.", ephemeral=True)
        self.participantes.append(interaction.user)
        await interaction.response.send_message("✅ Te has anotado correctamente.", ephemeral=True)

# --- 4. CLASE PRINCIPAL DEL BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="darky!", intents=intents)
    
    async def setup_hook(self):
        await self.tree.sync()
    
    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        banco_datos[uid] = banco_datos.get(uid, 0) + 2
        await self.process_commands(message)

bot = DarkyBot()

# --- 5. COMANDOS DE ECONOMÍA ---
@bot.tree.command(name="work", description="Realizar un turno laboral")
async def work(interaction: discord.Interaction):
    ganancia = random.randint(80, 300)
    uid = str(interaction.user.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + ganancia
    await interaction.response.send_message(f"💼 Has ganado **${ganancia}**.")

@bot.tree.command(name="banco", description="Consultar balance de cuenta")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="💳 BANCO CENTRAL", description=LINEA, color=COLOR_BOT)
    emb.add_field(name="Usuario", value=f"**{t.name}**", inline=True)
    emb.add_field(name="Saldo", value=f"**${saldo:,}**", inline=True)
    emb.set_thumbnail(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="pay", description="Transferir fondos a otro usuario")
async def pay(interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
    uid = str(interaction.user.id)
    if cantidad <= 0 or banco_datos.get(uid, 0) < cantidad:
        return await interaction.response.send_message("❌ Fondos insuficientes.", ephemeral=True)
    banco_datos[uid] -= cantidad
    banco_datos[str(usuario.id)] = banco_datos.get(str(usuario.id), 0) + cantidad
    await interaction.response.send_message(f"✅ Has enviado **${cantidad}** a {usuario.mention}.")

@bot.tree.command(name="regalar", description="Dar dinero administrativo (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    uid = str(miembro.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + cantidad
    emb = discord.Embed(title="🎁 DEPÓSITO ADMINISTRATIVO", color=COLOR_BOT)
    emb.description = f"Se han acreditado **${cantidad:,}** a {miembro.mention}.\nBalance actual: **${banco_datos[uid]:,}**"
    await interaction.response.send_message(embed=emb)

# --- 6. COMANDOS DE ENTRETENIMIENTO ---
@bot.tree.command(name="roblox", description="Muestra perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        uid = r['data'][0]['id']
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png").json()
        avatar_url = thumb['data'][0]['imageUrl']
        emb = discord.Embed(title=f"Perfil de {usuario}", url=f"https://www.roblox.com/users/{uid}/profile", color=COLOR_BOT)
        emb.set_image(url=avatar_url)
        await interaction.followup.send(embed=emb)
    except:
        await interaction.followup.send("❌ No se encontró al usuario.")

@bot.tree.command(name="ship", description="Calcula amor entre dos usuarios")
async def ship(interaction: discord.Interaction, m1: discord.Member, m2: discord.Member):
    await interaction.response.defer()
    p = random.randint(1, 100)
    av1 = io.BytesIO(await m1.display_avatar.read())
    av2 = io.BytesIO(await m2.display_avatar.read())
    i1 = Image.open(av1).convert("RGBA").resize((200, 200))
    i2 = Image.open(av2).convert("RGBA").resize((200, 200))
    l = Image.new("RGBA", (500, 200), (0, 0, 0, 0))
    l.paste(i1, (0, 0)); l.paste(i2, (300, 0))
    o = io.BytesIO(); l.save(o, format='PNG'); o.seek(0)
    emb = discord.Embed(title=f"💘 Afinidad: {p}%", color=COLOR_BOT)
    emb.set_image(url="attachment://ship.png")
    await interaction.followup.send(file=discord.File(o, filename="ship.png"), embed=emb)

# --- 7. ADMINISTRACIÓN ---
@bot.tree.command(name="delete", description="Limpiar mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"✅ Se han borrado {cantidad} mensajes.", ephemeral=True)

# --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ Error: Variable 'TOKEN' no encontrada.")
