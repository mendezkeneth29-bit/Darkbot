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
COLOR_EXITO = 0x43b581
COLOR_ERROR = 0xf04747
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
            emb = discord.Embed(title="TRANSACCIÓN FALLIDA", description="Saldo insuficiente para completar la compra.", color=COLOR_ERROR)
            return await interaction.response.send_message(embed=emb, ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        if not role: 
            emb = discord.Embed(title="ERROR DE SISTEMA", description="El artículo seleccionado ya no se encuentra en el servidor.", color=COLOR_ERROR)
            return await interaction.response.send_message(embed=emb, ephemeral=True)
        
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        emb = discord.Embed(title="COMPRA EXITOSA", description=f"Has adquirido el artículo: **{data['nombre']}**.", color=COLOR_EXITO)
        await interaction.response.send_message(embed=emb, ephemeral=True)

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
        if interaction.user in self.participantes:
            return await interaction.response.send_message("Ya te encuentras registrado en este sorteo.", ephemeral=True)
        self.participantes.append(interaction.user)
        await interaction.response.send_message("Inscripción confirmada correctamente.", ephemeral=True)

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
@bot.tree.command(name="tienda_config", description="Configurar inventario")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    emb = discord.Embed(title="CONFIGURACIÓN DE TIENDA", description=f"Artículo **{rol.name}** registrado correctamente.", color=COLOR_EXITO)
    await interaction.response.send_message(embed=emb, ephemeral=True)

@bot.tree.command(name="tienda", description="Ver catálogo")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles:
        emb = discord.Embed(title="CATÁLOGO VACÍO", description="No hay artículos registrados en la tienda.", color=COLOR_ERROR)
        return await interaction.response.send_message(embed=emb, ephemeral=True)
    emb = discord.Embed(title="CATÁLOGO PROFESIONAL", description=SEPARADOR, color=COLOR_BOT)
    for rid, data in tienda_roles.items():
        emb.add_field(name=f"📦 {data['nombre']}", value=f"```💰 ${data['precio']} | 📦 {data['stock']}```", inline=True)
    await interaction.response.send_message(embed=emb, view=TiendaView())

@bot.tree.command(name="banco", description="Ver saldo")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="ESTADO DE CUENTA", description=SEPARADOR, color=COLOR_BOT)
    emb.add_field(name="Usuario", value=f"**{t.name}**", inline=True)
    emb.add_field(name="Saldo", value=f"**${saldo:,}**", inline=True)
    emb.set_thumbnail(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="transferir", description="Enviar dinero")
async def transferir(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    aid = str(interaction.user.id)
    if cantidad <= 0 or banco_datos.get(aid, 0) < cantidad:
        emb = discord.Embed(title="ERROR DE TRANSFERENCIA", description="Fondos insuficientes o cantidad inválida.", color=COLOR_ERROR)
        return await interaction.response.send_message(embed=emb, ephemeral=True)
    banco_datos[aid] -= cantidad
    banco_datos[str(miembro.id)] = banco_datos.get(str(miembro.id), 0) + cantidad
    emb = discord.Embed(title="TRANSFERENCIA REALIZADA", description=f"Se han enviado **${cantidad}** a {miembro.mention}.", color=COLOR_EXITO)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="regalar", description="Asignar fondos (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    banco_datos[str(miembro.id)] = banco_datos.get(str(miembro.id), 0) + cantidad
    emb = discord.Embed(title="DEPÓSITO DE ADMINISTRACIÓN", description=f"Se han acreditado **${cantidad}** a {miembro.mention}.", color=COLOR_EXITO)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="giveaway", description="Lanzar sorteo")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(unidad=[app_commands.Choice(name="Minutos", value="m"), app_commands.Choice(name="Horas", value="h")])
async def giveaway(interaction: discord.Interaction, tiempo: int, unidad: str, premio: int, canal_ganador: discord.TextChannel):
    seg = tiempo * 60 if unidad == "m" else tiempo * 3600
    view = GiveawayView(timeout=seg)
    emb = discord.Embed(title="SORTEO ACTIVO", description=f"{SEPARADOR}\nPremio: **${premio}**\nFinaliza: <t:{int(time.time()+seg)}:R>", color=COLOR_BOT)
    await interaction.response.send_message("Sorteo programado.", ephemeral=True)
    await interaction.channel.send(embed=emb, view=view)
    await asyncio.sleep(seg)
    if not view.participantes:
        return await canal_ganador.send(embed=discord.Embed(title="SORTEO FINALIZADO", description="No hubo participantes en el sorteo.", color=COLOR_ERROR))
    g = random.choice(view.participantes)
    banco_datos[str(g.id)] = banco_datos.get(str(g.id), 0) + premio
    res = discord.Embed(title="GANADOR DEL SORTEO", description=f"Usuario: {g.mention}\nPremio: **${premio}**", color=COLOR_EXITO)
    await canal_ganador.send(embed=res)

@bot.tree.command(name="roblox", description="Perfil Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        uid = r['data'][0]['id']
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png").json()
        emb = discord.Embed(title=f"PERFIL: {usuario.upper()}", url=f"https://www.roblox.com/users/{uid}/profile", color=COLOR_BOT)
        emb.set_image(url=thumb['data'][0]['imageUrl'])
        await interaction.followup.send(embed=emb)
    except:
        await interaction.followup.send(embed=discord.Embed(title="ERROR", description="No se encontró el usuario en Roblox.", color=COLOR_ERROR))

@bot.tree.command(name="avatar", description="Ver avatar")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    emb = discord.Embed(title=f"AVATAR DE {t.name.upper()}", color=COLOR_BOT)
    emb.set_image(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="delete", description="Limpiar chat")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    emb = discord.Embed(title="LIMPIEZA DE CANAL", description=f"Se han eliminado **{cantidad}** mensajes.", color=COLOR_EXITO)
    await interaction.response.send_message(embed=emb, ephemeral=True)

# --- 6. FINAL ORIGINAL ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
