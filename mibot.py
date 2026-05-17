import discord
import os
import io
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import asyncio
import random
import time
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from groq import AsyncGroq
from discord.ext import commands
from discord import app_commands
from flask import Flask
from duckduckgo_search import DDGS
import threading

# -------------------------
# CLIENTES
# -------------------------

groq_client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)

TOKEN = os.getenv("TOKEN")

# -------------------------
# DATA
# -------------------------

warnings_data = {}
afk_data = {}
mensaje_count = {}
wlc_canal = {}
bye_canal = {}
xp_data = {}
nivel_canal = {}
xp_cooldown = {}
economia_data = {}

# -------------------------
# BOT
# -------------------------

class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=">dl ",
            intents=discord.Intents.all()
        )

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

# -------------------------
# EVENTOS
# -------------------------

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")

# =========================================================
# HELPERS TARJETAS
# =========================================================

async def descargar_imagen(url: str) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.read()
    return Image.open(io.BytesIO(data)).convert("RGBA")

def avatar_circular(img: Image.Image, size: int) -> Image.Image:
    img = img.resize((size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    resultado = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    resultado.paste(img, (0, 0), mask)
    return resultado

def fuente(size: int, bold: bool = False):
    opciones = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in opciones:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

# =========================================================
# HELPERS DATA
# =========================================================

def get_xp(guild_id, user_id):
    gid = str(guild_id)
    uid = str(user_id)
    if gid not in xp_data:
        xp_data[gid] = {}
    if uid not in xp_data[gid]:
        xp_data[gid][uid] = {"xp": 0, "level": 1}
    return xp_data[gid][uid]

def xp_para_nivel(nivel):
    return nivel * 100

def get_user_eco(guild_id, user_id):
    gid = str(guild_id)
    uid = str(user_id)
    if gid not in economia_data:
        economia_data[gid] = {}
    if uid not in economia_data[gid]:
        economia_data[gid][uid] = {"coins": 0, "last_daily": 0}
    return economia_data[gid][uid]

# =========================================================
# GENERADORES DE TARJETAS
# =========================================================

async def generar_userinfo(usuario: discord.Member) -> discord.File:
    W, H = 700, 340
    FONDO = (30, 31, 34)
    TEXTO = (255, 255, 255)
    SUBTEXTO = (180, 180, 190)
    CAMPO_FONDO = (40, 43, 48)

    img = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA IZQUIERDA DE COLOR
    color = usuario.color
    r = color.r if color.value else 88
    g = color.g if color.value else 101
    b = color.b if color.value else 242
    draw.rectangle([(0, 0), (6, H)], fill=(r, g, b))

    # AVATAR
    avatar_img = await descargar_imagen(str(usuario.display_avatar.url))
    avatar_img = avatar_circular(avatar_img, 90)
    img.paste(avatar_img, (24, 20), avatar_img)

    # NOMBRE
    draw.text((128, 22), usuario.display_name, font=fuente(26, bold=True), fill=TEXTO)
    draw.text((128, 56), f"@{usuario.name}", font=fuente(16), fill=SUBTEXTO)

    # LÍNEA SEPARADORA
    draw.rectangle([(24, 126), (W - 24, 128)], fill=(60, 63, 70))

    col1_x = 24
    col2_x = 370
    y = 148

    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle(
            [(x, y), (x + ancho, y + 64)],
            radius=8,
            fill=CAMPO_FONDO
        )
        draw.text((x + 12, y + 8), titulo, font=fuente(13), fill=SUBTEXTO)
        draw.text((x + 12, y + 30), valor, font=fuente(17, bold=True), fill=TEXTO)

    # FILA 1
    campo(col1_x, y, "USUARIO", f"@{usuario.display_name}")
    campo(col2_x, y, "ID", str(usuario.id))

    # FILA 2
    y2 = y + 80
    creado = usuario.created_at.strftime("%d/%m/%Y")
    entro = usuario.joined_at.strftime("%d/%m/%Y") if usuario.joined_at else "?"
    campo(col1_x, y2, "CUENTA CREADA", creado)
    campo(col2_x, y2, "ENTRO AL SERVER", entro)

    # FOOTER
    draw.text(
        (24, H - 22),
        f"Solicitado por {usuario.display_name}",
        font=fuente(12),
        fill=SUBTEXTO
    )

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="userinfo.png")


async def generar_serverinfo(guild: discord.Guild, solicitante: discord.Member) -> discord.File:
    W, H = 700, 400
    FONDO = (30, 31, 34)
    TEXTO = (255, 255, 255)
    SUBTEXTO = (180, 180, 190)
    CAMPO_FONDO = (40, 43, 48)

    img = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (6, H)], fill=(88, 101, 242))

    if guild.icon:
        icon_img = await descargar_imagen(str(guild.icon.url))
        icon_img = avatar_circular(icon_img, 90)
        img.paste(icon_img, (24, 20), icon_img)
        nombre_x = 128
    else:
        nombre_x = 24

    draw.text((nombre_x, 22), guild.name, font=fuente(26, bold=True), fill=TEXTO)
    draw.text((nombre_x, 56), f"ID: {guild.id}", font=fuente(14), fill=SUBTEXTO)
    draw.rectangle([(24, 126), (W - 24, 128)], fill=(60, 63, 70))

    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, fill=CAMPO_FONDO)
        draw.text((x + 12, y + 8), titulo, font=fuente(13), fill=SUBTEXTO)
        draw.text((x + 12, y + 30), str(valor), font=fuente(17, bold=True), fill=TEXTO)

    y = 148
    campo(24, y, "OWNER", guild.owner.display_name if guild.owner else "?")
    campo(370, y, "CREADO", guild.created_at.strftime("%d/%m/%Y"))

    y2 = y + 80
    ancho3 = 204
    campo(24,       y2, "MIEMBROS", str(guild.member_count),                                       ancho=ancho3)
    campo(24 + 224, y2, "ROLES",    str(len(guild.roles)),                                         ancho=ancho3)
    campo(24 + 448, y2, "EMOJIS",   str(len(guild.emojis)),                                        ancho=ancho3)

    y3 = y2 + 80
    campo(24,       y3, "TEXTO",  str(len(guild.text_channels)),                                   ancho=ancho3)
    campo(24 + 224, y3, "VOZ",    str(len(guild.voice_channels)),                                  ancho=ancho3)
    campo(24 + 448, y3, "BOOSTS", f"{guild.premium_subscription_count} (nv {guild.premium_tier})", ancho=ancho3)

    draw.text((24, H - 22), f"Solicitado por {solicitante.display_name}", font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="serverinfo.png")


