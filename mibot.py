import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
import random
import io
import asyncio
import time
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot Giveaway Elite Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BASE DE DATOS DEL BANCO ---
banco_datos = {}

# --- 3. VISTA DEL BOTÓN DE PARTICIPAR ---
class GiveawayView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.participantes = []

    @discord.ui.button(label="Participar 🎉", style=discord.ButtonStyle.green, custom_id="participar_btn")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participantes:
            return await interaction.response.send_message("¡Ija ke dice! Ya estás participando, no te desesperes. 🤣", ephemeral=True)
        
        self.participantes.append(interaction.user)
        await interaction.response.send_message("¡Ok mañana! Te has anotado correctamente. 💜", ephemeral=True)

# --- 4. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Sistema de Sorteos Elite Sincronizado! 💜🤣")

    async def on_message(self, message):
        if message.author.bot: return
        uid = str(message.author.id)
        if uid not in banco_datos: banco_datos[uid] = 0
        banco_datos[uid] += 5
        await self.process_commands(message)

bot = MyBot()

# --- 5. COMANDO GIVEAWAY ELITE ---

@bot.tree.command(name="giveaway", description="Crea un sorteo de dinero con depósito automático")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(unidad=[
    app_commands.Choice(name="Minutos", value="m"),
    app_commands.Choice(name="Horas", value="h"),
    app_commands.Choice(name="Días", value="d")
])
@app_commands.describe(
    tiempo="Número de minutos/horas/días", 
    unidad="Elige la unidad de tiempo", 
    premio="Cantidad de dólares a regalar", 
    canal_ganador="Canal donde se anunciará al ganador"
)
async def giveaway(
    interaction: discord.Interaction, 
    tiempo: int, 
    unidad: str, 
    premio: int, 
    canal_ganador: discord.TextChannel
):
    # Calcular segundos totales
    segundos = tiempo * 60 if unidad == "m" else tiempo * 3600 if unidad == "h" else tiempo * 86400
    
    if premio <= 0:
        return await interaction.response.send_message("¡Ija! No puedes sortear deudas. Pon un premio real. 🤣", ephemeral=True)

    finaliza_en = int(time.time() + segundos)
    view = GiveawayView(timeout=segundos)
    
    # Embed del sorteo (El que todos ven)
    emb = discord.Embed(
        title="🎊 ¡GRAN SORTEO DE DÓLARES! 🎊",
        description=f"Participa para ganar una fortuna del DarkyBot.\n\n"
                    f"💰 **Premio:** `${premio}` dólares\n"
                    f"📢 **Se anuncia en:** {canal_ganador.mention}\n"
                    f"⏰ **Finaliza:** <t:{finaliza_en}:R>",
        color=0x010101
    )
    emb.set_footer(text="Haz clic en el botón de abajo para entrar. 💜")

    await interaction.response.send_message(f"Sorteo iniciado con éxito. Suerte a todos. 🚀", ephemeral=True)
    mensaje_sorteo = await interaction.channel.send(embed=emb, view=view)

    # Esperar el tiempo configurado
    await asyncio.sleep(segundos)

    # Desactivar el botón al terminar
    view.children[0].disabled = True
    await mensaje_sorteo.edit(view=view)

    # Lógica del ganador al azar
    if not view.participantes:
        return await canal_ganador.send(f"❌ El sorteo de **${premio}** terminó, pero nadie se anotó. Ija ke dice... 💔🤣")

    ganador = random.choice(view.participantes)
    uid_ganador = str(ganador.id)

    # DEPÓSITO AUTOMÁTICO AL BANCO
    banco_datos[uid_ganador] = banco_datos.get(uid_ganador, 0) + premio

    # Embed del Ganador
    emb_win = discord.Embed(
        title="🏆 ¡TENEMOS UN GANADOR! 🏆",
        description=f"¡Felicidades {ganador.mention}!\n\n"
                    f"Has ganado el premio de **${premio}** dólares.\n"
                    f"💸 **Estado:** Dinero depositado automáticamente en tu `/banco`.\n\n"
                    f"🔗 [Ver sorteo original]({mensaje_sorteo.jump_url})",
        color=0x010101
    )
    emb_win.set_thumbnail(url=ganador.display_avatar.url)
    emb_win.set_footer(text="¡Gracias por participar! Ok mañana. 💜🤣")
    
    await canal_ganador.send(content=f"¡Felicidades {ganador.mention}! 🎉", embed=emb_win)

# --- 6. COMANDOS DE BANCO & GESTIÓN ---

@bot.tree.command(name="banco", description="Mira tu saldo")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    saldo = banco_datos.get(str(target.id), 0)
    emb = discord.Embed(title=f"🏦 Banco de {target.display_name}", description=f"Saldo: **${saldo}**", color=0x010101)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="transferir", description="Envía dinero a alguien")
async def transferir(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    aid = str(interaction.user.id)
    if cantidad <= 0 or banco_datos.get(aid, 0) < cantidad:
        return await interaction.response.send_message("No tienes fondos o cantidad inválida, ija. 🤣", ephemeral=True)
    banco_datos[aid] -= cantidad
    banco_datos[str(miembro.id)] = banco_datos.get(str(miembro.id), 0) + cantidad
    await interaction.response.send_message(f"✅ Has enviado **${cantidad}** a {miembro.mention}.")

# --- 7. OTROS COMANDOS (SHIP, ROBLOX) ---

@bot.tree.command(name="ship", description="Nivel de amor")
async def ship(interaction: discord.Interaction, miembro1: discord.Member, miembro2: discord.Member):
    await interaction.response.defer()
    p = random.randint(1, 100)
    av1 = io.BytesIO(await miembro1.display_avatar.read()); av2 = io.BytesIO(await miembro2.display_avatar.read())
    i1 = Image.open(av1).convert("RGBA").resize((200, 200)); i2 = Image.open(av2).convert("RGBA").resize((200, 200))
    l = Image.new("RGBA", (500, 200), (0, 0, 0, 0)); l.paste(i1, (0, 0)); l.paste(i2, (300, 0))
    o = io.BytesIO(); l.save(o, format='PNG'); o.seek(0)
    await interaction.followup.send(file=discord.File(o, filename="s.png"), embed=discord.Embed(title=f"💘 Ship: {p}%", color=0x010101).set_image(url="attachment://s.png"))

@bot.tree.command(name="roblox", description="Perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario], "excludeBannedUsers": False}, headers=headers).json()
        if 'data' in r and r['data']:
            u = r['data'][0]; uid = u['id']
            thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png", headers=headers).json()
            foto = thumb['data'][0]['imageUrl'] if 'data' in thumb else ""
            emb = discord.Embed(title=f"Perfil de {u['displayName']}", url=f"https://www.roblox.com/users/{uid}/profile", color=0x010101)
            if foto: emb.set_image(url=foto)
            await interaction.followup.send(embed=emb)
        else: await interaction.followup.send("No lo encontré.")
    except: await interaction.followup.send("Error en Roblox.")

# --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
