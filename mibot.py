import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (RENDER) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot Ultimate System Online 💜"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. BASES DE DATOS TEMPORALES ---
banco_datos = {}
tienda_roles = {} 

# --- 3. VISTAS INTERACTIVAS (TIENDA Y SORTEOS) ---

class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Selecciona un rol para comprar...", options=options, custom_id="select_tienda")

    async def callback(self, interaction: discord.Interaction):
        role_id = self.values[0]
        if role_id == "none": return
        data = tienda_roles.get(int(role_id))
        user_id = str(interaction.user.id)
        user_money = banco_datos.get(user_id, 0)
        if user_money < data['precio']:
            return await interaction.response.send_message(f"Estás pobre, ija. Te faltan ${data['precio'] - user_money}. 💜🤣", ephemeral=True)
        if data['stock'] <= 0:
            return await interaction.response.send_message("¡Se agotó el stock! Ok mañana. 💔", ephemeral=True)
        role = interaction.guild.get_role(int(role_id))
        if role in interaction.user.roles:
            return await interaction.response.send_message("Ya tienes este rol. 🤣", ephemeral=True)
        banco_datos[user_id] -= data['precio']
        tienda_roles[int(role_id)]['stock'] -= 1
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ ¡Compraste **{data['nombre']}**! ¡YIPIEEE! 💜", ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        options = []
        for rid, data in tienda_roles.items():
            if data['stock'] > 0:
                options.append(discord.SelectMenuOption(label=data['nombre'], value=str(rid), description=f"Precio: ${data['precio']} | Stock: {data['stock']}"))
        if not options: options.append(discord.SelectMenuOption(label="Sin stock", value="none"))
        self.add_item(TiendaSelect(options))

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout); self.participantes = []
    @discord.ui.button(label="Participar 🎉", style=discord.ButtonStyle.green, custom_id="give_btn")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes: return await interaction.response.send_message("Ya estás dentro, ija. 🤣", ephemeral=True)
        self.participantes.append(interaction.user); await interaction.response.send_message("¡Anotado! 💜", ephemeral=True)

# --- 4. BOT CORE SETUP ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True; intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Sincronización Total! Todos los comandos están listos. 💜🤣")

    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        banco_datos[uid] = banco_datos.get(uid, 0) + 5
        await self.process_commands(message)

bot = MyBot()

# --- 5. COMANDOS DE TIENDA Y GIVEAWAY ---

@bot.tree.command(name="tienda_config", description="Configura un rol en la tienda (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message(f"✅ **{rol.name}** configurado. 💜", ephemeral=True)

@bot.tree.command(name="tienda", description="Ver la tienda de roles")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("Tienda vacía. 🤣", ephemeral=True)
    emb = discord.Embed(title="🏪 DARKY STORE", description="Compra roles con tus dólares.", color=0x010101)
    for rid, data in tienda_roles.items():
        emb.add_field(name=data['nombre'], value=f"💰 `${data['precio']}`\n📦 Stock: `{data['stock']}`", inline=True)
    await interaction.response.send_message(embed=emb, view=TiendaView())

@bot.tree.command(name="giveaway", description="Sorteo automático")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(unidad=[app_commands.Choice(name="Minutos", value="m"), app_commands.Choice(name="Horas", value="h")])
async def giveaway(interaction: discord.Interaction, tiempo: int, unidad: str, premio: int, canal_ganador: discord.TextChannel):
    seg = tiempo * 60 if unidad == "m" else tiempo * 3600
    final = int(time.time() + seg); view = GiveawayView(timeout=seg)
    emb = discord.Embed(title="🎊 SORTEO 🎊", description=f"💰 **Premio:** `${premio}`\n⏰ **Finaliza:** <t:{final}:R>", color=0x010101)
    await interaction.response.send_message("¡Sorteo iniciado! 🚀", ephemeral=True)
    msg = await interaction.channel.send(embed=emb, view=view)
    await asyncio.sleep(seg)
    if not view.participantes: return await canal_ganador.send("Nadie participó. 🤣")
    ganador = random.choice(view.participantes); banco_datos[str(ganador.id)] = banco_datos.get(str(ganador.id), 0) + premio
    await canal_ganador.send(f"🏆 ¡{ganador.mention} ganó **${premio}**! 💜🤣")

# --- 6. COMANDOS DE ECONOMÍA ---

@bot.tree.command(name="banco", description="Mira tu dinero")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    await interaction.response.send_message(embed=discord.Embed(title=f"🏦 Banco de {target.name}", description=f"Saldo: **${banco_datos.get(str(target.id), 0)}**", color=0x010101))

@bot.tree.command(name="transferir", description="Envía dinero a alguien")
async def transferir(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    aid = str(interaction.user.id)
    if cantidad <= 0 or banco_datos.get(aid, 0) < cantidad:
        return await interaction.response.send_message("Fondos insuficientes, ija. 🤣", ephemeral=True)
    banco_datos[aid] -= cantidad; banco_datos[str(miembro.id)] = banco_datos.get(str(miembro.id), 0) + cantidad
    await interaction.response.send_message(f"✅ Enviaste **${cantidad}** a {miembro.mention}.")

@bot.tree.command(name="regalar", description="Generar dinero (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    banco_datos[str(miembro.id)] = banco_datos.get(str(miembro.id), 0) + cantidad
    await interaction.response.send_message(f"🎁 Regalaste **${cantidad}** a {miembro.mention}. 💜")

# --- 7. COMANDOS SOCIALES Y ÚTILES ---

@bot.tree.command(name="ship", description="Amor entre dos")
async def ship(interaction: discord.Interaction, m1: discord.Member, m2: discord.Member):
    await interaction.response.defer(); p = random.randint(1, 100)
    av1 = io.BytesIO(await m1.display_avatar.read()); av2 = io.BytesIO(await m2.display_avatar.read())
    i1 = Image.open(av1).convert("RGBA").resize((200, 200)); i2 = Image.open(av2).convert("RGBA").resize((200, 200))
    l = Image.new("RGBA", (500, 200), (0, 0, 0, 0)); l.paste(i1, (0, 0)); l.paste(i2, (300, 0))
    o = io.BytesIO(); l.save(o, format='PNG'); o.seek(0)
    await interaction.followup.send(file=discord.File(o, filename="s.png"), embed=discord.Embed(title=f"💘 Ship: {p}%", color=0x010101).set_image(url="attachment://s.png"))

@bot.tree.command(name="avatar", description="Ver avatar")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    await interaction.response.send_message(embed=discord.Embed(title=f"Avatar de {t.name}", color=0x010101).set_image(url=t.display_avatar.url))

@bot.tree.command(name="userinfo", description="Info del usuario")
async def userinfo(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    emb = discord.Embed(title=f"Info de {t.name}", color=0x010101); emb.add_field(name="ID", value=f"`{t.id}`")
    emb.set_thumbnail(url=t.display_avatar.url); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="roblox", description="Perfil Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        uid = r['data'][0]['id']
        await interaction.followup.send(embed=discord.Embed(title=f"Perfil de {usuario}", url=f"https://www.roblox.com/users/{uid}/profile", color=0x010101))
    except: await interaction.followup.send("No lo encontré.")

@bot.tree.command(name="embed", description="Crea un embed")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str):
    await interaction.channel.send(embed=discord.Embed(title=titulo, description=descripcion, color=0x010101))
    await interaction.response.send_message("Ok mañana! 💜", ephemeral=True)

@bot.tree.command(name="delete", description="Borrar mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Borrados {cantidad}. 💜", ephemeral=True)

# --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive(); bot.run(os.getenv('TOKEN'))