async def generar_nivel(usuario: discord.Member, nivel: int, xp: int, xp_needed: int) -> discord.File:
    W, H = 680, 180
    FONDO    = (14, 14, 14)
    ACENTO   = (245, 240, 232)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (170, 170, 170)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ACENTO)

    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 100)
        img.paste(av, (38, 40), av)
    except:
        draw.ellipse([(38, 40), (138, 140)], fill=GRIS)

    draw.ellipse([(36, 38), (140, 142)], outline=ACENTO, width=2)
    draw.text((162, 28), usuario.display_name, font=fuente(21, bold=True), fill=TEXTO)
    draw.rounded_rectangle([(162, 62), (242, 84)], radius=11, fill=ACENTO)
    draw.text((202, 68), f"Nivel {nivel}", font=fuente(12, bold=True), fill=FONDO, anchor="mt")
    draw.text((162, 100), f"{xp} / {xp_needed} XP", font=fuente(12), fill=SUBTEXTO)
    draw.rounded_rectangle([(162, 118), (630, 130)], radius=6, fill=GRIS)

    progreso = min(xp / xp_needed, 1.0)
    fill_w = int(162 + (468 * progreso))
    if fill_w > 162:
        draw.rounded_rectangle([(162, 118), (fill_w, 130)], radius=6, fill=ACENTO)

    draw.text((162, 152), f"Subiste al nivel {nivel} — sigue asi!", font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="nivel.png")


async def generar_balance(usuario: discord.Member, coins: int, last_daily: float) -> discord.File:
    W, H     = 680, 170
    FONDO    = (14, 14, 14)
    ACENTO   = (245, 240, 232)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ACENTO)

    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 37), av)
    except:
        draw.ellipse([(37, 37), (133, 133)], fill=GRIS)

    draw.ellipse([(35, 35), (135, 135)], outline=ACENTO, width=2)
    draw.text((158, 48), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO)
    draw.rectangle([(158, 90), (640, 91)], fill=GRIS)
    draw.text((158, 106), f"$ {coins:,} monedas", font=fuente(22, bold=True), fill=ACENTO)

    if last_daily == 0:
        daily_texto = "Nunca reclamaste tu daily"
    else:
        hace = int(time.time() - last_daily)
        if hace < 3600:
            daily_texto = f"Ultimo daily: hace {hace // 60} minutos"
        elif hace < 86400:
            daily_texto = f"Ultimo daily: hace {hace // 3600} horas"
        else:
            daily_texto = f"Ultimo daily: hace {hace // 86400} dias"

    draw.text((158, 148), daily_texto, font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="balance.png")


async def generar_ranking(guild: discord.Guild, top: list) -> discord.File:
    filas = len(top)
    W, H  = 680, 130 + (filas * 46)
    FONDO    = (14, 14, 14)
    ACENTO   = (245, 240, 232)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)
    OSCURO   = (21, 21, 21)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ACENTO)
    draw.text((34, 30), "Ranking", font=fuente(18, bold=True), fill=TEXTO)
    draw.text((34, 58), "Top usuarios con mas monedas", font=fuente(11), fill=SUBTEXTO)
    draw.rectangle([(34, 72), (646, 73)], fill=GRIS)

    medallas = ["1", "2", "3"]

    for n, (uid, data) in enumerate(top):
        member = guild.get_member(int(uid))
        nombre = member.display_name if member else f"Usuario {uid}"
        nombre = nombre[:20] + "..." if len(nombre) > 20 else nombre
        y = 82 + (n * 46)
        color_fila = (26, 26, 26) if n == 0 else OSCURO
        draw.rounded_rectangle([(34, y), (646, y + 36)], radius=8, fill=color_fila)
        medalla = f"#{n+1}" if n >= 3 else medallas[n]
        draw.text((54, y + 10), medalla, font=fuente(14, bold=True), fill=ACENTO if n == 0 else SUBTEXTO)
        draw.text((90, y + 10), nombre, font=fuente(13, bold=n == 0), fill=TEXTO)
        draw.text((620, y + 10), f"$ {data['coins']:,}", font=fuente(13), fill=ACENTO if n == 0 else SUBTEXTO, anchor="ra")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ranking.png")


async def generar_ban(usuario: discord.Member, razon: str, moderador: discord.Member) -> discord.File:
    W, H     = 680, 190
    FONDO    = (14, 14, 14)
    ROJO     = (239, 68, 68)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ROJO)

    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 47), av)
    except:
        draw.ellipse([(37, 47), (133, 143)], fill=GRIS)

    draw.ellipse([(35, 45), (135, 145)], outline=ROJO, width=2)
    draw.line([(50, 60), (120, 130)], fill=ROJO, width=3)
    draw.line([(120, 60), (50, 130)], fill=ROJO, width=3)
    draw.text((158, 42), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO)
    draw.rounded_rectangle([(158, 68), (228, 90)], radius=11, fill=ROJO)
    draw.text((193, 74), "Baneado", font=fuente(12, bold=True), fill=TEXTO, anchor="mt")
    draw.rectangle([(158, 104), (645, 105)], fill=GRIS)
    draw.text((158, 116), "RAZON", font=fuente(11), fill=SUBTEXTO)
    razon_texto = razon[:50] + "..." if len(razon) > 50 else razon
    draw.text((158, 134), razon_texto, font=fuente(15, bold=True), fill=TEXTO)
    draw.text((158, 164), f"Moderador: {moderador.display_name}", font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ban.png")


async def generar_afk(usuario: discord.Member, motivo: str) -> discord.File:
    W, H     = 680, 190
    FONDO    = (14, 14, 14)
    ACENTO   = (245, 240, 232)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ACENTO)

    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 47), av)
    except:
        draw.ellipse([(37, 47), (133, 143)], fill=GRIS)

    draw.ellipse([(35, 45), (135, 145)], outline=ACENTO, width=2)
    draw.text((98, 72), "z", font=fuente(17, bold=True), fill=ACENTO)
    draw.text((110, 58), "z", font=fuente(14, bold=True), fill=ACENTO)
    draw.text((120, 46), "z", font=fuente(11), fill=ACENTO)
    draw.text((158, 42), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO)
    draw.rounded_rectangle([(158, 68), (218, 90)], radius=11, fill=ACENTO)
    draw.text((188, 74), "AFK", font=fuente(12, bold=True), fill=FONDO, anchor="mt")
    draw.rectangle([(158, 104), (645, 105)], fill=GRIS)
    draw.text((158, 116), "MOTIVO", font=fuente(11), fill=SUBTEXTO)
    motivo_texto = motivo[:50] + "..." if len(motivo) > 50 else motivo
    draw.text((158, 134), motivo_texto, font=fuente(15, bold=True), fill=TEXTO)
    draw.text((158, 164), "Te avisare si te mencionan...", font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="afk.png")


