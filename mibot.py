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
def home(): return "Darky Bot Mega Store Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- 2. BASES DE DATOS TEMPORALES ---
banco_datos = {}
tienda_roles = {} # Estructura: {rol_id: {"precio": int, "stock": int, "nombre": str}}

# --- 3. VISTAS (TIENDA Y SORTEOS) ---

class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        options = []
        for rid, data in tienda_roles.items():
            if data['stock'] > 0:
                options.append(discord.SelectMenuOption(
                    label=data['nombre'], 
                    value=str(rid), 
                    description=f"Precio: ${data['precio']} | Stock: {data['stock']}"
                ))
        
        if not options:
            options.append(discord.SelectMenuOption(label="Sin stock", value="none"))

        self.add_item(TiendaSelect(options))

class TiendaSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Selecciona un rol para comprar...", options=options, custom_id="select_tienda")

    async def callback(self, interaction: discord.Interaction):
        role_id = self.values[0]
        if role_id == "none": return await interaction.response.send_message("No hay nada que comprar, ija. 🤣", ephemeral=True)
        
        data = tienda_roles.get(int(role_id))
        user_id = str(interaction.user.id)
        user_money = banco_datos.get(user_id, 0)

        if user_money < data['precio']:
            return await interaction.response.send_message(f"Estás pobre, te faltan ${data['precio'] - user_money}. 💜🤣", ephemeral=True)
        
        if data['stock'] <= 0:
            return await interaction.response.send_message("¡Se agotó! Ok mañana. 💔", ephemeral=True)

        # Proceso de compra
        role = interaction.guild.get_role(int(role_id))
        if role in interaction.user.roles:
            return await interaction.response.send_message("¡Ya tienes este rol! No gastes por gastar. 🤣", ephemeral=True)

        banco_datos[user_id] -= data['precio']
        tienda_roles[int(role_id)]['stock'] -= 1
        await interaction.user.add_roles(role)
        
        await interaction.response.send_message(f"✅ ¡Compraste **{data['nombre']}**! Se te descontaron ${data['precio']}. ¡YIPIEEE! 💜", ephemeral=True)

class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.participantes = []
    @discord.ui.button(label="Participar 🎉", style=discord.ButtonStyle.green, custom_id="giveaway_btn")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes: return await interaction.response.send_message("Ya estás dentro, ija. 🤣", ephemeral=True)
        self.participantes.append(interaction.user)
        await interaction.response.send_message("¡Ok mañana! Anotado. 💜", ephemeral=True)

# --- 4. BOT CORE ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True; intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Sincronización Total! Banco, Tienda y Sorteos listos. 💜🤣")

    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        banco_datos[uid] = banco_datos.get(uid, 0) + 5
        await self.process_commands(message)

bot = MyBot()

# --- 5. COMANDOS DE TIENDA (ADMIN) ---

@bot.tree.command(name="tienda_config", description="Agrega o actualiza un rol en la tienda")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_config(interaction: discord.Interaction, rol: discord.Role, precio: int, stock: int):
    tienda_roles[rol.id] = {"precio": precio, "stock": stock, "nombre": rol.name}
    await interaction.response.send_message(f"✅ Rol **{rol.name}** configurado a ${precio} con {stock} unidades. ¡Ok mañana! 💜", ephemeral=True)

@bot.tree.command(name="tienda", description="Abre la tienda de roles")
async def tienda(interaction: discord.Interaction):
    if not tienda_roles:
        return await interaction.response.send_message("La tienda está vacía, ija ke dice. 🤣", ephemeral=True)
    
    emb = discord.Embed(title="🏪 DARKY STORE - ROLES EXCLUSIVOS", description="Usa tus dólares ganados por chatear para comprar rangos.", color=0x010101)
    for rid, data in tienda_roles.items():
        emb.add_field(name=data['nombre'], value=f"💰 Precio: `${data['precio']}`\n📦 Stock: `{data['stock']}`", inline=True)
    
    await interaction.response.send_message(embed=emb, view=TiendaView())

# --- 6. COMANDO GIVEAWAY ELITE ---

@bot.tree.command(name="giveaway", description="Sorteo con depósito automático")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(unidad=[app_commands.Choice(name="Minutos", value="m"), app_commands.Choice(name="Horas", value="h")])
async def giveaway(interaction: discord.Interaction, tiempo: int, unidad: str, premio: int, canal_ganador: discord.TextChannel):
    seg = tiempo * 60 if unidad == "m" else tiempo * 3600
    finaliza = int(time.time() + seg)
    view = GiveawayView(timeout=seg)
    emb = discord.Embed(title="🎊 SORTEO ACTIVO 🎊", description=f"💰 **Premio:** `${premio}`\n⏰ **Termina:** <t:{finaliza}:R>", color=0x010101)
    await interaction.response.send_message("Sorteo lanzado. 🚀", ephemeral=True)
    msg = await interaction.channel.send(embed=emb, view=view)
    await asyncio.sleep(seg)
    if not view.participantes: return await canal_ganador.send("Nadie participó. 🤣")
    ganador = random.choice(view.participantes)
    banco_datos[str(ganador.id)] = banco_datos.get(str(ganador.id), 0) + premio
    await canal_ganador.send(f"🏆 ¡{ganador.mention} ganó **${premio}**! Depositados. 💜🤣")

# --- 7. COMANDOS BÁSICOS (BANCO, SHIP, ROBLOX, DELETE) ---

@bot.tree.command(name="banco", description="Mira tu dinero")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    await interaction.response.send_message(embed=discord.Embed(title=f"🏦 Banco de {target.name}", description=f"Saldo: **${banco_datos.get(str(target.id), 0)}**", color=0x010101))

@bot.tree.command(name="ship", description="Amor")
async def ship(interaction: discord.Interaction, m1: discord.Member, m2: discord.Member):
    await interaction.response.defer()
    p = random.randint(1, 100)
    av1 = io.BytesIO(await m1.display_avatar.read()); av2 = io.BytesIO(await m2.display_avatar.read())
    i1 = Image.open(av1).convert("RGBA").resize((200, 200)); i2 = Image.open(av2).convert("RGBA").resize((200, 200))
    l = Image.new("RGBA", (500, 200), (0, 0, 0, 0)); l.paste(i1, (0, 0)); l.paste(i2, (300, 0))
    o = io.BytesIO(); l.save(o, format='PNG'); o.seek(0)
    await interaction.followup.send(file=discord.File(o, filename="s.png"), embed=discord.Embed(title=f"💘 {p}%", color=0x010101).set_image(url="attachment://s.png"))

@bot.tree.command(name="delete", description="Borrar mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Borrados {cantidad}. 💜", ephemeral=True)

# --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
