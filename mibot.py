import discord
from discord import app_commands
from discord.ext import commands
import os

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
COLOR = 0x000000

# --- BASE DE DATOS (simple) ---
data = {}

# --- BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

# --- SISTEMA DE MENSAJES ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)

    if uid not in data:
        data[uid] = {
            "credito": 0,
            "dinero_transferido": 0,
            "ha_transferido": 0,
            "debe": 0,
            "prestado": 0
        }

    data[uid]["credito"] += 5

    await bot.process_commands(message)

# --- COMANDO CARTERA ---
@bot.tree.command(name="cartera", description="Ver cartera de un usuario")
async def cartera(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)

    if uid not in data:
        data[uid] = {
            "credito": 0,
            "dinero_transferido": 0,
            "ha_transferido": 0,
            "debe": 0,
            "prestado": 0
        }

    user_data = data[uid]

    embed = discord.Embed(
        title=f"Cartera de {usuario.name}",
        color=COLOR
    )

    embed.description = (
        f"credito: {user_data['credito']}$\n"
        f"dinero transferido: {user_data['dinero_transferido']}$\n"
        f"-----------------------\n"
        f"ha transferido: {user_data['ha_transferido']}$\n"
        f"debe: {user_data['debe']}$\n"
        f"prestado: {user_data['prestado']}$"
    )

    embed.set_thumbnail(url=usuario.display_avatar.url)

    await i.response.send_message(embed=embed)

# --- BASE TIENDA ---
tienda_roles = {}

# --- COMANDO PARA AGREGAR ROLES ---
@bot.tree.command(name="tienda-set")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_set(i: discord.Interaction, rol: discord.Role, precio: int, stock: int):

    tienda_roles[rol.id] = {
        "precio": precio,
        "stock": stock
    }

    embed = discord.Embed(title="ROL AGREGADO A TIENDA", color=COLOR)
    embed.description = (
        f"Rol: {rol.mention}\n"
        f"Precio: ${precio}\n"
        f"Stock: {stock}"
    )

    await i.response.send_message(embed=embed)

# --- SELECTOR ---
class TiendaSelect(discord.ui.Select):
    def __init__(self):
        opciones = []

        for rid, data_rol in tienda_roles.items():
            opciones.append(
                discord.SelectOption(
                    label=f"Rol {rid}",
                    description=f"${data_rol['precio']}",
                    value=str(rid)
                )
            )

        super().__init__(placeholder="Selecciona un rol", options=opciones)

    async def callback(self, interaction: discord.Interaction):
        rid = int(self.values[0])
        item = tienda_roles[rid]
        uid = str(interaction.user.id)

        if uid not in data:
            return await interaction.response.send_message("No tienes datos aún", ephemeral=True)

        if data[uid]["credito"] < item["precio"]:
            return await interaction.response.send_message("No tienes dinero suficiente", ephemeral=True)

        if item["stock"] <= 0:
            return await interaction.response.send_message("Sin stock", ephemeral=True)

        role = interaction.guild.get_role(rid)
        if not role:
            return await interaction.response.send_message("Rol no encontrado", ephemeral=True)

        # COBRAR
        data[uid]["credito"] -= item["precio"]
        item["stock"] -= 1

        # DAR ROL
        await interaction.user.add_roles(role)

        embed = discord.Embed(title="COMPRA EXITOSA", color=COLOR)
        embed.description = (
            f"Rol: {role.mention}\n"
            f"Precio: ${item['precio']}\n"
            f"Stock restante: {item['stock']}"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- VIEW ---
class TiendaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect())

# --- COMANDO PARA VER TIENDA ---
@bot.tree.command(name="tienda")
async def tienda(i: discord.Interaction):

    if not tienda_roles:
        return await i.response.send_message("No hay roles en la tienda")

    embed = discord.Embed(title="TIENDA DE ROLES", color=COLOR)

    for idx, (rid, item) in enumerate(tienda_roles.items(), start=1):
        role = i.guild.get_role(rid)

        embed.add_field(
            name=f"{idx}. {role.name if role else 'Rol eliminado'}",
            value=f"Precio: ${item['precio']}\nStock: {item['stock']}",
            inline=False
        )

    await i.response.send_message(embed=embed, view=TiendaView())

# --- START ---
bot.run(TOKEN)