async def generar_spotify(usuario: discord.Member, actividad: discord.Spotify) -> discord.File:
    W, H     = 680, 180
    FONDO    = (14, 14, 14)
    VERDE    = (29, 185, 84)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=VERDE)

    try:
        portada = await descargar_imagen(actividad.album_cover_url)
        portada = portada.resize((130, 130)).convert("RGBA")
        mask = Image.new("L", (130, 130), 0)
        ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (130, 130)], radius=10, fill=255)
        portada_r = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
        portada_r.paste(portada, (0, 0), mask)
        img.paste(portada_r, (30, 25), portada_r)
    except:
        draw.rounded_rectangle([(30, 25), (160, 155)], radius=10, fill=GRIS)

    draw.rounded_rectangle([(29, 24), (161, 156)], radius=10, outline=VERDE, width=2)
    draw.text((182, 28), f"{usuario.display_name} esta escuchando", font=fuente(13), fill=SUBTEXTO)

    cancion = actividad.title[:30] + "..." if len(actividad.title) > 30 else actividad.title
    draw.text((182, 50), cancion, font=fuente(20, bold=True), fill=TEXTO)
    draw.text((182, 78), actividad.artist, font=fuente(14), fill=VERDE)

    album = actividad.album[:35] + "..." if len(actividad.album) > 35 else actividad.album
    draw.text((182, 100), album, font=fuente(12), fill=SUBTEXTO)
    draw.rectangle([(182, 118), (645, 119)], fill=GRIS)

    ahora        = discord.utils.utcnow()
    duracion     = actividad.duration.total_seconds()
    transcurrido = (ahora - actividad.start).total_seconds()
    progreso     = min(transcurrido / duracion, 1.0) if duracion > 0 else 0

    draw.rounded_rectangle([(182, 128), (645, 136)], radius=4, fill=GRIS)
    fill_w = int(182 + (463 * progreso))
    if fill_w > 182:
        draw.rounded_rectangle([(182, 128), (fill_w, 136)], radius=4, fill=VERDE)

    fmt = lambda s: f"{int(s) // 60}:{int(s) % 60:02}"
    draw.text((182, 148), fmt(max(transcurrido, 0)), font=fuente(11), fill=SUBTEXTO)
    draw.text((645, 148), fmt(duracion), font=fuente(11), fill=SUBTEXTO, anchor="ra")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="spotify.png")
    
# =========================================================
# USERINFO
# =========================================================

@bot.tree.command(name="userinfo")
async def userinfo_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    await i.followup.send(file=await generar_userinfo(usuario))

@bot.command(name="userinfo")
async def userinfo_prefix(ctx, usuario: discord.Member = None):
    usuario = usuario or ctx.author
    await ctx.send(file=await generar_userinfo(usuario))

# =========================================================
# SERVERINFO
# =========================================================

@bot.tree.command(name="serverinfo")
async def serverinfo_slash(i: discord.Interaction):
    await i.response.defer()
    await i.followup.send(file=await generar_serverinfo(i.guild, i.user))

@bot.command(name="serverinfo")
async def serverinfo_prefix(ctx):
    await ctx.send(file=await generar_serverinfo(ctx.guild, ctx.author))

# =========================================================
# BAN
# =========================================================

@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_slash(i: discord.Interaction, usuario: discord.Member, razon: str = "Sin razon"):
    if usuario == i.user:
        await i.response.send_message("> No puedes banearte a ti mismo", ephemeral=True)
        return
    await i.response.defer()
    try:
        await usuario.ban(reason=razon)
        await i.followup.send(file=await generar_ban(usuario, razon, i.user))
    except Exception as e:
        await i.followup.send(f"Error:\n```{e}```", ephemeral=True)

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_prefix(ctx, usuario: discord.Member, *, razon: str = "Sin razon"):
    if usuario == ctx.author:
        await ctx.send("> No puedes banearte a ti mismo")
        return
    try:
        await usuario.ban(reason=razon)
        await ctx.send(file=await generar_ban(usuario, razon, ctx.author))
    except Exception as e:
        await ctx.send(f"Error:\n```{e}```")

# =========================================================
# AFK
# =========================================================

@bot.tree.command(name="afk")
async def afk_slash(i: discord.Interaction, motivo: str = "Sin motivo"):
    await i.response.defer()
    afk_data[i.user.id] = {"motivo": motivo, "tiempo": time.time()}
    usuario = i.guild.get_member(i.user.id)
    await i.followup.send(file=await generar_afk(usuario, motivo))

@bot.command(name="afk")
async def afk_prefix(ctx, *, motivo: str = "Sin motivo"):
    afk_data[ctx.author.id] = {"motivo": motivo, "tiempo": time.time()}
    await ctx.send(file=await generar_afk(ctx.author, motivo))

# =========================================================
# AVATAR
# =========================================================

@bot.tree.command(name="avatar")
async def avatar_slash(i: discord.Interaction, usuario: discord.Member = None):
    usuario = usuario or i.user
    embed = discord.Embed(title=f"Avatar de {usuario.name}", color=0x000000)
    embed.set_image(url=usuario.display_avatar.url)
    await i.response.send_message(embed=embed)

@bot.command(name="avatar")
async def avatar_prefix(ctx, usuario: discord.Member = None):
    usuario = usuario or ctx.author
    embed = discord.Embed(title=f"Avatar de {usuario.name}", color=0x000000)
    embed.set_image(url=usuario.display_avatar.url)
    await ctx.send(embed=embed)

# =========================================================
# SPOTIFY
# =========================================================

@bot.tree.command(name="spotify", description="Muestra la musica que escucha un usuario")
async def spotify_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    actividad = discord.utils.find(lambda a: isinstance(a, discord.Spotify), usuario.activities)
    if not actividad:
        await i.followup.send(f"> **{usuario.name} no esta escuchando Spotify**",)
        return
    await i.followup.send(file=await generar_spotify(usuario, actividad))

@bot.command(name="spotify")
async def spotify_prefix(ctx, usuario: discord.Member = None):
    usuario = usuario or ctx.author
    actividad = discord.utils.find(lambda a: isinstance(a, discord.Spotify), usuario.activities)
    if not actividad:
        await ctx.send(f"**{usuario.display_name} no esta escuchando Spotify**")
        return
    await ctx.send(file=await generar_spotify(usuario, actividad))
    
# =========================================================
# NIVEL
# =========================================================

