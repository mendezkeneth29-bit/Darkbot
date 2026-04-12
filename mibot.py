import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import time

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
COLOR = 0x000000

# --- BASE DE DATOS (simple) ---
data = {}
tienda_roles = {}
prestamos = []

# --- BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

# --- INIT USER ---
def init_user(uid: str):
    if uid not in data:
        data[uid] = {
            "credito": 0,
            "dinero_transferido": 0,
            "ha_transferido": 0,
            "debe": 0,
            "prestado": 0
        }

# --- SISTEMA DE MENSAJES ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    init_user(uid)

    data[uid]["credito"] += 5

    await bot.process_commands(message)

# --- COMANDO CARTERA ---
@bot.tree.command(name="cartera", description="Ver cartera de un usuario")
async def cartera(i: discord.Interaction, usuario: discord.Member = None):

    usuario = usuario or i.user
    uid = str(usuario.id)
    init_user(uid)

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

# --- TIENDA SET ---
@bot.tree.command(name="tienda-set")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_set(i: discord.Interaction, rol: discord.Role, precio: int, stock: int):

    tienda_roles[rol.id] = {
        "precio": precio,
        "stock": stock
    }

    embed = discord.Embed(title="ITEM AGREGADO A TIENDA", color=COLOR)
    embed.description = (
        f"Rol: {rol.mention}\n"
        f"Precio: ${precio}\n"
        f"Stock: {stock}"
    )

    await i.response.send_message(embed=embed)

# --- TIENDA RESET ---
@bot.tree.command(name="tienda-reset")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_reset(i: discord.Interaction):

    tienda_roles.clear()

    embed = discord.Embed(title="TIENDA RESETEADA", color=COLOR)
    embed.description = "Todos los roles fueron eliminados de la tienda"

    await i.response.send_message(embed=embed)

# --- SELECT ---
class TiendaSelect(discord.ui.Select):
    def __init__(self):

        opciones = []

        for rid, data_rol in tienda_roles.items():
            opciones.append(
                discord.SelectOption(
                    label=f"ID {rid}",
                    description=f"${data_rol['precio']}",
                    value=str(rid)
                )
            )

        # FIX: evitar crash si está vacío
        if not opciones:
            opciones = [discord.SelectOption(label="Sin items", value="0")]

        super().__init__(placeholder="Selecciona un rol", options=opciones)

    async def callback(self, interaction: discord.Interaction):

        rid = int(self.values[0])

        if rid not in tienda_roles:
            return await interaction.response.send_message("No tienes datos aún", ephemeral=True)

        item = tienda_roles[rid]
        uid = str(interaction.user.id)
        init_user(uid)

        if data[uid]["credito"] < item["precio"]:
            return await interaction.response.send_message("No tienes dinero suficiente", ephemeral=True)

        if item["stock"] <= 0:
            return await interaction.response.send_message("Sin stock", ephemeral=True)

        role = interaction.guild.get_role(rid)
        if not role:
            return await interaction.response.send_message("Rol no encontrado", ephemeral=True)

        data[uid]["credito"] -= item["precio"]
        item["stock"] -= 1

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

# --- TIENDA ---
@bot.tree.command(name="tienda")
async def tienda(i: discord.Interaction):

    if not tienda_roles:
        return await i.response.send_message("La tienda está vacía")

    embed = discord.Embed(title="TIENDA", color=COLOR)

    for idx, (rid, item) in enumerate(tienda_roles.items(), start=1):
        role = i.guild.get_role(rid) if i.guild else None

        embed.add_field(
            name=f"{idx}. {role.name if role else 'Rol eliminado'}",
            value=f"Precio: ${item['precio']}\nStock: {item['stock']}",
            inline=False
        )

    await i.response.send_message(embed=embed, view=TiendaView())

# --- PRESTAMOS ---
class PrestamoView(discord.ui.View):
    def __init__(self, prestador, receptor, cantidad, dias):
        super().__init__(timeout=60)
        self.prestador = prestador
        self.receptor = receptor
        self.cantidad = cantidad
        self.dias = dias

    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.green)
    async def aceptar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.receptor:
            return await interaction.response.send_message("No es tu préstamo", ephemeral=True)

        uid_p = str(self.prestador.id)
        uid_r = str(self.receptor.id)

        init_user(uid_p)
        init_user(uid_r)

        if data[uid_p]["credito"] < self.cantidad:
            return await interaction.response.send_message("El prestador no tiene dinero", ephemeral=True)

        data[uid_p]["credito"] -= self.cantidad
        data[uid_r]["credito"] += self.cantidad

        prestamos.append({
            "prestador": uid_p,
            "receptor": uid_r,
            "cantidad": self.cantidad,
            "tiempo": time.time() + (self.dias * 86400)
        })

        data[uid_r]["debe"] += self.cantidad
        data[uid_p]["prestado"] += self.cantidad

        await interaction.response.send_message(
            embed=discord.Embed(
                title="PRÉSTAMO ACEPTADO",
                description=f"{self.receptor.mention} recibió ${self.cantidad}",
                color=COLOR
            )
        )

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.red)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.receptor:
            return await interaction.response.send_message("No es tu préstamo", ephemeral=True)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="PRÉSTAMO RECHAZADO",
                description="El préstamo fue rechazado",
                color=COLOR
            )
        )

# --- COMANDO PRESTAR ---
@bot.tree.command(name="prestar")
async def prestar(i: discord.Interaction, cantidad: int, usuario: discord.Member, dias: int):

    prestador = i.user
    receptor = usuario

    embed = discord.Embed(color=COLOR)

    embed.title = f"{prestador.name} quiere prestar dinero a {receptor.name}"
    embed.description = (
        "-------------------------------------------------------\n"
        f"> - el dinero se debera pagar en {dias} dias\n"
        f"> - la cantidad de dinero prestado sera de ${cantidad}\n"
        "> - si este dinero no es entregado la fecha planeada se le quitara el dinero pendiente al que debe\n"
        "-------------------------------------------------------\n"
        f"{receptor.mention} aceptas o rechazas el prestamo?"
    )

    embed.set_thumbnail(url=receptor.display_avatar.url)

    await i.response.send_message(
        embed=embed,
        view=PrestamoView(prestador, receptor, cantidad, dias)
    )

# --- LOOP PRESTAMOS ---
async def revisar_prestamos():
    while True:
        ahora = time.time()

        for deuda in prestamos[:]:
            if ahora >= deuda["tiempo"]:
                uid_r = deuda["receptor"]
                uid_p = deuda["prestador"]
                cantidad = deuda["cantidad"]

                if data.get(uid_r, {}).get("credito", 0) >= cantidad:
                    data[uid_r]["credito"] -= cantidad
                    data[uid_p]["credito"] += cantidad

                prestamos.remove(deuda)

        await asyncio.sleep(60)

# --- READY ---
@bot.event
async def on_ready():
    print("Bot listo")
    bot.loop.create_task(revisar_prestamos())

# --- RUN ---
bot.run(TOKEN)
