import discord
from discord import app_commands
from discord.ext import commands
import os, random, asyncio, time
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (KEEP ALIVE PARA RENDER) ---
app = Flask('')
@app.route('/')
def home(): return "DarkyBot Premium Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. CONFIGURACIÓN VISUAL Y DATOS ---
COLOR_BOT = 0x000001
SEP_G = "『 ━━━━━━━━━━━━━━━━━━━━━━━ 』"
SEP_S = "─" * 35
banco_datos = {}
tienda_roles = {}
advertencias = {}

# --- 3. COMPONENTES UI (INTERFAZ) ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="💠 Explora el catálogo de élite...", options=options)
    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        if banco_datos.get(uid, 0) < data['precio']:
            emb = discord.Embed(title="❌ TRANSACCIÓN FALLIDA", description=f"**Motivo:** Fondos insuficientes.\n**Costo:** `${data['precio']}`", color=COLOR_BOT)
            return await interaction.response.send_message(embed=emb, ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        if not role: return await interaction.response.send_message("❌ Rol no encontrado.", ephemeral=True)
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        emb = discord.Embed(title="💎 ADQUISICIÓN EXITOSA", description=f"{SEP_G}\n• **Objeto:** {data['nombre']}\n• **Saldo Restante:** `${banco_datos[uid]:,}`\n{SEP_G}", color=COLOR_BOT)
        await interaction.response.send_message(embed=emb, ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect(options))

class GView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout); self.participantes = []
    @discord.ui.button(label="Obtener Ticket", style=discord.ButtonStyle.secondary, emoji="🎟️")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participantes:
            self.participantes.append(interaction.user)
            await interaction.response.send_message("✅ ¡Registrado!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Ya tienes ticket.", ephemeral=True)

# --- 4. CLASE DEL BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="darky!", intents=intents)
    async def setup_hook(self): await self.tree.sync()

bot = DarkyBot()

# --- 5. COMANDOS ---
@bot.tree.command(name="regalar", description="👑 Inyectar capital (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    uid = str(miembro.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + cantidad
    emb = discord.Embed(title="💠 CRÉDITO ADMINISTRATIVO", description=SEP_G, color=COLOR_BOT)
    emb.add_field(name="📥 Destinatario", value=miembro.mention, inline=True)
    emb.add_field(name="💰 Monto", value=f"`$ {cantidad:,}`", inline=True)
    emb.set_footer(text=f"Autorizado por: {interaction.user.name}")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="work", description="⚒️ Trabajar")
async def work(interaction: discord.Interaction):
    pago = random.randint(200, 600)
    uid = str(interaction.user.id)
    banco_datos[uid] = banco_datos.get(uid, 0) + pago
    emb = discord.Embed(title="⚒️ REPORTE LABORAL", description=f"Ganaste: `$ {pago}`\nTotal: `$ {banco_datos[uid]:,}`", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="banco", description="🏦 Ver balance")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title="🏦 BÓVEDA", description=f"Usuario: {t.mention}\nBalance: **$ {saldo:,}**", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="tienda", description="🏪 Ver catálogo")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("❌ Tienda vacía.")
    emb = discord.Embed(title="🏪 CATÁLOGO", color=COLOR_BOT)
    opts = []
    for rid, d in tienda_roles.items():
        if d['stock'] > 0:
            emb.add_field(name=f"📦 {d['nombre']}", value=f"Precio: `${d['precio']}`", inline=True)
            opts.append(discord.SelectMenuOption(label=d['nombre'], value=str(rid)))
    await interaction.response.send_message(embed=emb, view=TiendaView(opts))

@bot.tree.command(name="tienda_config", description="⚙️ Configurar tienda")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message("✅ Configurado.", ephemeral=True)

@bot.tree.command(name="giveaway", description="🎉 Iniciar sorteo")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, tiempo_min: int, premio: int, canal: discord.TextChannel):
    seg = tiempo_min * 60
    v = GView(timeout=seg)
    emb = discord.Embed(title="🎉 SORTEO", description=f"Premio: **${premio:,}**\nFinaliza: <t:{int(time.time()+seg)}:R>", color=COLOR_BOT)
    await interaction.response.send_message("✅ Lanzado.", ephemeral=True)
    await canal.send(embed=emb, view=v)
    await asyncio.sleep(seg)
    if not v.participantes: return await canal.send("⚠️ Sin participantes.")
    ganador = random.choice(v.participantes)
    banco_datos[str(ganador.id)] = banco_datos.get(str(ganador.id), 0) + premio
    await canal.send(embed=discord.Embed(title="🏆 GANADOR", description=f"{ganador.mention} ganó **${premio:,}**", color=COLOR_BOT))

# --- 9. EJECUCIÓN FINAL (ESTO ES LO QUE PEDISTE AL FINAL) ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ CRITICAL: TOKEN NOT FOUND")