@bot.tree.command(name="nivel", description="Ve tu nivel actual")
async def nivel_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    data = get_xp(i.guild.id, usuario.id)
    await i.followup.send(file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.command(name="nivel")
async def nivel_prefix(ctx, usuario: discord.Member = None):
    usuario = usuario or ctx.author
    data = get_xp(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

# =========================================================
# BALANCE
# =========================================================

@bot.tree.command(name="balance", description="Ve tu cuenta bancaria")
async def balance_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    data = get_user_eco(i.guild.id, usuario.id)
    await i.followup.send(file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.command(name="balance")
async def balance_prefix(ctx, usuario: discord.Member = None):
    usuario = usuario or ctx.author
    data = get_user_eco(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_balance(usuario, data["coins"], data["last_daily"]))

# =========================================================
# DAILY
# =========================================================

@bot.tree.command(name="daily", description="Reclama tus monedas diarias")
async def daily_slash(i: discord.Interaction):
    await i.response.defer()
    data = get_user_eco(i.guild.id, i.user.id)
    ahora = time.time()
    if ahora - data["last_daily"] < 86400:
        restante = int(86400 - (ahora - data["last_daily"]))
        h, m, s = restante // 3600, (restante % 3600) // 60, restante % 60
        await i.followup.send(f"> Vuelve en `{h:02}:{m:02}:{s:02}`", ephemeral=True)
        return
    recompensa = random.randint(100, 500)
    data["coins"] += recompensa
    data["last_daily"] = ahora
    await i.followup.send(content=f"> Recibiste **{recompensa}** monedas!", file=await generar_balance(i.guild.get_member(i.user.id), data["coins"], data["last_daily"]))

@bot.command(name="daily")
async def daily_prefix(ctx):
    data = get_user_eco(ctx.guild.id, ctx.author.id)
    ahora = time.time()
    if ahora - data["last_daily"] < 86400:
        restante = int(86400 - (ahora - data["last_daily"]))
        h, m, s = restante // 3600, (restante % 3600) // 60, restante % 60
        await ctx.send(f"> Vuelve en `{h:02}:{m:02}:{s:02}`")
        return
    recompensa = random.randint(100, 500)
    data["coins"] += recompensa
    data["last_daily"] = ahora
    await ctx.send(content=f"> Recibiste **{recompensa}** monedas!", file=await generar_balance(ctx.author, data["coins"], data["last_daily"]))

# =========================================================
# RANKING
# =========================================================

@bot.tree.command(name="ranking", description="Top de usuarios con mas monedas")
async def ranking_slash(i: discord.Interaction):
    await i.response.defer()
    gid = str(i.guild.id)
    if gid not in economia_data or not economia_data[gid]:
        await i.followup.send("> Nadie tiene monedas todavia.", ephemeral=True)
        return
    top = sorted(economia_data[gid].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
    await i.followup.send(file=await generar_ranking(i.guild, top))

@bot.command(name="ranking")
async def ranking_prefix(ctx):
    gid = str(ctx.guild.id)
    if gid not in economia_data or not economia_data[gid]:
        await ctx.send("> Nadie tiene monedas todavia.")
        return
    top = sorted(economia_data[gid].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
    await ctx.send(file=await generar_ranking(ctx.guild, top))

# =========================================================
# GENERAR TARJETA WARN
# =========================================================

async def generar_warn(usuario: discord.Member, razon: str, total: int) -> discord.File:
    W, H     = 680, 180
    FONDO    = (14, 14, 14)
    AMARILLO = (245, 158, 11)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA LATERAL
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AMARILLO)

    # TRIANGULO
    triangulo = [(80, 22), (138, 122), (22, 122)]
    draw.polygon(triangulo, fill=AMARILLO)

    # SIGNO !
    draw.rounded_rectangle([(75, 44), (85, 90)], radius=5, fill=FONDO)
    draw.ellipse([(74, 102), (86, 114)], fill=FONDO)

    # NOMBRE
    draw.text((162, 28), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO)

    # BADGE
    draw.rounded_rectangle([(162, 56), (252, 78)], radius=11, fill=AMARILLO)
    draw.text((207, 62), "Advertido", font=fuente(12, bold=True), fill=FONDO, anchor="mt")

    # SEPARADOR
    draw.rectangle([(162, 92), (645, 93)], fill=GRIS)

    # RAZON
    draw.text((162, 104), "RAZON", font=fuente(11), fill=SUBTEXTO)
    razon_texto = razon[:50] + "..." if len(razon) > 50 else razon
    draw.text((162, 122), razon_texto, font=fuente(15, bold=True), fill=TEXTO)

    # TOTAL WARNS
    draw.text((162, 154), f"Total de warns: {total}", font=fuente(12), fill=AMARILLO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="warn.png")

# =========================================================
# GENERAR TARJETA WARNINGS
# =========================================================

async def generar_warnings(usuario: discord.Member, warns: list) -> discord.File:
    filas = min(len(warns), 10)
    W     = 680
    H     = 90 + (filas * 44)
    FONDO    = (14, 14, 14)
    AMARILLO = (245, 158, 11)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)
    OSCURO   = (21, 21, 21)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA LATERAL
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AMARILLO)

    # TITULO
    draw.text((34, 24), f"Warns de {usuario.display_name}", font=fuente(18, bold=True), fill=TEXTO)
    draw.rectangle([(34, 44), (646, 45)], fill=GRIS)

    # FILAS
    for n, w in enumerate(warns[:10]):
        y = 54 + (n * 44)
        color_fila = (26, 26, 26) if n % 2 == 0 else OSCURO
        draw.rounded_rectangle([(34, y), (646, y + 34)], radius=8, fill=color_fila)

        # NUMERO
        draw.text((54, y + 8), f"#{n+1}", font=fuente(13, bold=True), fill=AMARILLO)

        # RAZON
        razon = w["razon"][:40] + "..." if len(w["razon"]) > 40 else w["razon"]
        draw.text((88, y + 10), razon, font=fuente(13), fill=TEXTO)

        # MODERADOR
        mod = w["moderador"][:20] + "..." if len(w["moderador"]) > 20 else w["moderador"]
        draw.text((634, y + 10), mod, font=fuente(11), fill=SUBTEXTO, anchor="ra")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="warnings.png")

# =========================================================
# COMANDO WARN
# =========================================================

@bot.tree.command(name="warn")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn_slash(i: discord.Interaction, usuario: discord.Member, razon: str):
    await i.response.defer()
    gid, uid = str(i.guild.id), str(usuario.id)
    if gid not in warnings_data: warnings_data[gid] = {}
    if uid not in warnings_data[gid]: warnings_data[gid][uid] = []
    warnings_data[gid][uid].append({"razon": razon, "moderador": str(i.user), "fecha": str(datetime.now())})
    total = len(warnings_data[gid][uid])
    await i.followup.send(file=await generar_warn(usuario, razon, total))

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def warn_prefix(ctx, usuario: discord.Member, *, razon: str):
    gid, uid = str(ctx.guild.id), str(usuario.id)
    if gid not in warnings_data: warnings_data[gid] = {}
    if uid not in warnings_data[gid]: warnings_data[gid][uid] = []
    warnings_data[gid][uid].append({"razon": razon, "moderador": str(ctx.author), "fecha": str(datetime.now())})
    total = len(warnings_data[gid][uid])
    await ctx.send(file=await generar_warn(usuario, razon, total))

# =========================================================
# COMANDO WARNINGS
# =========================================================

@bot.tree.command(name="warnings")
async def warnings_slash(i: discord.Interaction, usuario: discord.Member):
    await i.response.defer()
    gid, uid = str(i.guild.id), str(usuario.id)
    if gid not in warnings_data or uid not in warnings_data[gid]:
        await i.followup.send("> Ese usuario no tiene warnings", ephemeral=True)
        return
    await i.followup.send(file=await generar_warnings(usuario, warnings_data[gid][uid]))

@bot.command(name="warnings")
async def warnings_prefix(ctx, usuario: discord.Member):
    gid, uid = str(ctx.guild.id), str(usuario.id)
    if gid not in warnings_data or uid not in warnings_data[gid]:
        await ctx.send("> Ese usuario no tiene warnings")
        return
    await ctx.send(file=await generar_warnings(usuario, warnings_data[gid][uid]))

# =========================================================
# GENERAR TARJETA LOCK
# =========================================================

async def generar_lock(canal: discord.TextChannel, bloqueado: bool) -> discord.File:
    W, H     = 680, 170
    FONDO    = (14, 14, 14)
    COLOR    = (239, 68, 68) if bloqueado else (34, 197, 94)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA LATERAL
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=COLOR)

    # CUERPO DEL CANDADO
    draw.rounded_rectangle([(44, 88), (116, 144)], radius=8, fill=COLOR)

    if bloqueado:
        # ARCO CERRADO - semicírculo perfecto
        draw.arc([(56, 42), (104, 98)], start=180, end=0, fill=COLOR, width=10)
    else:
        # ARCO ABIERTO - desplazado arriba sin cerrar
        draw.arc([(68, 30), (116, 86)], start=180, end=360, fill=COLOR, width=10)

    # AGUJERO LLAVE
    draw.ellipse([(71, 103), (89, 121)], fill=FONDO)
    draw.rounded_rectangle([(76, 112), (84, 126)], radius=3, fill=FONDO)

    # TITULO
    titulo = "Canal Bloqueado" if bloqueado else "Canal Desbloqueado"
    draw.text((144, 32), titulo, font=fuente(22, bold=True), fill=TEXTO)

    # SEPARADOR
    draw.rectangle([(144, 62), (654, 63)], fill=GRIS)

    # CANAL
    draw.text((144, 76), "CANAL", font=fuente(12), fill=SUBTEXTO)
    draw.text((144, 96), f"# {canal.name}", font=fuente(15, bold=True), fill=TEXTO)

    # MENSAJE
    msg = "Nadie puede enviar mensajes." if bloqueado else "Ya pueden enviar mensajes."
    draw.text((144, 136), msg, font=fuente(13), fill=COLOR)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="lock.png")

