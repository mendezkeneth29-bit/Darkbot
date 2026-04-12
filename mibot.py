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

# --- AGREGAR A TIENDA ---
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

# --- RESET TIENDA ---
@bot.tree.command(name="tienda-reset")
@app_commands.checks.has_permissions(administrator=True)
async def tienda_reset(i: discord.Interaction):

    tienda_roles.clear()

    embed = discord.Embed(title="TIENDA RESETEADA", color=COLOR)
    embed.description = "Todos los roles fueron eliminados de la tienda"

    await i.response.send_message(embed=embed)

# --- SELECTOR ---
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

# --- VER TIENDA ---
@bot.tree.command(name="tienda")
async def tienda(i: discord.Interaction):

    if not tienda_roles:
        return await i.response.send_message("La tienda está vacía")

    embed = discord.Embed(title="TIENDA", color=COLOR)

    for idx, (rid, item) in enumerate(tienda_roles.items(), start=1):
        role = i.guild.get_role(rid)

        embed.add_field(
            name=f"{idx}. {role.name if role else 'Rol eliminado'}",
            value=f"Precio: ${item['precio']}\nStock: {item['stock']}",
            inline=False
        )

    await i.response.send_message(embed=embed, view=TiendaView())

import asyncio
import time

prestamos = []

# --- VIEW BOTONES ---
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

        if data[uid_p]["credito"] < self.cantidad:
            return await interaction.response.send_message("El prestador no tiene dinero", ephemeral=True)

        # transferir dinero
        data[uid_p]["credito"] -= self.cantidad
        data[uid_r]["credito"] += self.cantidad

        # registrar deuda
        deuda = {
            "prestador": uid_p,
            "receptor": uid_r,
            "cantidad": self.cantidad,
            "tiempo": time.time() + (self.dias * 86400)
        }

        prestamos.append(deuda)

        # actualizar datos
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

# --- SISTEMA AUTOMÁTICO DE COBRO ---
async def revisar_prestamos():
    while True:
        ahora = time.time()

        for deuda in prestamos[:]:
            if ahora >= deuda["tiempo"]:
                uid_r = deuda["receptor"]
                uid_p = deuda["prestador"]
                cantidad = deuda["cantidad"]

                if data[uid_r]["credito"] >= cantidad:
                    data[uid_r]["credito"] -= cantidad
                    data[uid_p]["credito"] += cantidad

                prestamos.remove(deuda)

        await asyncio.sleep(60)

# --- INICIAR LOOP ---
@bot.event
async def on_ready():
    bot.loop.create_task(revisar_prestamos())

# --- START ---
bot.run(TOKEN)
