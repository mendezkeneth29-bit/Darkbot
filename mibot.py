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

# --- CONFIG ---
TOKEN = os.getenv("TOKEN")
TENOR_KEY = "LIVDSRZULELA"  # clave pública de Tenor

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

# --- FUNCION GIF TENOR ---
def get_gif(query):
    url = f"https://g.tenor.com/v1/search?q={query}&key={TENOR_KEY}&limit=10"
    r = requests.get(url).json()
    return random.choice(r["results"])["media"][0]["gif"]["url"]

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
async def cartera_cmd(i: discord.Interaction):
    money = cartera.get(str(i.user.id), 0)

    e = discord.Embed(title="SISTEMA FINANCIERO CENTRAL", color=COLOR)
    e.set_thumbnail(url=i.user.display_avatar.url)
    e.description = (
        f"Usuario: {i.user.mention}\n"
        f"Saldo disponible: ${money:,}\n\n"
        f"{SEP}\n"
        f"Generación automática:\n"
        f"+5 cada 10 segundos\n"
        f"Estado: ACTIVO"
    )
    await i.response.send_message(embed=e)

# --- SHIP ---
@bot.tree.command(name="ship")
async def ship(i: discord.Interaction, u1: discord.Member, u2: discord.Member):
    p = random.randint(0, 100)

    img1 = Image.open(io.BytesIO(requests.get(u1.display_avatar.url).content)).resize((256,256))
    img2 = Image.open(io.BytesIO(requests.get(u2.display_avatar.url).content)).resize((256,256))

    final = Image.new("RGBA",(820,256),(0,0,0,0))
    final.paste(img1,(0,0))
    final.paste(img2,(564,0))

    draw = ImageDraw.Draw(final)

    try:
        font = ImageFont.truetype("arial.ttf", 160)
    except:
        font = ImageFont.load_default()

    text = f"{p}%"
    bbox = draw.textbbox((0,0),text,font=font)
    x = 410 - (bbox[2]//2)

    draw.text((x+6,80+6),text,fill=(0,0,0),font=font)
    draw.text((x,80),text,fill=(255,255,255),font=font)

    buf = io.BytesIO()
    final.save(buf,"PNG")
    buf.seek(0)

    file = discord.File(buf,"ship.png")

    e = discord.Embed(title="ANÁLISIS DE COMPATIBILIDAD", color=COLOR)
    e.description = (
        f"{u1.mention} + {u2.mention}\n\n"
        f"Resultado: {p}%\n\n"
        f"{SEP}\n"
        f"Compatibilidad generada mediante algoritmo aleatorio."
    )
    e.set_image(url="attachment://ship.png")

    await i.response.send_message(embed=e,file=file)

# --- REGALAR ---
@bot.tree.command(name="regalar")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(i, user:discord.Member, cantidad:int):
    uid=str(user.id)
    cartera[uid]=cartera.get(uid,0)+cantidad

    e=discord.Embed(title="TRANSFERENCIA AUTORIZADA",color=COLOR)
    e.set_thumbnail(url=user.display_avatar.url)
    e.description=(
        f"Beneficiario: {user.mention}\n"
        f"Monto: ${cantidad:,}\n"
        f"Administrador: {i.user.mention}\n"
        f"Nuevo saldo: ${cartera[uid]:,}\n\n{SEP}"
    )
    await i.response.send_message(embed=e)

# --- TRANSFERIR ---
@bot.tree.command(name="transferir")
async def transferir(i, user:discord.Member, cantidad:int):
    uid=str(i.user.id)
    uid2=str(user.id)

    if cartera.get(uid,0)<cantidad:
        return await i.response.send_message("Fondos insuficientes",ephemeral=True)

    cartera[uid]-=cantidad
    cartera[uid2]=cartera.get(uid2,0)+cantidad

    e=discord.Embed(title="TRANSFERENCIA EJECUTADA",color=COLOR)
    e.description=(
        f"Emisor: {i.user.mention}\n"
        f"Receptor: {user.mention}\n"
        f"Monto: ${cantidad:,}\n\n{SEP}"
    )
    await i.response.send_message(embed=e)

# --- TRABAJO ---
@bot.tree.command(name="trabajo")
async def trabajo(i):
    dinero=random.randint(50,300)
    uid=str(i.user.id)
    cartera[uid]+=dinero

    e=discord.Embed(title="ACTIVIDAD LABORAL COMPLETADA",color=COLOR)
    e.description=f"Ingreso generado: ${dinero:,}\n\n{SEP}"
    await i.response.send_message(embed=e)

# --- ROBLOX ---
@bot.tree.command(name="roblox")
async def roblox(i,usuario:str):
    try:
        r=requests.post("https://users.roblox.com/v1/usernames/users",json={"usernames":[usuario]}).json()
        if not r["data"]:
            return await i.response.send_message("No encontrado",ephemeral=True)

        uid=r["data"][0]["id"]
        avatar=requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png").json()["data"][0]["imageUrl"]

        e=discord.Embed(title="PERFIL ROBLOX",color=COLOR)
        e.description=f"Usuario: {usuario}\nID: {uid}"
        e.set_image(url=avatar)

        await i.response.send_message(embed=e)
    except:
        await i.response.send_message("Error",ephemeral=True)

# --- INTERACCIONES CON GIFS ---
@bot.tree.command(name="beso")
async def beso(i,u:discord.Member):
    gif=get_gif("anime kiss")
    e=discord.Embed(title="INTERACCIÓN: BESO",color=COLOR)
    e.description=f"{i.user.mention} besa a {u.mention}"
    e.set_image(url=gif)
    await i.response.send_message(embed=e)

@bot.tree.command(name="abrazo")
async def abrazo(i,u:discord.Member):
    gif=get_gif("anime hug")
    e=discord.Embed(title="INTERACCIÓN: ABRAZO",color=COLOR)
    e.description=f"{i.user.mention} abraza a {u.mention}"
    e.set_image(url=gif)
    await i.response.send_message(embed=e)

@bot.tree.command(name="golpe")
async def golpe(i,u:discord.Member):
    gif=get_gif("anime slap")
    e=discord.Embed(title="INTERACCIÓN: GOLPE",color=COLOR)
    e.description=f"{i.user.mention} golpea a {u.mention}"
    e.set_image(url=gif)
    await i.response.send_message(embed=e)

# --- START ---
keep_alive()
bot.run(TOKEN)
