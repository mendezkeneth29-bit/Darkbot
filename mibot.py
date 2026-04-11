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
    embed = discord.Embed(title="CARTERA", color=COLOR)
    embed.description = f"Dinero actual: ${money:,}"
    await interaction.response.send_message(embed=embed)

# --- SHIP ULTRA ---
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
        font = ImageFont.truetype("arial.ttf", 140)
    except:
        font = ImageFont.load_default()

    text = f"{p}%"
    bbox = draw.textbbox((0,0),text,font=font)
    x = 400 - (bbox[2]//2)

    draw.text((x+5,90+5),text,fill=(0,0,0),font=font)
    draw.text((x,90),text,fill=(255,255,255),font=font)

    buf = io.BytesIO()
    final.save(buf,"PNG")
    buf.seek(0)

    file = discord.File(buf,"ship.png")
    embed = discord.Embed(title="COMPATIBILIDAD", color=COLOR)
    embed.set_image(url="attachment://ship.png")

    await interaction.response.send_message(embed=embed,file=file)

# --- REGALAR ---
@bot.tree.command(name="regalar")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction, user:discord.Member, cantidad:int):
    uid=str(user.id)
    cartera[uid]=cartera.get(uid,0)+cantidad

    embed=discord.Embed(title="REGALO",color=COLOR)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.description=f"{user.mention} recibió ${cantidad:,}\nNuevo saldo: ${cartera[uid]:,}"
    await interaction.response.send_message(embed=embed)

# --- TRANSFERIR ---
@bot.tree.command(name="transferir")
async def transferir(interaction,user:discord.Member,cantidad:int):
    uid=str(interaction.user.id)
    uid2=str(user.id)

    if cartera.get(uid,0)<cantidad:
        return await interaction.response.send_message("No tienes dinero",ephemeral=True)

    cartera[uid]-=cantidad
    cartera[uid2]=cartera.get(uid2,0)+cantidad

    embed=discord.Embed(title="TRANSFERENCIA",color=COLOR)
    embed.description=f"{interaction.user.mention} envió ${cantidad:,} a {user.mention}"
    await interaction.response.send_message(embed=embed)

# --- TRABAJO ---
@bot.tree.command(name="trabajo")
async def trabajo(interaction):
    dinero=random.randint(50,300)
    uid=str(interaction.user.id)
    cartera[uid]=cartera.get(uid,0)+dinero

    embed=discord.Embed(title="TRABAJO",color=COLOR)
    embed.description=f"Ganaste ${dinero:,}"
    await interaction.response.send_message(embed=embed)

# --- ROBLOX ---
@bot.tree.command(name="roblox")
async def roblox(interaction,usuario:str):
    try:
        r=requests.post("https://users.roblox.com/v1/usernames/users",json={"usernames":[usuario]}).json()
        if not r["data"]:
            return await interaction.response.send_message("No encontrado",ephemeral=True)

        uid=r["data"][0]["id"]
        avatar=requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png").json()["data"][0]["imageUrl"]

        embed=discord.Embed(title="ROBLOX",color=COLOR)
        embed.description=f"{usuario}\nID: {uid}"
        embed.set_image(url=avatar)

        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("Error",ephemeral=True)

# --- 12 COMANDOS INTERACTIVOS ---

@bot.tree.command(name="dado")
async def dado(i): 
    e=discord.Embed(title="DADO",description=str(random.randint(1,6)),color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="coinflip")
async def coin(i):
    e=discord.Embed(title="COINFLIP",description=random.choice(["Cara","Cruz"]),color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="iq")
async def iq(i,u:Optional[discord.Member]=None):
    u=u or i.user
    e=discord.Embed(title="IQ",description=f"{u.mention}: {random.randint(50,200)}",color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="amor")
async def amor(i,u:discord.Member):
    e=discord.Embed(title="AMOR",description=f"{i.user.mention} ama a {u.mention} un {random.randint(0,100)}%",color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="meme")
async def meme(i):
    r=requests.get("https://meme-api.com/gimme").json()
    e=discord.Embed(title=r["title"],color=COLOR)
    e.set_image(url=r["url"])
    await i.response.send_message(embed=e)

@bot.tree.command(name="8ball")
async def ball(i,pregunta:str):
    respuestas=["Sí","No","Tal vez","Probablemente","No creo"]
    e=discord.Embed(title="8BALL",description=random.choice(respuestas),color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="abrazo")
async def abrazo(i,u:discord.Member):
    e=discord.Embed(title="ABRAZO",description=f"{i.user.mention} abraza a {u.mention}",color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="golpe")
async def golpe(i,u:discord.Member):
    e=discord.Embed(title="GOLPE",description=f"{i.user.mention} golpea a {u.mention}",color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="beso")
async def beso(i,u:discord.Member):
    e=discord.Embed(title="BESO",description=f"{i.user.mention} besa a {u.mention}",color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="insulto")
async def insulto(i):
    lista=["tonto","lento","npc","bug humano"]
    e=discord.Embed(title="INSULTO",description=random.choice(lista),color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="ruleta")
async def ruleta(i):
    e=discord.Embed(title="RULETA",description=str(random.randint(1,6)),color=COLOR)
    await i.response.send_message(embed=e)

@bot.tree.command(name="numero")
async def numero(i):
    e=discord.Embed(title="NÚMERO",description=str(random.randint(0,1000)),color=COLOR)
    await i.response.send_message(embed=e)

# --- DELETE ---
@bot.tree.command(name="delete")
@app_commands.checks.has_permissions(administrator=True)
async def delete(i,cantidad:int):
    await i.channel.purge(limit=cantidad)
    e=discord.Embed(title="LIMPIEZA",description=f"{cantidad} mensajes eliminados",color=COLOR)
    await i.response.send_message(embed=e,ephemeral=True)

# --- START ---
keep_alive()
bot.run(os.getenv("TOKEN"))
