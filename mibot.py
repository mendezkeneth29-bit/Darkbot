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

# --- 3. VISTAS ---
class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        options = []
        for rid, data in tienda_roles.items():
            if data['stock'] > 0:
                options.append(discord.SelectMenuOption(label=data['nombre'], value=str(rid), description=f"${data['precio']}"))
        if not options: options.append(discord.SelectMenuOption(label="Sin stock", value="none"))
        self.add_item(TiendaSelect(options))

class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Elige un rol...", options=options, custom_id="sel_t")
    async def callback(self, interaction: discord.Interaction):
        rid = self.values[0]
        if rid == "none": return
        data = tienda_roles.get(int(rid))
        uid = str(interaction.user.id)
        if banco_datos.get(uid, 0) < data['precio']:
            return await interaction.response.send_message("Pobre. 🤣", ephemeral=True)
        role = interaction.guild.get_role(int(rid))
        banco_datos[uid] -= data['precio']
        tienda_roles[int(rid)]['stock'] -= 1
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ ¡Comprado! 💜", ephemeral=True)

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout); self.participantes = []
    @discord.ui.button(label="Participar 🎉", style=discord.ButtonStyle.green)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes: return await interaction.response.send_message("Ya estás dentro. 🤣", ephemeral=True)
        self.participantes.append(interaction.user); await interaction.response.send_message("Anotado. 💜", ephemeral=True)

# --- 4. BOT SETUP ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True; intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        # Sincroniza globalmente
        await self.tree.sync()
        print("¡Sincronización Total! 💜🤣")

bot = MyBot()

# --- 5. COMANDOS ---

@bot.tree.command(name="tienda_config", description="Configura un rol")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message(f"✅ Configurado: {rol.name}. 💜", ephemeral=True)

@bot.tree.command(name="tienda", description="Ver tienda")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles: return await interaction.response.send_message("Vacía. 🤣", ephemeral=True)
    emb = discord.Embed(title="🏪 DARKY STORE", color=0x010101)
    for rid, data in tienda_roles.items():
        emb.add_field(name=data['nombre'], value=f"💰 ${data['precio']} | 📦 {data['stock']}")
    await interaction.response.send_message(embed=emb, view=TiendaView())

@bot.tree.command(name="roblox", description="Perfil Roblox con Avatar")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        # 1. Obtener ID
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        uid = r['data'][0]['id']
        # 2. Obtener Avatar (Thumbnail Oficial)
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png&isCircular=false").json()
        avatar_url = thumb['data'][0]['imageUrl']
        
        emb = discord.Embed(title=f"Perfil de {usuario}", url=f"https://www.roblox.com/users/{uid}/profile", color=0x010101)
        emb.set_image(url=avatar_url) # AVATAR GRANDE
        await interaction.followup.send(embed=emb)
    except: await interaction.followup.send("No lo encontré. 🤣")

@bot.tree.command(name="banco", description="Mira tu saldo")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    saldo = banco_datos.get(str(target.id), 0)
    emb = discord.Embed(title=f"🏦 Banco de {target.name}", description=f"Saldo: **${saldo}**", color=0x010101)
    emb.set_thumbnail(url=target.display_avatar.url) # AVATAR DE DISCORD AL LADO
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="giveaway", description="Sorteo")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, tiempo: int, premio: int, canal: discord.TextChannel):
    seg = tiempo * 60; final = int(time.time() + seg); view = GiveawayView(timeout=seg)
    emb = discord.Embed(title="🎊 SORTEO 🎊", description=f"💰 `${premio}`\n⏰ <t:{final}:R>", color=0x010101)
    await interaction.response.send_message("🚀", ephemeral=True)
    msg = await interaction.channel.send(embed=emb, view=view)
    await asyncio.sleep(seg)
    if not view.participantes: return await canal.send("Nadie entró. 🤣")
    g = random.choice(view.participantes); banco_datos[str(g.id)] = banco_datos.get(str(g.id), 0) + premio
    await canal.send(f"🏆 {g.mention} ganó **${premio}**! 💜🤣")

@bot.tree.command(name="ship", description="Amor")
async def ship(interaction: discord.Interaction, m1: discord.Member, m2: discord.Member):
    await interaction.response.defer(); p = random.randint(1, 100)
    av1 = io.BytesIO(await m1.display_avatar.read()); av2 = io.BytesIO(await m2.display_avatar.read())
    i1 = Image.open(av1).convert("RGBA").resize((200, 200)); i2 = Image.open(av2).convert("RGBA").resize((200, 200))
    l = Image.new("RGBA", (500, 200), (0, 0, 0, 0)); l.paste(i1, (0, 0)); l.paste(i2, (300, 0))
    o = io.BytesIO(); l.save(o, format='PNG'); o.seek(0)
    await interaction.followup.send(file=discord.File(o, filename="s.png"), embed=discord.Embed(title=f"💘 {p}%", color=0x010101).set_image(url="attachment://s.png"))

@bot.tree.command(name="delete", description="Limpiar")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Borrados. 💜", ephemeral=True)

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive(); bot.run(os.getenv('TOKEN'))
