import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (KEEP ALIVE) ---
app = Flask(__name__)
@app.route('/')
def home(): return "DarkyBot Professional System Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. CONFIGURACIÓN ---
COLOR_BOT = 0x2b2d31
SEPARADOR = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
banco_datos = {}
tienda_roles = {} 

# --- 3. VISTAS ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Seleccione un artículo...", options=options, custom_id="sel_t")
    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        if banco_datos.get(uid, 0) < data['precio']:
            return await interaction.response.send_message("Saldo insuficiente.", ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("Rol no disponible.", ephemeral=True)
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"Adquisición confirmada: **{data['nombre']}**.", ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        options = []
        for rid, data in tienda_roles.items():
            if data['stock'] > 0:
                options.append(discord.SelectMenuOption(label=data['nombre'], value=str(rid), description=f"Precio: ${data['precio']}"))
        if not options: options.append(discord.SelectMenuOption(label="Sin existencias", value="none"))
        self.add_item(TiendaSelect(options))

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout); self.participantes = []
    @discord.ui.button(label="Participar", style=discord.ButtonStyle.secondary, emoji="🎟️")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes: return await interaction.response.send_message("Ya registrado.", ephemeral=True)
        self.participantes.append(interaction.user); await interaction.response.send_message("Registro exitoso.", ephemeral=True)

# --- 4. SETUP ---
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

# --- 5. COMANDOS ---
@bot.tree.command(name="tienda_config", description="Configurar tienda")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message(f"Artículo **{rol.name}** configurado.", ephemeral=True)

@bot.tree.command(name="tienda", description="Catálogo")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("Catálogo vacío.", ephemeral=True)
    emb = discord.Embed(title="CATÁLOGO PROFESIONAL", description=SEPARADOR, color=COLOR_BOT)
    for rid, data in tienda_roles.items():
        emb.add_field(name=f"📦 {data['nombre']}", value=f"```💰 ${data['precio']} | 📦 {data['stock']}```", inline=True)
    await interaction.response.send_message(embed=emb, view=TiendaView())

@bot.tree.command(name="banco", description="Saldo")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="ESTADO DE CUENTA", description=SEPARADOR, color=COLOR_BOT)
    emb.add_field(name="Titular", value=t.name, inline=True)
    emb.add_field(name="Saldo", value=f"${saldo:,}", inline=True)
    emb.set_thumbnail(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="giveaway", description="Sorteo")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(unidad=[app_commands.Choice(name="Minutos", value="m"), app_commands.Choice(name="Horas", value="h")])
async def giveaway(interaction: discord.Interaction, tiempo: int, unidad: str, premio: int, canal_ganador: discord.TextChannel):
    seg = tiempo * 60 if unidad == "m" else tiempo * 3600
    view = GiveawayView(timeout=seg)
    emb = discord.Embed(title="SORTEO DE FONDOS", description=f"{SEPARADOR}\nPremio: **${premio}**\nTermina: <t:{int(time.time()+seg)}:R>", color=COLOR_BOT)
    await interaction.response.send_message("Sorteo activo.", ephemeral=True)
    await interaction.channel.send(embed=emb, view=view)
    await asyncio.sleep(seg)
    if not view.participantes: return await canal_ganador.send("Sorteo sin participantes.")
    g = random.choice(view.participantes); banco_datos[str(g.id)] = banco_datos.get(str(g.id), 0) + premio
    res = discord.Embed(title="RESULTADO", description=f"Ganador: {g.mention}\nPremio: **${premio}**", color=COLOR_BOT)
    await canal_ganador.send(embed=res)

@bot.tree.command(name="roblox", description="Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        uid = r['data'][0]['id']
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png").json()
        emb = discord.Embed(title=f"ROBLOX: {usuario.upper()}", url=f"https://www.roblox.com/users/{uid}/profile", color=COLOR_BOT)
        emb.set_image(url=thumb['data'][0]['imageUrl'])
        await interaction.followup.send(embed=emb)
    except: await interaction.followup.send("Error al buscar perfil.")

@bot.tree.command(name="avatar", description="Avatar")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    emb = discord.Embed(title=f"AVATAR DE {t.name.upper()}", color=COLOR_BOT)
    emb.set_image(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="delete", description="Limpiar")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Limpieza de {cantidad} mensajes.", ephemeral=True)

# --- 6. FINAL ORIGINAL ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