# =========================================================
# LOCK
# =========================================================

@bot.tree.command(name="lock")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock_slash(i: discord.Interaction):
    await i.response.defer()
    ow = i.channel.overwrites_for(i.guild.default_role)
    ow.send_messages = False
    await i.channel.set_permissions(i.guild.default_role, overwrite=ow)
    await i.followup.send(file=await generar_lock(i.channel, bloqueado=True))

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_prefix(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    await ctx.send(file=await generar_lock(ctx.channel, bloqueado=True))

# =========================================================
# UNLOCK
# =========================================================

@bot.tree.command(name="unlock")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock_slash(i: discord.Interaction):
    await i.response.defer()
    ow = i.channel.overwrites_for(i.guild.default_role)
    ow.send_messages = True
    await i.channel.set_permissions(i.guild.default_role, overwrite=ow)
    await i.followup.send(file=await generar_lock(i.channel, bloqueado=False))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_prefix(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    await ctx.send(file=await generar_lock(ctx.channel, bloqueado=False))
# =========================================================
# NUKE
# =========================================================

@bot.tree.command(name="nuke")
@app_commands.checks.has_permissions(manage_channels=True)
async def nuke_slash(i: discord.Interaction):
    canal = i.channel
    nuevo = await canal.clone()
    await canal.delete()
    await nuevo.send(embed=discord.Embed(title="Canal Nukeado", description="> Canal purificado exitosamente.", color=0x000000))

@bot.command(name="nuke")
@commands.has_permissions(manage_channels=True)
async def nuke_prefix(ctx):
    canal = ctx.channel
    nuevo = await canal.clone()
    await canal.delete()
    await nuevo.send(embed=discord.Embed(title="Canal Nukeado", description="> Canal purificado exitosamente.", color=0x000000))

# =========================================================
# DELETE
# =========================================================

@bot.tree.command(name="delete")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete_slash(i: discord.Interaction, cantidad: app_commands.Range[int, 1, 1000]):
    await i.response.defer(ephemeral=True)
    eliminados = await i.channel.purge(limit=cantidad)
    await i.followup.send(f"> Se eliminaron {len(eliminados)} mensajes", ephemeral=True)

@bot.command(name="delete")
@commands.has_permissions(manage_messages=True)
async def delete_prefix(ctx, cantidad: int):
    eliminados = await ctx.channel.purge(limit=cantidad + 1)
    await ctx.send(f"Se eliminaron {len(eliminados) - 1} mensajes", delete_after=3)

# =========================================================
# EMBED CREATE
# =========================================================

@bot.hybrid_command(
    name="embed", 
    description="Crea un embed totalmente personalizado"
)
async def crear_embed(
    ctx: commands.Context,
    titulo: typing.Optional[str] = None,
    descripcion: typing.Optional[str] = None,
    color: typing.Optional[str] = None, # Formato Hexadecimal, ej: #FF0000 o #010101
    autor: typing.Optional[str] = None,
    imagen_autor: typing.Optional[str] = None,
    imagen_principal: typing.Optional[str] = None,
    imagen_derecha: typing.Optional[str] = None, # Thumbnail
    pie_de_pagina: typing.Optional[str] = None,
    imagen_pie: typing.Optional[str] = None
):
    # Verificación por si el usuario ejecuta el comando sin enviar ningún dato
    if not any([titulo, descripcion, color, autor, imagen_autor, imagen_principal, imagen_derecha, pie_de_pagina, imagen_pie]):
        return await ctx.send("> Debes rellenar al menos una de las opciones para crear un embed.", ephemeral=True)

    # 1. Configurar Color (Si no pone, se usa el gris por defecto de Discord)
    embed_color = discord.Color.default()
    if color:
        try:
            embed_color = discord.Color.from_str(color)
        except ValueError:
            return await ctx.send("> El formato de color no es válido. Usa un código Hex (Ej: `#FF0000` o `#010101`).", ephemeral=True)

    # 2. Inicializar Embed con Título, Descripción y Color
    embed = discord.Embed(
        title=titulo,
        description=descripcion,
        color=embed_color
    )

    # 3. Configurar Autor e Imagen de Autor
    if autor:
        # Si pone autor pero no imagen, solo se aplica el texto
        embed.set_author(name=autor, icon_url=imagen_autor)
    elif imagen_autor:
        # Si puso url de imagen de autor pero olvidó el texto, Discord exige texto para mostrar el icono
        embed.set_author(name="Autor", icon_url=imagen_autor)

    # 4. Configurar Imagen de arriba a la derecha (Thumbnail)
    if imagen_derecha:
        embed.set_thumbnail(url=imagen_derecha)

    # 5. Configurar Imagen Principal (Abajo en grande)
    if imagen_principal:
        embed.set_image(url=imagen_principal)

    # 6. Configurar Pie de página (Footer) e Imagen de pie de página
    if pie_de_pagina:
        embed.set_footer(text=pie_de_pagina, icon_url=imagen_pie)
    elif imagen_pie:
        # Discord exige texto en el footer para poder renderizar su icono
        embed.set_footer(text=" ", icon_url=imagen_pie)

    # Enviar el embed terminado
    await ctx.send(embed=embed)

# =========================================================
# SET NIVELES / WLC / BYE
# =========================================================

@bot.tree.command(name="set-niveles", description="Elige el canal donde se anuncian los niveles")
@app_commands.checks.has_permissions(administrator=True)
async def set_niveles_slash(i: discord.Interaction, canal: discord.TextChannel):
    nivel_canal[i.guild.id] = canal.id
    await i.response.send_message(f"> Canal de niveles seteado en {canal.mention}", ephemeral=True)

@bot.command(name="set-niveles")
@commands.has_permissions(administrator=True)
async def set_niveles_prefix(ctx, canal: discord.TextChannel):
    nivel_canal[ctx.guild.id] = canal.id
    await ctx.send(f"> Canal de niveles seteado en {canal.mention}")

@bot.tree.command(name="wlc", description="Activa el mensaje de bienvenida")
@app_commands.checks.has_permissions(administrator=True)
async def wlc_slash(i: discord.Interaction, canal: discord.TextChannel):
    wlc_canal[i.guild.id] = canal.id
    await i.response.send_message(f"> Bienvenida activada en {canal.mention}", ephemeral=True)

@bot.command(name="wlc")
@commands.has_permissions(administrator=True)
async def wlc_prefix(ctx, canal: discord.TextChannel):
    wlc_canal[ctx.guild.id] = canal.id
    await ctx.send(f"> Bienvenida activada en {canal.mention}")

@bot.tree.command(name="bye", description="Activa el mensaje de despedida")
@app_commands.checks.has_permissions(administrator=True)
async def bye_slash(i: discord.Interaction, canal: discord.TextChannel):
    bye_canal[i.guild.id] = canal.id
    await i.response.send_message(f"> Despedida activada en {canal.mention}", ephemeral=True)

@bot.command(name="bye")
@commands.has_permissions(administrator=True)
async def bye_prefix(ctx, canal: discord.TextChannel):
    bye_canal[ctx.guild.id] = canal.id
    await ctx.send(f"> Despedida activada en {canal.mention}")

@bot.tree.command(name="reset-wlc")
@app_commands.checks.has_permissions(administrator=True)
async def reset_wlc_slash(i: discord.Interaction):
    wlc_canal.pop(i.guild.id, None)
    await i.response.send_message("> Bienvenida desactivada", ephemeral=True)

@bot.tree.command(name="reset-bye")
@app_commands.checks.has_permissions(administrator=True)
async def reset_bye_slash(i: discord.Interaction):
    bye_canal.pop(i.guild.id, None)
    await i.response.send_message("> Despedida desactivada", ephemeral=True)

# =========================================================
# ASK IA
# =========================================================

@bot.tree.command(name="ask")
async def ask_slash(i: discord.Interaction, mensaje: str):
    await i.response.defer()
    try:
        if any(p in mensaje.lower() for p in ["imagen", "foto", "dibujo", "genera", "wallpaper"]):
            image_url = f"https://image.pollinations.ai/prompt/{mensaje.replace(' ', '%20')}"
            embed = discord.Embed(title="Imagen generada", description=f"> Prompt: {mensaje}", color=0x000000)
            embed.set_image(url=image_url)
            await i.followup.send(embed=embed)
            return
        respuesta = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Eres una IA amigable, divertida y algo sarcastica, tu nombre es Daylight."}, {"role": "user", "content": mensaje}]
        )
        texto = respuesta.choices[0].message.content
        embed = discord.Embed(color=0x000000)
        embed.description = f"### Emisor\n> {mensaje}\n\n### Receptor\n> {texto}"
        await i.followup.send(embed=embed)
    except Exception as e:
        await i.followup.send(f"Error:\n```{e}```")

@bot.command(name="ask")
async def ask_prefix(ctx, *, mensaje: str):
    try:
        respuesta = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Eres una IA amigable, divertida y algo sarcastica, tu nombre es Daylight."}, {"role": "user", "content": mensaje}]
        )
        texto = respuesta.choices[0].message.content
        embed = discord.Embed(color=0x000000)
        embed.description = f"### Emisor\n> {mensaje}\n\n### Receptor\n> {texto}"
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error:\n```{e}```")

