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
TENOR_KEY = "LIVDSRZULELA"

cartera = {}
cooldowns = {}
warnings = {}
afk_users = {}

COLOR = 0x000000
SEP = "━━━━━━━━━━━━━━━━━━━━━━"

# --- BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

# --- TENOR ---
def get_gif(query):
    url = f"https://g.tenor.com/v1/search?q={query}&key={TENOR_KEY}&limit=10"
    r = requests.get(url).json()
    return random.choice(r["results"])["media"][0]["gif"]["url"]

# --- EVENTO UNIFICADO ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)

    # ECONOMÍA
    if time.time() - cooldowns.get(uid, 0) > 10:
        cartera[uid] = cartera.get(uid, 0) + 5
        cooldowns[uid] = time.time()

    # AFK
    if uid in afk_users:
        del afk_users[uid]
        await message.channel.send(f"{message.author.mention} ya no está AFK")

    for user in message.mentions:
        if str(user.id) in afk_users:
            await message.channel.send(f"{user.name} está AFK: {afk_users[str(user.id)]}")

    await bot.process_commands(message)

# --- COMANDOS ---

@bot.tree.command(name="cartera")
async def cartera_cmd(i: discord.Interaction):
    money = cartera.get(str(i.user.id), 0)
    e = discord.Embed(title="SISTEMA FINANCIERO", color=COLOR)
    e.set_thumbnail(url=i.user.display_avatar.url)
    e.description = f"{i.user.mention}\nSaldo: ${money:,}\n{SEP}\n+5 cada 10s"
    await i.response.send_message(embed=e)

@bot.tree.command(name="afk")
async def afk(i, motivo:str="Ausente"):
    afk_users[str(i.user.id)] = motivo
    await i.response.send_message(embed=discord.Embed(title="AFK", description=motivo, color=COLOR))

@bot.tree.command(name="serverinfo")
async def serverinfo(i: discord.Interaction):
    g = i.guild
    e = discord.Embed(title="INFO SERVIDOR", color=COLOR)
    if g.icon:
        e.set_thumbnail(url=g.icon.url)

    e.description = (
        f"Nombre: {g.name}\nID: {g.id}\n\n"
        f"{SEP}\nDueño: {g.owner}\nCreado: {g.created_at.strftime('%d/%m/%Y')}\n\n"
        f"{SEP}\nMiembros: {g.member_count}\nRoles: {len(g.roles)}\nCanales: {len(g.channels)}"
    )
    await i.response.send_message(embed=e)

@bot.tree.command(name="ship")
async def ship(i: discord.Interaction, u1: discord.Member, u2: discord.Member):
    p = random.randint(0,100)

    img1 = Image.open(io.BytesIO(requests.get(u1.display_avatar.url).content)).resize((256,256))
    img2 = Image.open(io.BytesIO(requests.get(u2.display_avatar.url).content)).resize((256,256))

    final = Image.new("RGBA",(900,256),(0,0,0,0))
    final.paste(img1,(0,0))
    final.paste(img2,(644,0))

    draw = ImageDraw.Draw(final)
    font = ImageFont.truetype("DejaVuSans-Bold.ttf",180)

    text=f"{p}%"
    bbox=draw.textbbox((0,0),text,font=font)
    x=(900//2)-(bbox[2]//2)
    y=(256//2)-(bbox[3]//2)

    draw.text((x,y),text,fill=(255,255,255),font=font)

    buf=io.BytesIO()
    final.save(buf,"PNG")
    buf.seek(0)

    file=discord.File(buf,"ship.png")

    e=discord.Embed(title="COMPATIBILIDAD",color=COLOR)
    e.set_image(url="attachment://ship.png")

    await i.response.send_message(embed=e,file=file)

@bot.tree.command(name="delete")
@app_commands.checks.has_permissions(administrator=True)
async def delete(i,cantidad:int):
    await i.channel.purge(limit=cantidad)
    await i.response.send_message(embed=discord.Embed(title="LIMPIEZA",description=f"{cantidad} mensajes eliminados",color=COLOR),ephemeral=True)

# --- GIFS ---
@bot.tree.command(name="beso")
async def beso(i,u:discord.Member):
    e=discord.Embed(title="BESO",color=COLOR)
    e.set_image(url=get_gif("anime kiss"))
    await i.response.send_message(embed=e)

@bot.tree.command(name="abrazo")
async def abrazo(i,u:discord.Member):
    e=discord.Embed(title="ABRAZO",color=COLOR)
    e.set_image(url=get_gif("anime hug"))
    await i.response.send_message(embed=e)

# --- INTERACTIVO BOTÓN ---
class TrabajoView(discord.ui.View):
    @discord.ui.button(label="Trabajar", style=discord.ButtonStyle.green)
    async def trabajar(self, interaction, button):
        dinero=random.randint(50,200)
        uid=str(interaction.user.id)
        cartera[uid]=cartera.get(uid,0)+dinero

        await interaction.response.send_message(
            embed=discord.Embed(title="TRABAJO",description=f"${dinero}",color=COLOR),
            ephemeral=True
        )

@bot.tree.command(name="trabajo")
async def trabajo(i):
    await i.response.send_message(
        embed=discord.Embed(title="TRABAJO INTERACTIVO",color=COLOR),
        view=TrabajoView()
    )

# --- START ---
keep_alive()
bot.run(TOKEN)
