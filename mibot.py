import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. SERVIDOR INTERNO PARA RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "DarkyBot esta vivo y operando."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. CONFIGURACIÓN VISUAL ---
COLOR_BOT = 0x000001
LINEA = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
banco_datos = {}
tienda_roles = {}
advertencias = {}

# --- 3. VISTAS DE INTERFAZ ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Selección de catálogo...", options=options)

    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        if banco_datos.get(uid, 0) < data['precio']:
            return await interaction.response.send_message(embed=discord.Embed(title="SISTEMA", description="Fondos insuficientes.", color=COLOR_BOT), ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("Error: Rol no encontrado.", ephemeral=True)
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        await interaction.response.send_message(embed=discord.Embed(title="COMPRA", description=f"Obtenido: **{data['nombre']}**", color=COLOR_BOT), ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect(options))

class GView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.participantes = []
    @discord.ui.button(label="Participar", style=discord.ButtonStyle.secondary, emoji="🎉")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participantes:
            self.participantes.append(interaction.user)
            await interaction.response.send_message("Registrado.", ephemeral=True)
        else:
            await interaction.response.send_message("Ya estas dentro.", ephemeral=True)

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
        banco_datos[uid] = banco_datos.get(uid, 0) + 1
        await self.process_commands(message)

bot = DarkyBot()

# --- 5. COMANDOS ---
@bot.tree.command(name="work", description="Ganar dinero")
async def work(interaction: discord.Interaction):
    ganancia = random.randint(50, 200)
    uid = str(interaction.user.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + ganancia
    await interaction.response.send_message(embed=discord.Embed(title="TRABAJO", description=f"Ganaste **${ganancia}**.", color=COLOR_BOT))

@bot.tree.command(name="banco", description="Ver balance")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="BANCO", color=COLOR_BOT)
    emb.add_field(name="Usuario", value=t.name)
    emb.add_field(name="Saldo", value=f"${saldo:,}")
    emb.set_thumbnail(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="slot", description="Casino")
async def slot(interaction: discord.Interaction, apuesta: int):
    uid = str(interaction.user.id)
    if apuesta <= 0 or banco_datos.get(uid, 0) < apuesta:
        return await interaction.response.send_message("Fondos insuficientes.")
    iconos = ["💎", "🎰", "🍒", "🍎"]
    r1, r2, r3 = random.choice(iconos), random.choice(iconos), random.choice(iconos)
    if r1 == r2 == r3:
        win = apuesta * 5
        banco_datos[uid] += win
        res = f"¡GANASTE! +${win}"
    else:
        banco_datos[uid] -= apuesta
        res = f"Perdiste -${apuesta}"
    emb = discord.Embed(title="SLOTS", description=f"{r1} | {r2} | {r3}\n\n{res}", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="userinfo", description="Info usuario")
async def userinfo(interaction: discord.Interaction, miembro: Optional[discord.Member] = None):
    m = miembro or interaction.user
    emb = discord.Embed(title=f"INFO: {m.name}", color=COLOR_BOT)
    emb.add_field(name="ID", value=m.id, inline=False)
    emb.add_field(name="Cuenta", value=f"<t:{int(m.created_at.timestamp())}:D>")
    emb.set_thumbnail(url=m.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="warn", description="Warnear")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, miembro: discord.Member, razon: str):
    uid = str(miembro.id)
    advertencias[uid] = advertencias.get(uid, 0) + 1
    emb = discord.Embed(title="WARN", description=f"{miembro.mention} advertido.\nTotal: {advertencias[uid]}", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="tienda_config", description="Configurar tienda")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message("Configurado.", ephemeral=True)

@bot.tree.command(name="tienda", description="Ver tienda")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("Tienda vacía.", ephemeral=True)
    emb = discord.Embed(title="TIENDA", description=LINEA, color=COLOR_BOT)
    options = []
    for rid, d in tienda_roles.items():
        if d['stock'] > 0:
            emb.add_field(name=d['nombre'], value=f"Precio: ${d['precio']}\nStock: {d['stock']}")
            options.append(discord.SelectMenuOption(label=d['nombre'], value=str(rid)))
    if not options: return await interaction.response.send_message("Sin stock.")
    await interaction.response.send_message(embed=emb, view=TiendaView(options))

@bot.tree.command(name="giveaway", description="Sorteo")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, tiempo_min: int, premio: int, canal: discord.TextChannel):
    seg = tiempo_min * 60
    v = GView(timeout=seg)
    emb = discord.Embed(title="SORTEO", description=f"Premio: **${premio}**\nTermina: <t:{int(time.time()+seg)}:R>", color=COLOR_BOT)
    await interaction.response.send_message("Lanzado.", ephemeral=True)
    await canal.send(embed=emb, view=v)
    await asyncio.sleep(seg)
    if not v.participantes: return await canal.send("Nadie participo.")
    ganador = random.choice(v.participantes)
    banco_datos[str(ganador.id)] = banco_datos.get(str(ganador.id), 0) + premio
    await canal.send(embed=discord.Embed(title="GANADOR", description=f"{ganador.mention} gano ${premio}", color=COLOR_BOT))

# --- 6. INICIO ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("TOKEN")
    if token:
        bot.run(token)
    else:
        print("Error: No se encontro el TOKEN en las variables de entorno.")
