import discord
from discord import app_commands
from discord.ext import commands
import os, random, requests, time, io
from flask import Flask
from threading import Thread
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

# --- KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home():
    return "DarkyBot Online"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# --- DATOS ---
cartera = {}
cooldowns = {}
COLOR = 0x000000
SEP = "━━━━━━━━━━━━━━━━━━━━━━"

# --- BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

# --- DINERO POR MENSAJE ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    if time.time() - cooldowns.get(uid, 0) > 10:
        cartera[uid] = cartera.get(uid, 0) + 5
        cooldowns[uid] = time.time()

    await bot.process_commands(message)

# --- CARTERA ---
@bot.tree.command(name="cartera")
async def cartera_cmd(interaction: discord.Interaction):
    money = cartera.get(str(interaction.user.id), 0)

    embed = discord.Embed(title="SISTEMA FINANCIERO GLOBAL", color=COLOR)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    embed.description = (
        f"Usuario: {interaction.user.mention}\n"
        f"Saldo actual: ${money:,}\n\n"
        f"{SEP}\n"
        f"Ingreso automático:\n"
        f"+5 cada 10 segundos por actividad\n\n"
        f"Estado: ACTIVO"
    )

    await interaction.response.send_message(embed=embed)

# --- SHIP ---
@bot.tree.command(name="ship")
async def ship(interaction: discord.Interaction, u1: discord.Member, u2: discord.Member):
    p = random.randint(0, 100)

    img1 = Image.open(io.BytesIO(requests.get(u1.display_avatar.url).content)).resize((256,256))
    img2 = Image.open(io.BytesIO(requests.get(u2.display_avatar.url).content)).resize((256,256))

    final = Image.new("RGBA",(800,256),(0,0,0,0))
    final.paste(img1,(0,0))
    final.paste(img2,(544,0))

    draw = ImageDraw.Draw(final)

    try:
        font = ImageFont.truetype("arial.ttf", 150)
    except:
        font = ImageFont.load_default()

    text = f"{p}%"
    bbox = draw.textbbox((0,0),text,font=font)
    x = 400 - (bbox[2]//2)

    draw.text((x+6,90+6),text,fill=(0,0,0),font=font)
    draw.text((x,90),text,fill=(255,255,255),font=font)

    buf = io.BytesIO()
    final.save(buf,"PNG")
    buf.seek(0)

    file = discord.File(buf,"ship.png")

    embed = discord.Embed(title="ANÁLISIS DE COMPATIBILIDAD", color=COLOR)
    embed.description = (
        f"Usuarios analizados:\n"
        f"{u1.mention} + {u2.mention}\n\n"
        f"Resultado final: {p}%\n\n"
        f"{SEP}\n"
        f"Este cálculo es generado por algoritmo aleatorio."
    )
    embed.set_image(url="attachment://ship.png")

    await interaction.response.send_message(embed=embed,file=file)

# --- REGALAR ---
@bot.tree.command(name="regalar")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction, user:discord.Member, cantidad:int):
    uid=str(user.id)
    cartera[uid]=cartera.get(uid,0)+cantidad

    embed=discord.Embed(title="TRANSFERENCIA AUTORIZADA",color=COLOR)
    embed.set_thumbnail(url=user.display_avatar.url)

    embed.description=(
        f"Usuario beneficiado: {user.mention}\n"
        f"Monto entregado: ${cantidad:,}\n"
        f"Autorizado por: {interaction.user.mention}\n"
        f"Saldo actualizado: ${cartera[uid]:,}\n\n"
        f"{SEP}"
    )

    await interaction.response.send_message(embed=embed)

# --- GESTOS CON GIFS ---
@bot.tree.command(name="beso")
async def beso(i,u:discord.Member):
    gifs=["https://media.tenor.com/images/8c4e0.gif"]
    e=discord.Embed(title="INTERACCIÓN: BESO",color=COLOR)
    e.description=f"{i.user.mention} besa a {u.mention}"
    e.set_image(url=random.choice(gifs))
    await i.response.send_message(embed=e)

@bot.tree.command(name="abrazo")
async def abrazo(i,u:discord.Member):
    gifs=["https://media.tenor.com/images/3c1a7.gif"]
    e=discord.Embed(title="INTERACCIÓN: ABRAZO",color=COLOR)
    e.description=f"{i.user.mention} abraza a {u.mention}"
    e.set_image(url=random.choice(gifs))
    await i.response.send_message(embed=e)

# --- MÁS COMANDOS DETALLADOS ---
@bot.tree.command(name="iq")
async def iq(i,u:Optional[discord.Member]=None):
    u=u or i.user
    iq_val=random.randint(50,200)

    e=discord.Embed(title="ANÁLISIS INTELECTUAL AVANZADO",color=COLOR)
    e.description=f"Usuario: {u.mention}\nResultado IQ: {iq_val}\n\n{SEP}\nEvaluación generada automáticamente."
    await i.response.send_message(embed=e)

# --- START ---
keep_alive()
bot.run(os.getenv("TOKEN"))
