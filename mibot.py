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

# --- TIENDA ROLES ---
tienda_roles = {}

# --- SELECTOR ---
class TiendaRolesSelect(discord.ui.Select):
    def __init__(self, opciones):
        super().__init__(placeholder="Selecciona un rol...", options=opciones)

    async def callback(self, interaction: discord.Interaction):
        rid = int(self.values[0])
        item = tienda_roles[rid]
        uid = str(interaction.user.id)

        # verificar usuario en data
        if uid not in data:
            return await interaction.response.send_message("No tienes datos aún", ephemeral=True)

        # verificar dinero
        if data[uid]["credito"] < item["precio"]:
            return await interaction.response.send_message("No tienes suficiente dinero", ephemeral=True)

        # verificar stock
        if item["stock"] <= 0:
            return await interaction.response.send_message("Este rol ya no tiene stock", ephemeral=True)

        role = interaction.guild.get_role(rid)
        if not role:
            return await interaction.response.send_message("El rol no existe", ephemeral=True)

        # COBRAR
        data[uid]["credito"] -= item["precio"]
        item["stock"] -= 1

        # DAR ROL
        await interaction.user.add_roles(role)

        embed = discord.Embed(title="COMPRA REALIZADA", color=COLOR)
        embed.description = (
            f"Rol: {role.mention}\n"
            f"Precio: ${item['precio']}\n"
            f"Stock restante: {item['stock']}"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- VIEW ---
class TiendaRolesView(discord.ui.View):
    def __init__(self, opciones):
        super().__init__(timeout=None)
        self.add_item(TiendaRolesSelect(opciones))

# --- COMANDO TIENDA ---
@bot.tree.command(name="tienda")
async def tienda(i: discord.Interaction, roles: str):

    tienda_roles.clear()
    lista = roles.split(",")

    embed = discord.Embed(
        title="TIENDA DE ROLES",
        description="Selecciona un rol para comprar",
        color=COLOR
    )

    opciones = []

    for idx, item in enumerate(lista, start=1):
        try:
            rol_txt, precio, stock = item.split("|")

            # obtener ID del rol
            rol_id = int(rol_txt.strip().replace("<@&", "").replace(">", ""))

            role = i.guild.get_role(rol_id)
            if not role:
                continue

            tienda_roles[rol_id] = {
                "precio": int(precio),
                "stock": int(stock)
            }

            embed.add_field(
                name=f"{idx}. {role.name}",
                value=f"Precio: ${precio}\nStock: {stock}",
                inline=False
            )

            opciones.append(
                discord.SelectOption(
                    label=role.name,
                    description=f"${precio}",
                    value=str(rol_id)
                )
            )

        except:
            continue

    await i.response.send_message(embed=embed, view=TiendaRolesView(opciones))

# --- START ---
bot.run(TOKEN)
