import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time, datetime
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (KEEP ALIVE) ---
app = Flask('')
@app.route('/')
def home(): return "DarkyBot Final Edition Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. CONFIGURACIÓN VISUAL ---
COLOR_BOT = 0x000001
LINEA = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
banco_datos = {}
tienda_roles = {}
advertencias = {}

# --- 3. COMPONENTES UI ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="🛒 Catálogo de artículos...", options=options)
    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        if banco_datos.get(uid, 0) < data['precio']:
            return await interaction.response.send_message(embed=discord.Embed(title="🚫 SALDO INSUFICIENTE", color=COLOR_BOT), ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("❌ Rol no encontrado.", ephemeral=True)
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        await interaction.response.send_message(embed=discord.Embed(title="✅ COMPRA EXITOSA", description=f"Has obtenido: **{data['nombre']}**", color=COLOR_BOT), ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect(options))

class GView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout); self.participantes = []
    @discord.ui.button(label="Participar", style=discord.ButtonStyle.secondary, emoji="🎉")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participantes:
            self.participantes.append(interaction.user); await interaction.response.send_message("🎫 Registrado.", ephemeral=True)
        else: await interaction.response.send_message("⚠️ Ya estas inscrito.", ephemeral=True)

# --- 4. CLASE DEL BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="darky!", intents=intents)
    async def setup_hook(self): await self.tree.sync()
    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        banco_datos[uid] = banco_datos.get(uid, 0) + 2
        await self.process_commands(message)

bot = DarkyBot()

# --- 5. COMANDOS DE ECONOMÍA (NUEVO REGALAR INCLUIDO) ---
@bot.tree.command(name="regalar", description="Asignar dinero a un usuario (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    uid = str(miembro.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + cantidad
    emb = discord.Embed(title="💎 BONIFICACIÓN ADMINISTRATIVA", description=f"{LINEA}\nSe han acreditado **${cantidad:,}** a la cuenta de {miembro.mention}.\n{LINEA}", color=COLOR_BOT)
    emb.set_footer(text=f"Operación realizada por {interaction.user.name}")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="work", description="Trabajar")
async def work(interaction: discord.Interaction):
    ganancia = random.randint(100, 400)
    uid = str(interaction.user.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + ganancia
    emb = discord.Embed(title="💼 TRABAJO FINALIZADO", description=f"Recibiste: **${ganancia}**", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="banco", description="Ver balance")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="💳 BALANCE BANCARIO", description=f"**Usuario:** {t.name}\n**Saldo:** ${saldo:,}", color=COLOR_BOT)
    emb.set_thumbnail(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="slot", description="Casino")
async def slot(interaction: discord.Interaction, apuesta: int):
    uid = str(interaction.user.id)
    if apuesta <= 0 or banco_datos.get(uid, 0) < apuesta: return await interaction.response.send_message("❌ Fondos insuficientes.")
    iconos = ["💎", "🎰", "⭐"]
    r1, r2, r3 = random.choice(iconos), random.choice(iconos), random.choice(iconos)
    if r1 == r2 == r3:
        win = apuesta * 10
        banco_datos[uid] += win
        res = f"🔥 **¡JACKPOT!** +${win}"
    else:
        banco_datos[uid] -= apuesta
        res = f"💀 **Perdiste** -${apuesta}"
    emb = discord.Embed(title="🎰 SLOTS", description=f"`[ {r1} | {r2} | {r3} ]`\n\n{res}", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

# --- 6. INFO Y SOCIAL ---
@bot.tree.command(name="userinfo", description="Perfil de usuario")
async def userinfo(interaction: discord.Interaction, miembro: Optional[discord.Member] = None):
    m = miembro or interaction.user
    emb = discord.Embed(title=f"👤 PERFIL: {m.name}", color=COLOR_BOT)
    emb.add_field(name="ID", value=f"`{m.id}`", inline=False)
    emb.add_field(name="Unión", value=f"<t:{int(m.joined_at.timestamp())}:D>", inline=True)
    emb.set_thumbnail(url=m.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="avatar", description="Ver avatar")
async def avatar(interaction: discord.Interaction, miembro: Optional[discord.Member] = None):
    t = miembro or interaction.user
    emb = discord.Embed(title=f"📸 AVATAR: {t.name}", color=COLOR_BOT)
    emb.set_image(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

# --- 7. MODERACIÓN ---
@bot.tree.command(name="warn", description="Warnear")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, miembro: discord.Member, razon: str):
    uid = str(miembro.id)
    advertencias[uid] = advertencias.get(uid, 0) + 1
    emb = discord.Embed(title="⚠️ WARN", description=f"{miembro.mention} advertido.\n**Razón:** {razon}\n**Total:** {advertencias[uid]}", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="delete", description="Limpiar chat")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(embed=discord.Embed(title="🧹 LIMPIEZA", description=f"Se borraron {cantidad} mensajes.", color=COLOR_BOT), ephemeral=True)

# --- 8. TIENDA Y SORTEOS ---
@bot.tree.command(name="tienda_config", description="Configurar tienda")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message("🛠️ Rol registrado.", ephemeral=True)

@bot.tree.command(name="tienda", description="Ver tienda")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("❌ Tienda vacía.", ephemeral=True)
    emb = discord.Embed(title="🏪 CATÁLOGO", description=LINEA, color=COLOR_BOT)
    opts = []
    for rid, d in tienda_roles.items():
        if d['stock'] > 0:
            emb.add_field(name=f"📦 {d['nombre']}", value=f"Precio: `${d['precio']}`")
            opts.append(discord.SelectMenuOption(label=d['nombre'], value=str(rid)))
    if not opts: return await interaction.response.send_message("❌ Sin stock.")
    await interaction.response.send_message(embed=emb, view=TiendaView(opts))

@bot.tree.command(name="giveaway", description="Sorteo")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, tiempo_min: int, premio: int, canal: discord.TextChannel):
    seg = tiempo_min * 60
    v = GView(timeout=seg)
    emb = discord.Embed(title="🎁 SORTEO", description=f"Premio: **${premio}**\nTermina: <t:{int(time.time()+seg)}:R>", color=COLOR_BOT)
    await interaction.response.send_message("✅ Iniciado.", ephemeral=True)
    await canal.send(embed=emb, view=v)
    await asyncio.sleep(seg)
    if not v.participantes: return await canal.send("⚠️ Nadie participó.")
    ganador = random.choice(v.participantes)
    banco_datos[str(ganador.id)] = banco_datos.get(str(ganador.id), 0) + premio
    await canal.send(embed=discord.Embed(title="🎉 GANADOR", description=f"{ganador.mention} ganó ${premio}", color=COLOR_BOT))

# --- 9. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("TOKEN")
    if token: bot.run(token)
    else: print("❌ Error: TOKEN no configurado.")
