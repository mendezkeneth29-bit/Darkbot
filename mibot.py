import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time, datetime
from PIL import Image, ImageDraw, ImageFont
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (KEEP ALIVE) ---
app = Flask('')
@app.route('/')
def home(): return "DarkyBot Professional System Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. CONFIGURACIÓN VISUAL ---
COLOR_BOT = 0x000001
LINEA = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
banco_datos = {}
tienda_roles = {}
advertencias = {}

# --- 3. COMPONENTES UI (SISTEMA DE TIENDA Y SORTEOS) ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="🛒 Seleccione un artículo del catálogo...", options=options)

    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        if banco_datos.get(uid, 0) < data['precio']:
            emb = discord.Embed(title="🚫 TRANSACCIÓN DENEGADA", description=f"{LINEA}\n**Motivo:** Fondos insuficientes en su cuenta bancaria.", color=COLOR_BOT)
            return await interaction.response.send_message(embed=emb, ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        if not role: 
            return await interaction.response.send_message("❌ Error: El rol ya no existe.", ephemeral=True)
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        emb = discord.Embed(title="✅ COMPRA CONFIRMADA", description=f"{LINEA}\nHa adquirido: **{data['nombre']}**\nSu nuevo saldo: **${banco_datos[uid]:,}**", color=COLOR_BOT)
        await interaction.response.send_message(embed=emb, ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect(options))

class GView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout); self.participantes = []
    @discord.ui.button(label="Inscribirse al Sorteo", style=discord.ButtonStyle.secondary, emoji="🎟️")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participantes:
            self.participantes.append(interaction.user)
            await interaction.response.send_message("🎫 Su participación ha sido registrada.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Ya se encuentra inscrito.", ephemeral=True)

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
        banco_datos[uid] = banco_datos.get(uid, 0) + 2
        await self.process_commands(message)

bot = DarkyBot()

# --- 5. COMANDOS DE ECONOMÍA ---
@bot.tree.command(name="work", description="Realizar un turno laboral")
async def work(interaction: discord.Interaction):
    ganancia = random.randint(80, 300)
    uid = str(interaction.user.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + ganancia
    emb = discord.Embed(title="💼 JORNADA LABORAL", description=f"{LINEA}\nHas trabajado con éxito y recibiste: **${ganancia}**.\nTu balance actual: **${banco_datos[uid]:,}**", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="banco", description="Ver su estado de cuenta")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="💳 REGISTRO FINANCIERO", description=LINEA, color=COLOR_BOT)
    emb.add_field(name="Titular de la cuenta", value=f"**{t.name}**", inline=False)
    emb.add_field(name="Saldo Total", value=f"**${saldo:,}**", inline=True)
    emb.set_thumbnail(url=t.display_avatar.url)
    emb.set_footer(text=f"ID de Usuario: {t.id}")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="slot", description="Casino: Tragamonedas")
async def slot(interaction: discord.Interaction, apuesta: int):
    uid = str(interaction.user.id)
    if apuesta <= 0 or banco_datos.get(uid, 0) < apuesta:
        return await interaction.response.send_message("❌ Fondos insuficientes.")
    iconos = ["💎", "🎰", "🍒", "🍎", "🔔", "⭐"]
    r1, r2, r3 = random.choice(iconos), random.choice(iconos), random.choice(iconos)
    if r1 == r2 == r3:
        win = apuesta * 8
        banco_datos[uid] += win
        res = f"🌟 **¡JACKPOT!** Has ganado **${win}**"
    elif r1 == r2 or r2 == r3 or r1 == r3:
        win = apuesta * 2
        banco_datos[uid] += win
        res = f"✨ **¡GANASTE!** Has ganado **${win}**"
    else:
        banco_datos[uid] -= apuesta
        res = f"💔 **¡PERDISTE!** Perdiste **${apuesta}**"
    emb = discord.Embed(title="🎰 MÁQUINA DE CASINO", description=f"{LINEA}\n**Resultado:**\n`[ {r1} | {r2} | {r3} ]`\n{LINEA}\n{res}", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="pay", description="Transferir fondos a otro usuario")
async def pay(interaction: discord.Interaction, usuario: discord.Member, cantidad: int):
    uid = str(interaction.user.id)
    if cantidad <= 0 or banco_datos.get(uid, 0) < cantidad:
        return await interaction.response.send_message("❌ Fondos insuficientes.", ephemeral=True)
    banco_datos[uid] -= cantidad
    banco_datos[str(usuario.id)] = banco_datos.get(str(usuario.id), 0) + cantidad
    emb = discord.Embed(title="💸 TRANSFERENCIA EXITOSA", description=f"{LINEA}\nHas enviado **${cantidad}** a {usuario.mention}.", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

# --- 6. COMANDOS DE INFORMACIÓN ---
@bot.tree.command(name="userinfo", description="Ficha técnica de un usuario")
async def userinfo(interaction: discord.Interaction, miembro: Optional[discord.Member] = None):
    m = miembro or interaction.user
    emb = discord.Embed(title=f"👤 PERFIL: {m.name.upper()}", description=LINEA, color=COLOR_BOT)
    emb.add_field(name="ID de Discord", value=f"`{m.id}`", inline=False)
    emb.add_field(name="Fecha de Creación", value=f"<t:{int(m.created_at.timestamp())}:D>", inline=True)
    emb.add_field(name="Ingreso al Server", value=f"<t:{int(m.joined_at.timestamp())}:D>", inline=True)
    emb.add_field(name="Roles", value=len(m.roles)-1, inline=True)
    emb.set_thumbnail(url=m.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="serverinfo", description="Resumen del servidor")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    emb = discord.Embed(title=f"🏰 SISTEMA: {g.name.upper()}", description=LINEA, color=COLOR_BOT)
    emb.add_field(name="Fundador", value=g.owner.mention, inline=True)
    emb.add_field(name="Miembros", value=f"👥 {g.member_count}", inline=True)
    emb.add_field(name="Nivel de Boost", value=f"💎 {g.premium_tier}", inline=True)
    emb.add_field(name="Canales", value=f"💬 {len(g.channels)}", inline=True)
    emb.add_field(name="Roles", value=f"🏷️ {len(g.roles)}", inline=True)
    if g.icon: emb.set_thumbnail(url=g.icon.url)
    await interaction.response.send_message(embed=emb)

# --- 7. MODERACIÓN Y UTILIDAD ---
@bot.tree.command(name="warn", description="Aplicar advertencia administrativa")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, miembro: discord.Member, razon: str):
    uid = str(miembro.id)
    advertencias[uid] = advertencias.get(uid, 0) + 1
    emb = discord.Embed(title="⚠️ ADVERTENCIA REGISTRADA", description=f"{LINEA}\n**Usuario:** {miembro.mention}\n**Motivo:** {razon}\n**Total Warns:** {advertencias[uid]}", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="delete", description="Limpieza de historial del canal")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    emb = discord.Embed(title="🧹 LIMPIEZA COMPLETADA", description=f"Se han eliminado **{cantidad}** mensajes.", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb, ephemeral=True)

