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
def home(): return "Darky Bot Mega System Online 💜"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. BASES DE DATOS ---
banco_datos = {}
tienda_roles = {} 

# --- 3. VISTAS ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Selecciona un rol...", options=options, custom_id="select_tienda")

    async def callback(self, interaction: discord.Interaction):
        role_id = self.values[0]
        if role_id == "none": return
        data = tienda_roles.get(int(role_id))
        user_id = str(interaction.user.id)
        user_money = banco_datos.get(user_id, 0)
        
        if user_money < data['precio']:
            return await interaction.response.send_message(f"Estás pobre, ija. 🤣", ephemeral=True)
        
        role = interaction.guild.get_role(int(role_id))
        banco_datos[user_id] -= data['precio']
        tienda_roles[int(role_id)]['stock'] -= 1
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ ¡Compraste **{data['nombre']}**! 💜", ephemeral=True)

class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        options = []
        for rid, data in tienda_roles.items():
            if data['stock'] > 0:
                options.append(discord.SelectMenuOption(label=data['nombre'], value=str(rid), description=f"${data['precio']}"))
        if not options: options.append(discord.SelectMenuOption(label="Sin stock", value="none"))
        self.add_item(TiendaSelect(options))

# --- 4. BOT SETUP ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True; intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Sincronizado! 💜🤣")

bot = MyBot()

# --- 5. COMANDOS ---

@bot.tree.command(name="tienda_config", description="Configura un rol (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    # CORRECCIÓN: El bot ahora responde de inmediato para evitar el error de "no responde"
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message(f"✅ Configurado: **{rol.name}** a ${precio} con {stock} unidades. 💜", ephemeral=True)

@bot.tree.command(name="banco", description="Mira tu dinero")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    saldo = banco_datos.get(str(target.id), 0)
    # DETALLE: Avatar de Discord a la par (Thumbnail)
    emb = discord.Embed(title=f"🏦 Banco de {target.name}", description=f"Saldo: **${saldo}**", color=0x010101)
    emb.set_thumbnail(url=target.display_avatar.url) 
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="roblox", description="Perfil Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        # Buscamos el ID por el nombre
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        user_id = r['data'][0]['id']
        # DETALLE: Obtenemos el Avatar (Headshot) del jugador
        thumb_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png"
        
        emb = discord.Embed(title=f"Perfil de {usuario}", url=f"https://www.roblox.com/users/{user_id}/profile", color=0x010101)
        emb.set_image(url=thumb_url) # Aquí ponemos el avatar grande
        await interaction.followup.send(embed=emb)
    except:
        await interaction.followup.send("No encontré ese usuario de Roblox, ija. 🤣")

# (Aquí puedes pegar el resto de comandos: ship, giveaway, delete...)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
