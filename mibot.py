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
COLOR = 0x000000
SEP = "━━━━━━━━━━━━━━━━━━━━━━"

# --- BOT ---
class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

# --- TENOR GIF ---
def get_gif(query):
    url = f"https://g.tenor.com/v1/search?q={query}&key={TENOR_KEY}&limit=10"
    r = requests.get(url).json()
    return random.choice(r["results"])["media"][0]["gif"]["url"]

# --- DINERO ---
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

    e = discord.Embed(title="SISTEMA FINANCIERO", color=COLOR)
    e.set_thumbnail(url=i.user.display_avatar.url)
    e.description = (
        f"Usuario: {i.user.mention}\n"
        f"Saldo: ${money:,}\n\n"
        f"{SEP}\n"
        f"Ingreso automático:\n+5 cada 10 segundos\n"
        f"Estado: ACTIVO"
    )
    await i.response.send_message(embed=e)

# --- SHIP ---
@bot.tree.command(name="ship")
async def ship(i: discord.Interaction, u1: discord.Member, u2: discord.Member):
    p = random.randint(0, 100)

    img1 = Image.open(io.BytesIO(requests.get(u1.display_avatar.url).content)).resize((256,256))
    img2 = Image.open(io.BytesIO(requests.get(u2.display_avatar.url).content)).resize((256,256))

    final = Image.new("RGBA",(900,256),(0,0,0,0))
    final.paste(img1,(0,0))
    final.paste(img2,(644,0))

    draw = ImageDraw.Draw(final)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 180)
    except:
        font = ImageFont.load_default()

    text = f"{p}%"
    bbox = draw.textbbox((0,0),text,font=font)
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]

    x = (900//2)-(w//2)
    y = (256//2)-(h//2)

    draw.text((x+8,y+8),text,fill=(0,0,0),font=font)
    draw.text((x,y),text,fill=(255,255,255),font=font)

    buf = io.BytesIO()
    final.save(buf,"PNG")
    buf.seek(0)

    file = discord.File(buf,"ship.png")

    e = discord.Embed(title="COMPATIBILIDAD", color=COLOR)
    e.description = f"{u1.mention} + {u2.mention}\nResultado: {p}%"
    e.set_image(url="attachment://ship.png")

    await i.response.send_message(embed=e,file=file)

# --- DELETE ---
@bot.tree.command(name="delete")
@app_commands.checks.has_permissions(administrator=True)
async def delete(i, cantidad:int):
    await i.channel.purge(limit=cantidad)
    e = discord.Embed(title="LIMPIEZA", color=COLOR)
    e.description = f"{cantidad} mensajes eliminados correctamente"
    await i.response.send_message(embed=e, ephemeral=True)

# --- INTERACCIONES ---
@bot.tree.command(name="beso")
async def beso(i,u:discord.Member):
    e=discord.Embed(title="BESO",color=COLOR)
    e.description=f"{i.user.mention} besa a {u.mention}"
    e.set_image(url=get_gif("anime kiss"))
    await i.response.send_message(embed=e)

@bot.tree.command(name="abrazo")
async def abrazo(i,u:discord.Member):
    e=discord.Embed(title="ABRAZO",color=COLOR)
    e.description=f"{i.user.mention} abraza a {u.mention}"
    e.set_image(url=get_gif("anime hug"))
    await i.response.send_message(embed=e)

@bot.tree.command(name="golpe")
async def golpe(i,u:discord.Member):
    e=discord.Embed(title="GOLPE",color=COLOR)
    e.description=f"{i.user.mention} golpea a {u.mention}"
    e.set_image(url=get_gif("anime slap"))
    await i.response.send_message(embed=e)

# --- INTERACTIVOS ---
@bot.tree.command(name="dado")
async def dado(i): await i.response.send_message(embed=discord.Embed(title="DADO",description=str(random.randint(1,6)),color=COLOR))

@bot.tree.command(name="coinflip")
async def coin(i): await i.response.send_message(embed=discord.Embed(title="COINFLIP",description=random.choice(["Cara","Cruz"]),color=COLOR))

@bot.tree.command(name="iq")
async def iq(i,u:Optional[discord.Member]=None):
    u=u or i.user
    await i.response.send_message(embed=discord.Embed(title="IQ",description=f"{u.mention}: {random.randint(50,200)}",color=COLOR))

@bot.tree.command(name="8ball")
async def ball(i,pregunta:str):
    r=["Sí","No","Tal vez","Probablemente","No"]
    await i.response.send_message(embed=discord.Embed(title="8BALL",description=random.choice(r),color=COLOR))

@bot.tree.command(name="meme")
async def meme(i):
    r=requests.get("https://meme-api.com/gimme").json()
    e=discord.Embed(title=r["title"],color=COLOR)
    e.set_image(url=r["url"])
    await i.response.send_message(embed=e)

# --- UTILIDAD SERVIDOR (15) ---
@bot.tree.command(name="userinfo")
async def userinfo(i, user: Optional[discord.Member]=None):
    user = user or i.user
    e=discord.Embed(title="USER INFO",color=COLOR)
    e.set_thumbnail(url=user.display_avatar.url)
    e.description=f"{user.mention}\nID:{user.id}\nCreado:{user.created_at.strftime('%d/%m/%Y')}"
    await i.response.send_message(embed=e)

@bot.tree.command(name="serverinfo")
async def serverinfo(i):
    g=i.guild
    e=discord.Embed(title="SERVER INFO",color=COLOR)
    e.description=f"{g.name}\nMiembros:{g.member_count}"
    await i.response.send_message(embed=e)

@bot.tree.command(name="avatar")
async def avatar(i,user:Optional[discord.Member]=None):
    user=user or i.user
    e=discord.Embed(title="AVATAR",color=COLOR)
    e.set_image(url=user.display_avatar.url)
    await i.response.send_message(embed=e)

@bot.tree.command(name="ping")
async def ping(i):
    e=discord.Embed(title="PING",description=f"{round(bot.latency*1000)}ms",color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="say")
async def say(i,mensaje:str):
    e=discord.Embed(title="MENSAJE",description=mensaje,color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="reglas")
async def reglas(i):
    e=discord.Embed(title="REGLAS",color=COLOR)
    e.description="Respeto\nNo spam\nNo contenido ilegal"
    await i.response.send_message(embed=e)

@bot.tree.command(name="warn")
async def warn(i,user:discord.Member,motivo:str):
    uid=str(user.id)
    warnings[uid]=warnings.get(uid,0)+1
    e=discord.Embed(title="WARN",color=COLOR)
    e.description=f"{user.mention}\nMotivo:{motivo}\nTotal:{warnings[uid]}"
    await i.response.send_message(embed=e)

@bot.tree.command(name="clearwarns")
async def clearwarns(i,user:discord.Member):
    warnings[str(user.id)]=0
    await i.response.send_message(embed=discord.Embed(title="WARNS LIMPIADOS",color=COLOR))

# --- START ---
keep_alive()
bot.run(TOKEN)