# =========================================================
# ON MESSAGE
# =========================================================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # QUITAR AFK
    if message.author.id in afk_data:
        tiempo_inicio = afk_data[message.author.id]["tiempo"]
        segundos_totales = int(time.time() - tiempo_inicio)
        m, s = divmod(segundos_totales, 60)
        h, m = divmod(m, 60)
        tiempo_texto = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s" if m > 0 else f"{s}s"
        await message.channel.send(f"**Bienvenido de nuevo {message.author.name}**\n> estuviste `{tiempo_texto}` inactivo")
        del afk_data[message.author.id]

    # AVISAR MENCIONES AFK
    for user in message.mentions:
        if user.id in afk_data and user.id != message.author.id:
            await message.channel.send(f"**{user.name}** esta dormido...\n> Motivo: `{afk_data[user.id]['motivo']}`")

    await bot.process_commands(message)

    # MONEDAS CADA 5 MENSAJES
    if message.guild:
        uid = str(message.author.id)
        if uid not in mensaje_count:
            mensaje_count[uid] = 0
        mensaje_count[uid] += 1
        if mensaje_count[uid] >= 5:
            mensaje_count[uid] = 0
            data = get_user_eco(str(message.guild.id), message.author.id)
            data["coins"] += random.randint(2, 4)

    # RESPONDER SI LE RESPONDEN AL BOT
    if not message.reference:
        return

    try:
        replied = await message.channel.fetch_message(message.reference.message_id)
        if replied.author.id != bot.user.id:
            return
        mensaje_original = replied.content
        if replied.embeds and replied.embeds[0].description:
            mensaje_original = replied.embeds[0].description
        system_prompt = f"Tu nombre SIEMPRE es Daylight. Eres un bot de Discord divertido y sarcastico. El usuario se llama {message.author.display_name} y estas en {message.guild.name}."
        respuesta = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}, {"role": "assistant", "content": mensaje_original}, {"role": "user", "content": message.content}]
        )
        texto = respuesta.choices[0].message.content
        embed = discord.Embed(color=0x000000)
        embed.description = f"### Emisor\n> {message.content}\n\n### Receptor\n> {texto}"
        await message.reply(embed=embed, mention_author=False)
    except:
        pass

# =========================================================
# EVENTOS JOIN / REMOVE
# =========================================================

@bot.event
async def on_member_join(member):
    if member.bot:
        return
    canal_id = wlc_canal.get(member.guild.id)
    if not canal_id:
        return
    canal = member.guild.get_channel(canal_id)
    if not canal:
        return
    embed = discord.Embed(
        title=f"-            Welc_ome_ {member.name}      ୨୧",
        description=(
            f"˙ ∘ ⊹ Bienvenido nuevo ~{member.mention}~ <:emoji_17:1494897832803700847>\n\n"
            f"12 edad _Minima_ ♱ 18 edad _Maxima_ ∘ ˙ (🦢)\n\n"
            f"[Book](https://0.com) | [Lobby](https://0.com) | [General](https://0.com)    ⌗"
        ),
        color=0xFFFFFF
    )
    embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    await canal.send(embed=embed)

@bot.event
async def on_member_remove(member):
    if member.bot:
        return
    canal_id = bye_canal.get(member.guild.id)
    if not canal_id:
        return
    canal = member.guild.get_channel(canal_id)
    if not canal:
        return
    embed = discord.Embed(
        title=f"-            God_bye_ {member.name}      ୨୧",
        description=(
            f"˙ ∘ ⊹ Hasta nunca maldito ~{member.name}~ <:emoji_26:1494897832803700847>\n\n"
            f"12 edad _Minima_ ♱ 18 edad _Maxima_ ∘ ˙ (🦢)\n\n"
            f"[Book](https://0.com) | [Lobby](https://0.com) | [General](https://0.com)    ⌗"
        ),
        color=0xFFFFFF
    )
    embed.set_footer(text=member.display_name, icon_url=member.display_avatar.url)
    await canal.send(embed=embed)

# =========================================================
# DAR XP
# =========================================================

