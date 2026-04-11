import discord
from discord import app_commands
from discord.ext import commands
import os, requests, random, io, asyncio, time
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot Ultimate Online 💜"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. BASE DE DATOS ---
banco_datos = {}
tienda_roles = {} 

# --- 3. VISTAS (BOTONES Y SELECTORES) ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Elige un rol para comprar...", options=options, custom_id="sel_t")
    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        if banco_datos.get(uid, 0) < data['precio']:
            return await interaction.response.send_message("No tienes dinero suficiente, ija. 🤣", ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
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
    @discord.ui.button(label="Participar 🎉", style=discord.ButtonStyle.green)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes: return await interaction.response.send_message("¡Ya estás participando! 🤣", ephemeral=True)
        self.participantes.append(interaction.user); await interaction.response.send_message("¡Ok mañana! Te has anotado. 💜", ephemeral=True)

# --- 4. BOT SETUP ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True; intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)
    async def setup_hook(self):
        await self.tree.sync()
        print("¡Sincronización Total! 💜🤣")
bot = MyBot()

# --- 5. COMANDOS DE ADMINISTRACIÓN Y TIENDA ---

@bot.tree.command(name="tienda_config", description="Configura un rol en la tienda (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message(f"✅ Configurado: {rol.name} a ${precio}. 💜", ephemeral=True)

@bot.tree.command(name="tienda", description="Abre la tienda de roles")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("La tienda está vacía. 🤣", ephemeral=True)
    emb = discord.Embed(title="🏪 DARKY STORE", color=0x010101)
    for rid, data in tienda_roles.items():
        emb.add_field(name=data['nombre'], value=f"💰 `${data['precio']}` | 📦 `{data['stock']}`")
    await interaction.response.send_message(embed=emb, view=TiendaView())

@bot.tree.command(name="giveaway", description="Sorteo de dinero automático")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(unidad=[app_commands.Choice(name="Minutos", value="m"), app_commands.Choice(name="Horas", value="h")])
async def giveaway(interaction: discord.Interaction, tiempo: int, unidad: str, premio: int, canal_ganador: discord.TextChannel):
    seg = tiempo * 60 if unidad == "m" else tiempo * 3600
    final = int(time.time() + seg); view = GiveawayView(timeout=seg)
    emb = discord.Embed(title="🎊 SORTEO ACTIVO 🎊", description=f"💰 **Premio:** `${premio}`\n⏰ **Termina:** <t:{final}:R>", color=0x010101)
    await interaction.response.send_message("Sorteo lanzado. 🚀", ephemeral=True)
    msg = await interaction.channel.send(embed=emb, view=view)
    await asyncio.sleep(seg)
    if not view.participantes: return await canal_ganador.send("Nadie participó. 🤣")
    g = random.choice(view.participantes); banco_datos[str(g.id)] = banco_datos.get(str(g.id), 0) + premio
    await canal_ganador.send(f"🏆 {g.mention} ganó **${premio}**! Depositados automáticamente. 💜🤣")

# --- 6. COMANDOS DE ECONOMÍA ---

@bot.tree.command(name="banco", description="Mira tu saldo")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    saldo = banco_datos.get(str(t.id), 0)
    emb = discord.Embed(title=f"🏦 Banco de {t.name}", description=f"Saldo: **${saldo}**", color=0x010101)
    emb.set_thumbnail(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="transferir", description="Envía dinero a otro usuario")
async def transferir(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    aid = str(interaction.user.id)
    if cantidad <= 0 or banco_datos.get(aid, 0) < cantidad:
        return await interaction.response.send_message("No tienes dinero suficiente, ija. 🤣", ephemeral=True)
    banco_datos[aid] -= cantidad; banco_datos[str(miembro.id)] = banco_datos.get(str(miembro.id), 0) + cantidad
    await interaction.response.send_message(f"✅ Has enviado **${cantidad}** a {miembro.mention}.")

@bot.tree.command(name="regalar", description="Dar dinero (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    banco_datos[str(miembro.id)] = banco_datos.get(str(miembro.id), 0) + cantidad
    await interaction.response.send_message(f"🎁 Generaste **${cantidad}** para {miembro.mention}. 💜")

# --- 7. COMANDOS SOCIALES Y ÚTILES ---

@bot.tree.command(name="roblox", description="Perfil de Roblox con Avatar")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        uid = r['data'][0]['id']
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png").json()
        avatar_url = thumb['data'][0]['imageUrl']
        emb = discord.Embed(title=f"Perfil de {usuario}", url=f"https://www.roblox.com/users/{uid}/profile", color=0x010101)
        emb.set_image(url=avatar_url)
        await interaction.followup.send(embed=emb)
    except: await interaction.followup.send("No encontré al usuario. 🤣")

@bot.tree.command(name="ship", description="Amor entre dos")
async def ship(interaction: discord.Interaction, m1: discord.Member, m2: discord.Member):
    await interaction.response.defer(); p = random.randint(1, 100)
    av1 = io.BytesIO(await m1.display_avatar.read()); av2 = io.BytesIO(await m2.display_avatar.read())
    i1 = Image.open(av1).convert("RGBA").resize((200, 200)); i2 = Image.open(av2).convert("RGBA").resize((200, 200))
    l = Image.new("RGBA", (500, 200), (0, 0, 0, 0)); l.paste(i1, (0, 0)); l.paste(i2, (300, 0))
    o = io.BytesIO(); l.save(o, format='PNG'); o.seek(0)
    await interaction.followup.send(file=discord.File(o, filename="s.png"), embed=discord.Embed(title=f"💘 {p}%", color=0x010101).set_image(url="attachment://s.png"))

@bot.tree.command(name="avatar", description="Ver avatar de alguien")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    await interaction.response.send_message(embed=discord.Embed(title=f"Avatar de {t.name}", color=0x010101).set_image(url=t.display_avatar.url))

@bot.tree.command(name="embed", description="Crea un mensaje embed")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str):
    await interaction.channel.send(embed=discord.Embed(title=titulo, description=descripcion, color=0x010101))
    await interaction.response.send_message("Ok mañana! 💜", ephemeral=True)

@bot.tree.command(name="delete", description="Limpiar mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Borrados {cantidad}. 💜", ephemeral=True)

# --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive(); bot.run(os.getenv('TOKEN'))
