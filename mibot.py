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

# --- TIENDA DATA ---
tienda = {}

# --- SELECTOR ---
class TiendaSelect(discord.ui.Select):
    def __init__(self, opciones):
        super().__init__(placeholder="Selecciona un producto...", options=opciones)

    async def callback(self, interaction: discord.Interaction):
        item_id = int(self.values[0])
        item = tienda[item_id]

        uid = str(interaction.user.id)

        if data[uid]["credito"] < item["precio"]:
            return await interaction.response.send_message("No tienes dinero suficiente", ephemeral=True)

        if item["stock"] <= 0:
            return await interaction.response.send_message("Sin stock", ephemeral=True)

        # COBRAR
        data[uid]["credito"] -= item["precio"]
        item["stock"] -= 1

        # DAR ROL SI EXISTE
        if item["rol"]:
            role = interaction.guild.get_role(item["rol"])
            if role:
                await interaction.user.add_roles(role)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="COMPRA EXITOSA",
                description=f"Compraste: {item['nombre']}",
                color=COLOR
            ),
            ephemeral=True
        )

# --- VIEW ---
class TiendaView(discord.ui.View):
    def __init__(self, opciones):
        super().__init__(timeout=None)
        self.add_item(TiendaSelect(opciones))

# --- COMANDO TIENDA ---
@bot.tree.command(name="tienda")
async def tienda_cmd(i: discord.Interaction, productos: str):

    tienda.clear()
    lista = productos.split(",")

    embed = discord.Embed(
        title="TIENDA",
        color=COLOR
    )

    opciones = []

    for idx, prod in enumerate(lista, start=1):
        try:
            nombre, precio, stock = prod.split("|")

            tienda[idx] = {
                "nombre": nombre.strip(),
                "precio": int(precio),
                "stock": int(stock),
                "rol": None  # opcional luego
            }

            embed.add_field(
                name=f"{idx}. {nombre}",
                value=f"Precio: ${precio}\nStock: {stock}",
                inline=False
            )

            opciones.append(
                discord.SelectOption(
                    label=nombre,
                    description=f"${precio}",
                    value=str(idx)
                )
            )

        except:
            continue

    await i.response.send_message(embed=embed, view=TiendaView(opciones))

# --- START ---
bot.run(TOKEN)