@bot.listen("on_message")
async def dar_xp(message):
    if message.author.bot or not message.guild:
        return
    uid = message.author.id
    ahora = time.time()
    if ahora - xp_cooldown.get(uid, 0) < 120:
        return
    xp_cooldown[uid] = ahora
    data = get_xp(message.guild.id, uid)
    data["xp"] += random.randint(10, 20)
    xp_needed = xp_para_nivel(data["level"])
    if data["xp"] >= xp_needed:
        data["xp"] -= xp_needed
        data["level"] += 1
        canal_id = nivel_canal.get(message.guild.id)
        canal = message.guild.get_channel(canal_id) if canal_id else message.channel
        try:
            await canal.send(content=message.author.mention, file=await generar_nivel(message.author, data["level"], data["xp"], xp_para_nivel(data["level"])))
        except Exception as e:
            print(f"Error nivel: {e}")

# =========================================================
# MANEJO DE ERRORES GLOBAL
# =========================================================
@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    
    embed = discord.Embed(
        title="Error",
        description=f"```{str(error)}```",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed, delete_after=10)
    logger.error(f"> Error en comando: {error}")
            
# =========================================================
# GENERAR TARJETA SHIP
# =========================================================

async def generar_ship(usuario1: discord.Member, usuario2: discord.Member, porcentaje: int) -> discord.File:
    W, H     = 680, 200
    FONDO    = (14, 14, 14)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    # COLOR SIEMPRE ROSA
    COLOR = (255, 92, 147)    # rosa fuerte

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA LATERAL
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=COLOR)

    # AVATAR USUARIO 1
    try:
        av1 = await descargar_imagen(str(usuario1.display_avatar.url))
        av1 = avatar_circular(av1, 110)
        img.paste(av1, (30, 45), av1)
    except:
        draw.ellipse([(30, 45), (140, 155)], fill=GRIS)
    draw.ellipse([(28, 43), (142, 157)], outline=COLOR, width=2)

    # AVATAR USUARIO 2
    try:
        av2 = await descargar_imagen(str(usuario2.display_avatar.url))
        av2 = avatar_circular(av2, 110)
        img.paste(av2, (540, 45), av2)
    except:
        draw.ellipse([(540, 45), (650, 155)], fill=GRIS)
    draw.ellipse([(538, 43), (652, 157)], outline=COLOR, width=2)

    # NOMBRES
    nombre1 = usuario1.display_name[:14] + "..." if len(usuario1.display_name) > 14 else usuario1.display_name
    nombre2 = usuario2.display_name[:14] + "..." if len(usuario2.display_name) > 14 else usuario2.display_name
    draw.text((85, 162), nombre1, font=fuente(13, bold=True), fill=TEXTO, anchor="mt")
    draw.text((595, 162), nombre2, font=fuente(13, bold=True), fill=TEXTO, anchor="mt")

    # BARRA CORAZON CENTRAL
    draw.rounded_rectangle([(160, 82), (520, 118)], radius=18, fill=GRIS)
    fill_w = int(160 + (360 * porcentaje / 100))
    if fill_w > 160:
        draw.rounded_rectangle([(160, 82), (fill_w, 118)], radius=18, fill=COLOR)

    # PORCENTAJE
    draw.text((340, 100), f"{porcentaje}%", font=fuente(20, bold=True), fill=TEXTO, anchor="mm")

    # FRASE
    if porcentaje >= 90:
        frase = "Almas gemelas de otra dimension"
    elif porcentaje >= 75:
        frase = "El amor es inevitable entre estos dos"
    elif porcentaje >= 60:
        frase = "Hay chispa, pero falta avivarlo"
    elif porcentaje >= 40:
        frase = "Podria funcionar... o no"
    elif porcentaje >= 20:
        frase = "Mejor como amigos"
    else:
        frase = "Incompatibles al maximo nivel"

    draw.text((340, 140), frase, font=fuente(12), fill=SUBTEXTO, anchor="mt")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ship.png")
    
# =========================================================
# COMANDO SHIP
# =========================================================

@bot.tree.command(name="ship", description="Calcula la compatibilidad entre dos usuarios")
async def ship_slash(i: discord.Interaction, usuario1: discord.Member, usuario2: discord.Member):
    await i.response.defer()

    # PORCENTAJE CONSISTENTE BASADO EN IDS
    seed = (usuario1.id + usuario2.id) % 101
    random.seed(seed)
    porcentaje = random.randint(0, 100)
    random.seed()

    archivo = await generar_ship(usuario1, usuario2, porcentaje)
    await i.followup.send(file=archivo)


@bot.command(name="ship")
async def ship_prefix(ctx, usuario1: discord.Member, usuario2: discord.Member):
    seed = (usuario1.id + usuario2.id) % 101
    random.seed(seed)
    porcentaje = random.randint(0, 100)
    random.seed()

    archivo = await generar_ship(usuario1, usuario2, porcentaje)
    await ctx.send(file=archivo)

# =========================================================
# CONFIGURACIÓN INICIAL DEL BOT
# =========================================================

intents = discord.Intents.default()
intents.message_content = True  # Necesario para los comandos con prefijo

# Puedes cambiar el prefijo "!" por el que uses en tu bot
bot = commands.Bot(command_prefix=">dl ", intents=intents)
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# =========================================================
# FUNCIONES AUXILIARES PARA PROCESAR IMÁGENES (PILLOW)
# =========================================================

async def descargar_imagen(url: str) -> Image.Image:
    """Descarga de forma asíncrona el avatar del usuario."""
    if not url:
        raise ValueError("La URL del avatar está vacía.")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                bytes_img = await resp.read()
                return Image.open(io.BytesIO(bytes_img)).convert("RGBA")
            raise Exception(f"No se pudo descargar el avatar. Status: {resp.status}")

def avatar_circular(img_avatar: Image.Image, size: int) -> Image.Image:
    """Recorta el avatar descargado en un círculo perfecto."""
    img_avatar = img_avatar.resize((size, size), Image.Resampling.LANCZOS)
    mascara = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mascara)
    draw.ellipse((0, 0, size, size), fill=255)
    
    resultado = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    resultado.paste(img_avatar, (0, 0), mask=mascara)
    return resultado