@bot.tree.command(name="avatar", description="Ver avatar en alta resolución")
async def avatar(interaction: discord.Interaction, miembro: Optional[discord.Member] = None):
    t = miembro or interaction.user
    emb = discord.Embed(title=f"📸 IMAGEN DE {t.name.upper()}", color=COLOR_BOT)
    emb.set_image(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

# --- 8. ENTRETENIMIENTO ---
@bot.tree.command(name="ship", description="Calculadora de afinidad amorosa")
async def ship(interaction: discord.Interaction, m1: discord.Member, m2: discord.Member):
    await interaction.response.defer()
    p = random.randint(1, 100)
    av1 = io.BytesIO(await m1.display_avatar.read())
    av2 = io.BytesIO(await m2.display_avatar.read())
    i1, i2 = Image.open(av1).convert("RGBA").resize((200, 200)), Image.open(av2).convert("RGBA").resize((200, 200))
    l = Image.new("RGBA", (500, 200), (0, 0, 0, 0))
    l.paste(i1, (0, 0)); l.paste(i2, (300, 0))
    o = io.BytesIO(); l.save(o, format='PNG'); o.seek(0)
    emb = discord.Embed(title="❤️ COMPATIBILIDAD", description=f"{LINEA}\n**{m1.name}** & **{m2.name}**\nNivel de amor: **{p}%**", color=COLOR_BOT)
    emb.set_image(url="attachment://ship.png")
    await interaction.followup.send(file=discord.File(o, filename="ship.png"), embed=emb)

@bot.tree.command(name="roblox", description="Ver perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        uid = r['data'][0]['id']
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png").json()
        emb = discord.Embed(title=f"🎮 ROBLOX: {usuario.upper()}", url=f"https://www.roblox.com/users/{uid}/profile", color=COLOR_BOT)
        emb.set_image(url=thumb['data'][0]['imageUrl'])
        await interaction.followup.send(embed=emb)
    except: await interaction.followup.send("❌ No se encontró el usuario.")

# --- 9. CONFIGURACIÓN DE TIENDA Y SORTEOS ---
@bot.tree.command(name="tienda_config", description="Registrar rol en la tienda")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    emb = discord.Embed(title="🛠️ CONFIGURACIÓN", description=f"Artículo **{rol.name}** registrado en inventario.", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb, ephemeral=True)

@bot.tree.command(name="tienda", description="Ver catálogo de artículos")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("❌ La tienda está vacía.", ephemeral=True)
    emb = discord.Embed(title="🏪 CATÁLOGO PROFESIONAL", description=LINEA, color=COLOR_BOT)
    opts = []
    for rid, d in tienda_roles.items():
        if d['stock'] > 0:
            emb.add_field(name=f"📦 {d['nombre']}", value=f"Precio: `${d['precio']}`\nStock: `{d['stock']}`")
            opts.append(discord.SelectMenuOption(label=d['nombre'], value=str(rid)))
    if not opts: return await interaction.response.send_message("❌ No hay stock disponible.")
    await interaction.response.send_message(embed=emb, view=TiendaView(opts))

@bot.tree.command(name="giveaway", description="Lanzar un sorteo de créditos")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, tiempo_min: int, premio: int, canal: discord.TextChannel):
    seg = tiempo_min * 60
    v = GView(timeout=seg)
    emb = discord.Embed(title="🎁 EVENTO DE SORTEO", description=f"{LINEA}\nPremio: **${premio}**\nFinaliza en: <t:{int(time.time()+seg)}:R>", color=COLOR_BOT)
    await interaction.response.send_message("✅ Sorteo iniciado.", ephemeral=True)
    await canal.send(embed=emb, view=v)
    await asyncio.sleep(seg)
    if not v.participantes: return await canal.send("⚠️ Sorteo anulado por falta de participantes.")
    ganador = random.choice(v.participantes)
    banco_datos[str(ganador.id)] = banco_datos.get(str(ganador.id), 0) + premio
    res = discord.Embed(title="🎉 GANADOR DEL SORTEO", description=f"{ganador.mention} ha ganado la recompensa de **${premio}**.", color=COLOR_BOT)
    await canal.send(embed=res)

# --- 10. EJECUCIÓN FINAL (COMPATIBLE CON RENDER) ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ Error Fatal: No se encontró la variable 'TOKEN' en el sistema.")