def fuente(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Intenta cargar Arial o una fuente por defecto si no existe en el sistema."""
    try:
        # Render corre en Linux, por lo que usualmente no tiene fuentes de Windows.
        # Si tienes un archivo .ttf en tu carpeta, pon su nombre aquí, ej: "font.ttf"
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()

# =========================================================
# GENERAR TARJETA TIKTOK (PILLOW)
# =========================================================

async def generar_tiktok(datos: dict) -> discord.File:
    W, H     = 680, 200
    FONDO    = (14, 14, 14)
    ROSA     = (255, 0, 80)
    CIAN     = (0, 242, 234)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA LATERAL DEGRADADO TIKTOK (rosa y cian)
    draw.rectangle([(0, 0), (6, H // 2)], fill=ROSA)
    draw.rectangle([(0, H // 2), (6, H)], fill=CIAN)

    # AVATAR
    try:
        av = await descargar_imagen(datos["avatar"])
        av = avatar_circular(av, 100)
        img.paste(av, (24, 50), av)
    except:
        draw.ellipse([(24, 50), (124, 150)], fill=GRIS)

    # BORDE AVATAR TIKTOK
    draw.ellipse([(22, 48), (126, 152)], outline=ROSA, width=2)
    draw.ellipse([(19, 45), (129, 155)], outline=CIAN, width=1)

    # NOMBRE Y USERNAME
    draw.text((144, 52), datos["nickname"], font=fuente(20, bold=True), fill=TEXTO)
    draw.text((144, 78), f"@{datos['username']}", font=fuente(13), fill=SUBTEXTO)

    # SEPARADOR
    draw.rectangle([(144, 106), (645, 107)], fill=GRIS)

    # STATS EN 3 COLUMNAS
    stats = [
        ("Seguidores", datos["followers"]),
        ("Siguiendo", datos["following"]),
        ("Likes",     datos["likes"]),
    ]

    col_x = [144, 310, 476]
    for n, (label, valor) in enumerate(stats):
        x = col_x[n]
        draw.text((x, 118), label, font=fuente(11), fill=SUBTEXTO)
        draw.text((x, 136), str(valor), font=fuente(17, bold=True), fill=TEXTO)

    # VIDEOS
    draw.text((144, 168), f"Videos: {datos['videos']}", font=fuente(12), fill=SUBTEXTO)

    # VERIFICADO
    if datos.get("verified"):
        draw.text((400, 168), "Cuenta verificada", font=fuente(12), fill=CIAN)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="tiktok.png")

# =========================================================
# COMANDO TIKTOK (SLASH Y PREFIJO)
# =========================================================

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Función interna compartida para formatear números de la API (Ej: 1500 -> 1.5K)
def fmt_tiktok_stats(n):
    try:
        n = int(n)
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)
    except:
        return "0"

@bot.tree.command(name="tiktok", description="Ver info de un perfil de TikTok")
async def tiktok_slash(i: discord.Interaction, usuario: str):
    await i.response.defer()
    try:
        url = "https://scraptik.p.rapidapi.com/get-user"
        headers = {
            "X-RapidAPI-Key":  RAPIDAPI_KEY,
            "X-RapidAPI-Host": "scraptik.p.rapidapi.com"
        }
        params = {"username": usuario.replace("@", "")}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as r:
                data = await r.json()

        user = data.get("user_info", {}).get("user", {})
        stats = data.get("user_info", {}).get("stats", {})

        if not user:
            await i.followup.send("> No se encontró ese usuario.", ephemeral=True)
            return

        datos = {
            "nickname":  user.get("nickname", usuario),
            "username":  user.get("uniqueId", usuario),
            "avatar":    user.get("avatarLarger", ""),
            "followers": fmt_tiktok_stats(stats.get("followerCount", 0)),
            "following": fmt_tiktok_stats(stats.get("followingCount", 0)),
            "likes":     fmt_tiktok_stats(stats.get("heartCount", 0)),
            "videos":    fmt_tiktok_stats(stats.get("videoCount", 0)),
            "verified":  user.get("verified", False)
        }

        archivo = await generar_tiktok(datos)
        await i.followup.send(file=archivo)

    except Exception as e:
        await i.followup.send(f"Error:\n```{e}```", ephemeral=True)


@bot.command(name="tiktok")
async def tiktok_prefix(ctx, *, usuario: str):
    async with ctx.typing():
        try:
            url = "https://scraptik.p.rapidapi.com/get-user"
            headers = {
                "X-RapidAPI-Key":  RAPIDAPI_KEY,
                "X-RapidAPI-Host": "scraptik.p.rapidapi.com"
            }
            params = {"username": usuario.replace("@", "")}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as r:
                    data = await r.json()

            user  = data.get("user_info", {}).get("user", {})
            stats = data.get("user_info", {}).get("stats", {})

            if not user:
                await ctx.send("> No se encontró ese usuario.")
                return

            datos = {
                "nickname":  user.get("nickname", usuario),
                "username":  user.get("uniqueId", usuario),
                "avatar":    user.get("avatarLarger", ""),
                "followers": fmt_tiktok_stats(stats.get("followerCount", 0)),
                "following": fmt_tiktok_stats(stats.get("followingCount", 0)),
                "likes":     fmt_tiktok_stats(stats.get("heartCount", 0)),
                "videos":    fmt_tiktok_stats(stats.get("videoCount", 0)),
                "verified":  user.get("verified", False)
            }

            archivo = await generar_tiktok(datos)
            await ctx.send(file=archivo)

        except Exception as e:
            await ctx.send(f"Error:\n```{e}```")
        if ctx.interaction:
            await ctx.interaction.followup.send(msg_err, ephemeral=True)
        else:
            await ctx.send(msg_err)

# ---------------------------
# ROBLOX
# ---------------------------

import aiohttp
import discord
from discord.ext import commands
from datetime import datetime

@bot.hybrid_command(
    name="roblox", 
    description="Mira el perfil de roblox de alguien"
)
async def roblox(ctx: commands.Context, usuario: str):
    # Asegura que el bot no se quede congelado esperando la respuesta de Roblox
    await ctx.defer() if ctx.interaction else None

    async with aiohttp.ClientSession() as session:
        # 1. Obtener el ID del usuario y su nombre real
        data_user = {"usernames": [usuario], "excludeBannedUsers": False}
        async with session.post("https://users.roblox.com/v1/usernames/users", json=data_user) as resp:
            if resp.status != 200:
                return await ctx.send("> Error al conectar con la API de Roblox.")
            
            res_user = await resp.json()
            if not res_user["data"]:
                return await ctx.send(f"> El usuario **{usuario}** no existe en Roblox.")
            
            user_info = res_user["data"][0]
            user_id = user_info["id"]
            roblox_user = user_info["displayName"] # Nombre visible

        # 2. Obtener fecha de creación (y si está baneado)
        async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as resp:
            res_details = await resp.json()
            # Formateamos la fecha (Ej: 25 Jan 2018)
            fecha_iso = res_details["created"].split("T")[0]
            fecha_obj = datetime.strptime(fecha_iso, "%Y-%m-%d")
            cuenta_creada = fecha_obj.strftime("%d/%m/%Y")

        # 3. Obtener cantidad de amigos
        async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count") as resp:
            res_friends = await resp.json()
            cantidad_amigos = res_friends.get("count", 0)

        # 4. Obtener el avatar completo (Cuerpo entero, tamaño grande 720x720)
        avatar_url = "https://images.rbxcdn.com/default_avatar.png" # Por si falla
        async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false") as resp:
            if resp.status == 200:
                res_thumb = await resp.json()
                if res_thumb["data"]:
                    avatar_url = res_thumb["data"][0]["imageUrl"]

    # Link al perfil real
    perfil_link = f"https://www.roblox.com/users/{user_id}/profile"

    # Creamos el Embed exactamente como lo querías
    embed = discord.Embed(
        description=(
            f"> **User:** {roblox_user}\n"
            f"> **Creada:** {cuenta_creada}\n"
            f"> **Amigos:** {cantidad_amigos}\n"
            f"> **Link:** [Visitar Perfil]({perfil_link})"
        ),
        color=discord.Color.from_str("#010101")
    )
    
    # Coloca el render del cuerpo completo abajo
    embed.set_image(url=avatar_url)

    # Si fue comando slash usa reply, si fue prefijo usa send de forma automática
    if ctx.interaction:
        await ctx.interaction.followup.send(embed=embed)
    else:
        await ctx.send(embed=embed)
# -------------------------
# FLASK WEB
# -------------------------

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot activo"

def run_web():
    flask_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

# -------------------------
# RUN
# -------------------------

bot.run(TOKEN)
