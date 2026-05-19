import discord
import os
import io
from datetime import datetime
import asyncio
import random
import json
import time
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from groq import AsyncGroq
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading

# -------------------------
# CLIENTES
# -------------------------

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
TOKEN        = os.getenv("TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# -------------------------
# COLOR GLOBAL
# -------------------------

ROSA = (255, 105, 180)

# -------------------------
# DATA
# -------------------------

warnings_data = {}
afk_data      = {}
mensaje_count = {}
welc_config   = {}
bye_config    = {}
xp_data       = {}
nivel_canal   = {}
xp_cooldown   = {}
economia_data = {}
claves_data   = {}

# -------------------------
# BOT
# -------------------------

class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=">mt ", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

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
    gid, uid = str(guild_id), str(user_id)
    if gid not in xp_data: xp_data[gid] = {}
    if uid not in xp_data[gid]: xp_data[gid][uid] = {"xp": 0, "level": 1}
    return xp_data[gid][uid]

def xp_para_nivel(nivel): return nivel * 100

def get_user_eco(guild_id, user_id):
    gid, uid = str(guild_id), str(user_id)
    if gid not in economia_data: economia_data[gid] = {}
    if uid not in economia_data[gid]: economia_data[gid][uid] = {"coins": 0, "last_daily": 0}
    return economia_data[gid][uid]

def get_user_claves(guild_id, user_id):
    gid, uid = str(guild_id), str(user_id)
    if gid not in claves_data: claves_data[gid] = {}
    if uid not in claves_data[gid]: claves_data[gid][uid] = {}
    return claves_data[gid][uid]

def parse_text(texto, member):
    if not texto:
        return ""
    return texto.replace("{user_name}", member.name) \
                .replace("{user_mention}", member.mention) \
                .replace("{user_id}", str(member.id)) \
                .replace("{server_name}", member.guild.name) \
                .replace("{user_avatar}", str(member.display_avatar.url))

async def get_member_from_ctx(ctx, usuario=None):
    if usuario:
        return usuario
    if ctx.message.reference:
        try:
            replied = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ctx.guild.get_member(replied.author.id)
            if member:
                return member
        except:
            pass
    return ctx.author

# =========================================================
# GENERADORES DE TARJETAS
# =========================================================

async def generar_userinfo(usuario: discord.Member) -> discord.File:
    W, H        = 700, 280
    FONDO       = (10, 10, 10)
    TEXTO       = (255, 255, 255)
    SUBTEXTO    = (160, 163, 172)
    CAMPO_FONDO = (20, 20, 20)
    CAMPO_BORDE = (50, 50, 60)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    for i_grad in range(60):
        alpha = int(80 * (1 - i_grad / 60))
        overlay = Image.new("RGBA", (W, 1), (*ROSA, alpha))
        img.paste(overlay, (0, i_grad), overlay)

    draw.rectangle([(0, 0), (5, H)], fill=ROSA)

    av_x, av_y = 28, 20
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 90)
        img.paste(av, (av_x, av_y), av)
    except:
        draw.ellipse([(av_x, av_y), (av_x + 90, av_y + 90)], fill=CAMPO_FONDO)

    draw.ellipse([(av_x - 3, av_y - 3), (av_x + 93, av_y + 93)], outline=ROSA, width=3)
    draw.ellipse([(av_x + 66, av_y + 66), (av_x + 84, av_y + 84)], fill=FONDO)
    draw.ellipse([(av_x + 68, av_y + 68), (av_x + 82, av_y + 82)], fill=(35, 165, 90))

    draw.text((136, 28), usuario.display_name, font=fuente(24, bold=True), fill=TEXTO)
    draw.text((136, 58), f"@{usuario.name}", font=fuente(13), fill=SUBTEXTO)

    draw.rectangle([(24, 128), (W - 24, 129)], fill=ROSA)

    def campo(x, y, titulo, valor, ancho=310):
        draw.rounded_rectangle([(x, y), (x + ancho, y + 62)], radius=10, fill=CAMPO_FONDO)
        draw.rounded_rectangle([(x, y), (x + ancho, y + 62)], radius=10, outline=CAMPO_BORDE, width=1)
        draw.rounded_rectangle([(x, y + 8), (x + 3, y + 54)], radius=2, fill=ROSA)
        draw.text((x + 14, y + 10), titulo, font=fuente(11), fill=SUBTEXTO)
        draw.text((x + 14, y + 32), valor, font=fuente(15, bold=True), fill=TEXTO)

    campo(24,  144, "USUARIO",         f"@{usuario.display_name}")
    campo(356, 144, "ID",              str(usuario.id))
    creado = usuario.created_at.strftime("%d/%m/%Y")
    entro  = usuario.joined_at.strftime("%d/%m/%Y") if usuario.joined_at else "?"
    campo(24,  218, "CUENTA CREADA",   creado)
    campo(356, 218, "ENTRO AL SERVER", entro)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="userinfo.png")


async def generar_serverinfo(guild: discord.Guild, solicitante: discord.Member) -> discord.File:
    W, H        = 700, 400
    FONDO       = (10, 10, 10)
    TEXTO       = (255, 255, 255)
    SUBTEXTO    = (160, 163, 172)
    CAMPO_FONDO = (20, 20, 20)
    CAMPO_BORDE = (50, 50, 60)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (6, H)], fill=ROSA)

    if guild.icon:
        icon_img = await descargar_imagen(str(guild.icon.url))
        icon_img = avatar_circular(icon_img, 90)
        img.paste(icon_img, (24, 20), icon_img)
        nombre_x = 128
    else:
        nombre_x = 24

    draw.ellipse([(22, 18), (116, 112)], outline=ROSA, width=2)
    draw.text((nombre_x, 22), guild.name, font=fuente(26, bold=True), fill=TEXTO)
    draw.text((nombre_x, 56), f"ID: {guild.id}", font=fuente(14), fill=SUBTEXTO)
    draw.rectangle([(24, 126), (W - 24, 127)], fill=ROSA)

    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, fill=CAMPO_FONDO)
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, outline=CAMPO_BORDE, width=1)
        draw.rounded_rectangle([(x, y + 8), (x + 3, y + 56)], radius=2, fill=ROSA)
        draw.text((x + 12, y + 8), titulo, font=fuente(13), fill=SUBTEXTO)
        draw.text((x + 12, y + 30), str(valor), font=fuente(17, bold=True), fill=TEXTO)

    y = 148
    campo(24, y, "OWNER", guild.owner.display_name if guild.owner else "?")
    campo(370, y, "CREADO", guild.created_at.strftime("%d/%m/%Y"))
    y2 = y + 80
    ancho3 = 204
    campo(24,       y2, "MIEMBROS", str(guild.member_count), ancho=ancho3)
    campo(24 + 224, y2, "ROLES",    str(len(guild.roles)),   ancho=ancho3)
    campo(24 + 448, y2, "EMOJIS",   str(len(guild.emojis)),  ancho=ancho3)
    y3 = y2 + 80
    campo(24,       y3, "TEXTO",  str(len(guild.text_channels)),  ancho=ancho3)
    campo(24 + 224, y3, "VOZ",    str(len(guild.voice_channels)), ancho=ancho3)
    campo(24 + 448, y3, "BOOSTS", f"{guild.premium_subscription_count} (nv {guild.premium_tier})", ancho=ancho3)

    draw.text((24, H - 22), f"Solicitado por {solicitante.display_name}", font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="serverinfo.png")


async def generar_nivel(usuario: discord.Member, nivel: int, xp: int, xp_needed: int) -> discord.File:
    W, H     = 680, 180
    FONDO    = (10, 10, 10)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (170, 170, 170)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ROSA)

    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 100)
        img.paste(av, (38, 40), av)
    except:
        draw.ellipse([(38, 40), (138, 140)], fill=GRIS)

    draw.ellipse([(36, 38), (140, 142)], outline=ROSA, width=2)
    draw.text((162, 28), usuario.display_name, font=fuente(21, bold=True), fill=TEXTO)
    draw.rounded_rectangle([(162, 62), (242, 84)], radius=11, fill=ROSA)
    draw.text((202, 68), f"Nivel {nivel}", font=fuente(12, bold=True), fill=FONDO, anchor="mt")
    draw.text((162, 100), f"{xp} / {xp_needed} XP", font=fuente(12), fill=SUBTEXTO)
    draw.rounded_rectangle([(162, 118), (630, 130)], radius=6, fill=GRIS)
    progreso = min(xp / xp_needed, 1.0)
    fill_w = int(162 + (468 * progreso))
    if fill_w > 162:
        draw.rounded_rectangle([(162, 118), (fill_w, 130)], radius=6, fill=ROSA)
    draw.text((162, 152), f"Subiste al nivel {nivel} — sigue asi!", font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="nivel.png")


async def generar_balance(usuario: discord.Member, coins: int, last_daily: float) -> discord.File:
    W, H     = 680, 170
    FONDO    = (10, 10, 10)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ROSA)

    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 37), av)
    except:
        draw.ellipse([(37, 37), (133, 133)], fill=GRIS)

    draw.ellipse([(35, 35), (135, 135)], outline=ROSA, width=2)
    draw.text((158, 48), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO)
    draw.rectangle([(158, 90), (640, 91)], fill=GRIS)
    draw.text((158, 106), f"$ {coins:,} monedas", font=fuente(22, bold=True), fill=ROSA)

    if last_daily == 0:
        daily_texto = "Nunca reclamaste tu daily"
    else:
        hace = int(time.time() - last_daily)
        if hace < 3600:    daily_texto = f"Ultimo daily: hace {hace // 60} minutos"
        elif hace < 86400: daily_texto = f"Ultimo daily: hace {hace // 3600} horas"
        else:              daily_texto = f"Ultimo daily: hace {hace // 86400} dias"

    draw.text((158, 148), daily_texto, font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="balance.png")


async def generar_ranking(guild: discord.Guild, top: list) -> discord.File:
    filas = len(top)
    W, H  = 680, 130 + (filas * 46)
    FONDO    = (10, 10, 10)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)
    OSCURO   = (15, 15, 15)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ROSA)
    draw.text((34, 30), "Ranking", font=fuente(18, bold=True), fill=TEXTO)
    draw.text((34, 58), "Top usuarios con mas monedas", font=fuente(11), fill=SUBTEXTO)
    draw.rectangle([(34, 72), (646, 73)], fill=GRIS)

    for n, (uid, data) in enumerate(top):
        member = guild.get_member(int(uid))
        nombre = member.display_name if member else f"Usuario {uid}"
        nombre = nombre[:20] + "..." if len(nombre) > 20 else nombre
        y = 82 + (n * 46)
        draw.rounded_rectangle([(34, y), (646, y + 36)], radius=8, fill=(26, 26, 26) if n == 0 else OSCURO)
        medalla = f"#{n+1}" if n >= 3 else str(n+1)
        draw.text((54, y + 10), medalla, font=fuente(14, bold=True), fill=ROSA if n == 0 else SUBTEXTO)
        draw.text((90, y + 10), nombre, font=fuente(13, bold=n == 0), fill=TEXTO)
        draw.text((620, y + 10), f"$ {data['coins']:,}", font=fuente(13), fill=ROSA if n == 0 else SUBTEXTO, anchor="ra")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ranking.png")


async def generar_ban(usuario: discord.Member, razon: str, moderador: discord.Member) -> discord.File:
    W, H     = 680, 190
    FONDO    = (10, 10, 10)
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
    FONDO    = (10, 10, 10)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ROSA)

    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 47), av)
    except:
        draw.ellipse([(37, 47), (133, 143)], fill=GRIS)

    draw.ellipse([(35, 45), (135, 145)], outline=ROSA, width=2)
    draw.text((98, 72), "z", font=fuente(17, bold=True), fill=ROSA)
    draw.text((110, 58), "z", font=fuente(14, bold=True), fill=ROSA)
    draw.text((120, 46), "z", font=fuente(11), fill=ROSA)
    draw.text((158, 42), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO)
    draw.rounded_rectangle([(158, 68), (218, 90)], radius=11, fill=ROSA)
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
    FONDO    = (10, 10, 10)
    VERDE    = (29, 185, 84)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ROSA)

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

    draw.rounded_rectangle([(29, 24), (161, 156)], radius=10, outline=ROSA, width=2)
    draw.text((182, 28), f"{usuario.display_name} esta escuchando", font=fuente(13), fill=SUBTEXTO)
    cancion = actividad.title[:30] + "..." if len(actividad.title) > 30 else actividad.title
    draw.text((182, 50), cancion, font=fuente(20, bold=True), fill=TEXTO)
    draw.text((182, 78), actividad.artist, font=fuente(14), fill=ROSA)
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
        draw.rounded_rectangle([(182, 128), (fill_w, 136)], radius=4, fill=ROSA)

    fmt = lambda s: f"{int(s) // 60}:{int(s) % 60:02}"
    draw.text((182, 148), fmt(max(transcurrido, 0)), font=fuente(11), fill=SUBTEXTO)
    draw.text((645, 148), fmt(duracion), font=fuente(11), fill=SUBTEXTO, anchor="ra")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="spotify.png")


async def generar_warn(usuario: discord.Member, razon: str, total: int) -> discord.File:
    W, H     = 680, 180
    FONDO    = (10, 10, 10)
    AMARILLO = (245, 158, 11)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AMARILLO)
    draw.polygon([(80, 22), (138, 122), (22, 122)], fill=AMARILLO)
    draw.rounded_rectangle([(75, 44), (85, 90)], radius=5, fill=FONDO)
    draw.ellipse([(74, 102), (86, 114)], fill=FONDO)
    draw.text((162, 28), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO)
    draw.rounded_rectangle([(162, 56), (252, 78)], radius=11, fill=AMARILLO)
    draw.text((207, 62), "Advertido", font=fuente(12, bold=True), fill=FONDO, anchor="mt")
    draw.rectangle([(162, 92), (645, 93)], fill=GRIS)
    draw.text((162, 104), "RAZON", font=fuente(11), fill=SUBTEXTO)
    razon_texto = razon[:50] + "..." if len(razon) > 50 else razon
    draw.text((162, 122), razon_texto, font=fuente(15, bold=True), fill=TEXTO)
    draw.text((162, 154), f"Total de warns: {total}", font=fuente(12), fill=AMARILLO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="warn.png")


async def generar_warnings(usuario: discord.Member, warns: list) -> discord.File:
    filas = min(len(warns), 10)
    W, H  = 680, 90 + (filas * 44)
    FONDO    = (10, 10, 10)
    AMARILLO = (245, 158, 11)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)
    OSCURO   = (15, 15, 15)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AMARILLO)
    draw.text((34, 24), f"Warns de {usuario.display_name}", font=fuente(18, bold=True), fill=TEXTO)
    draw.rectangle([(34, 44), (646, 45)], fill=GRIS)

    for n, w in enumerate(warns[:10]):
        y = 54 + (n * 44)
        draw.rounded_rectangle([(34, y), (646, y + 34)], radius=8, fill=(26, 26, 26) if n % 2 == 0 else OSCURO)
        draw.text((54, y + 8), f"#{n+1}", font=fuente(13, bold=True), fill=AMARILLO)
        razon = w["razon"][:40] + "..." if len(w["razon"]) > 40 else w["razon"]
        draw.text((88, y + 10), razon, font=fuente(13), fill=TEXTO)
        mod = w["moderador"][:20] + "..." if len(w["moderador"]) > 20 else w["moderador"]
        draw.text((634, y + 10), mod, font=fuente(11), fill=SUBTEXTO, anchor="ra")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="warnings.png")


async def generar_lock(canal: discord.TextChannel, bloqueado: bool) -> discord.File:
    W, H     = 680, 170
    FONDO    = (10, 10, 10)
    COLOR    = (239, 68, 68) if bloqueado else (34, 197, 94)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=COLOR)
    draw.rounded_rectangle([(44, 88), (116, 144)], radius=8, fill=COLOR)

    if bloqueado:
        draw.arc([(56, 42), (104, 98)], start=180, end=0, fill=COLOR, width=10)
    else:
        draw.arc([(68, 30), (116, 86)], start=180, end=360, fill=COLOR, width=10)

    draw.ellipse([(71, 103), (89, 121)], fill=FONDO)
    draw.rounded_rectangle([(76, 112), (84, 126)], radius=3, fill=FONDO)
    titulo = "Canal Bloqueado" if bloqueado else "Canal Desbloqueado"
    draw.text((144, 32), titulo, font=fuente(22, bold=True), fill=TEXTO)
    draw.rectangle([(144, 62), (654, 63)], fill=GRIS)
    draw.text((144, 76), "CANAL", font=fuente(12), fill=SUBTEXTO)
    draw.text((144, 96), f"# {canal.name}", font=fuente(15, bold=True), fill=TEXTO)
    msg = "Nadie puede enviar mensajes." if bloqueado else "Ya pueden enviar mensajes."
    draw.text((144, 136), msg, font=fuente(13), fill=COLOR)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="lock.png")


async def generar_ship(usuario1: discord.Member, usuario2: discord.Member, porcentaje: int) -> discord.File:
    W, H     = 680, 200
    FONDO    = (10, 10, 10)
    COLOR    = (255, 92, 147)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=COLOR)

    try:
        av1 = await descargar_imagen(str(usuario1.display_avatar.url))
        av1 = avatar_circular(av1, 110)
        img.paste(av1, (30, 45), av1)
    except:
        draw.ellipse([(30, 45), (140, 155)], fill=GRIS)
    draw.ellipse([(28, 43), (142, 157)], outline=COLOR, width=2)

    try:
        av2 = await descargar_imagen(str(usuario2.display_avatar.url))
        av2 = avatar_circular(av2, 110)
        img.paste(av2, (540, 45), av2)
    except:
        draw.ellipse([(540, 45), (650, 155)], fill=GRIS)
    draw.ellipse([(538, 43), (652, 157)], outline=COLOR, width=2)

    nombre1 = usuario1.display_name[:14] + "..." if len(usuario1.display_name) > 14 else usuario1.display_name
    nombre2 = usuario2.display_name[:14] + "..." if len(usuario2.display_name) > 14 else usuario2.display_name
    draw.text((85, 162), nombre1, font=fuente(13, bold=True), fill=TEXTO, anchor="mt")
    draw.text((595, 162), nombre2, font=fuente(13, bold=True), fill=TEXTO, anchor="mt")

    draw.rounded_rectangle([(160, 82), (520, 118)], radius=18, fill=GRIS)
    fill_w = int(160 + (360 * porcentaje / 100))
    if fill_w > 160:
        draw.rounded_rectangle([(160, 82), (fill_w, 118)], radius=18, fill=COLOR)

    draw.text((340, 100), f"{porcentaje}%", font=fuente(20, bold=True), fill=TEXTO, anchor="mm")

    if porcentaje >= 90:   frase = "Almas gemelas de otra dimension"
    elif porcentaje >= 75: frase = "El amor es inevitable entre estos dos"
    elif porcentaje >= 60: frase = "Hay chispa, pero falta avivarlo"
    elif porcentaje >= 40: frase = "Podria funcionar... o no"
    elif porcentaje >= 20: frase = "Mejor como amigos"
    else:                  frase = "Incompatibles al maximo nivel"

    draw.text((340, 140), frase, font=fuente(12), fill=SUBTEXTO, anchor="mt")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ship.png")


async def generar_spotify_search(tracks: list, query: str) -> discord.File:
    filas = min(len(tracks), 4)
    W, H  = 680, 110 + (filas * 80)
    FONDO    = (10, 10, 10)
    VERDE    = (29, 185, 84)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)
    OSCURO   = (15, 15, 15)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ROSA)
    draw.rounded_rectangle([(24, 16), (656, 72)], radius=12, fill=(18, 18, 18))
    draw.rounded_rectangle([(24, 16), (656, 72)], radius=12, outline=GRIS, width=1)
    draw.text((42, 24), "Spotify Search", font=fuente(11), fill=SUBTEXTO)
    query_texto = query[:55] + "..." if len(query) > 55 else query
    draw.text((42, 42), query_texto, font=fuente(15, bold=True), fill=TEXTO)
    draw.rectangle([(24, 86), (656, 87)], fill=GRIS)

    for n, track in enumerate(tracks[:4]):
        y = 96 + (n * 80)
        draw.rounded_rectangle([(24, y), (656, y + 68)], radius=10, fill=(20, 20, 20) if n % 2 == 0 else OSCURO)
        draw.rounded_rectangle([(24, y), (656, y + 68)], radius=10, outline=GRIS, width=1)
        try:
            cover = await descargar_imagen(track["cover"])
            cover = cover.resize((52, 52)).convert("RGBA")
            mask = Image.new("L", (52, 52), 0)
            ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (52, 52)], radius=6, fill=255)
            cover_r = Image.new("RGBA", (52, 52), (0, 0, 0, 0))
            cover_r.paste(cover, (0, 0), mask)
            img.paste(cover_r, (36, y + 8), cover_r)
        except:
            draw.rounded_rectangle([(36, y + 8), (88, y + 60)], radius=6, fill=GRIS)

        draw.text((100, y + 8), f"{n+1}.", font=fuente(12, bold=True), fill=ROSA)
        nombre = track["nombre"][:38] + "..." if len(track["nombre"]) > 38 else track["nombre"]
        draw.text((118, y + 8), nombre, font=fuente(14, bold=True), fill=TEXTO)
        artista = track["artista"][:45] + "..." if len(track["artista"]) > 45 else track["artista"]
        draw.text((118, y + 30), artista, font=fuente(12), fill=ROSA)
        draw.text((634, y + 28), track.get("duracion", ""), font=fuente(11), fill=SUBTEXTO, anchor="ra")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="spotify_search.png")

async def generar_claves_list(usuario: discord.Member, claves: dict) -> discord.File:
    filas = min(len(claves), 8)
    W, H  = 680, 90 + (filas * 50)
    FONDO    = (10, 10, 10)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)
    OSCURO   = (15, 15, 15)
    CYAN     = (0, 188, 212)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ROSA)
    draw.text((34, 24), f"Claves de {usuario.display_name}", font=fuente(18, bold=True), fill=TEXTO)
    draw.rectangle([(34, 44), (646, 45)], fill=GRIS)

    if not claves:
        draw.text((340, H//2), "No tienes claves configuradas", font=fuente(14), fill=SUBTEXTO, anchor="mm")
    else:
        for n, (clave, mensaje) in enumerate(list(claves.items())[:8]):
            y = 54 + (n * 50)
            draw.rounded_rectangle([(34, y), (646, y + 38)], radius=8, fill=(26, 26, 26) if n % 2 == 0 else OSCURO)
            draw.text((54, y + 8), f" {clave}", font=fuente(12, bold=True), fill=ROSA)
            msg = mensaje[:45] + "..." if len(mensaje) > 45 else mensaje
            draw.text((54, y + 24), msg, font=fuente(10), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="claves_list.png")

# =========================================================
# COMANDOS
# =========================================================

@bot.tree.command(name="userinfo")
async def userinfo_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    await i.followup.send(file=await generar_userinfo(usuario))

@bot.command(name="userinfo")
async def userinfo_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    await ctx.send(file=await generar_userinfo(usuario))

@bot.tree.command(name="serverinfo")
async def serverinfo_slash(i: discord.Interaction):
    await i.response.defer()
    await i.followup.send(file=await generar_serverinfo(i.guild, i.user))

@bot.command(name="serverinfo")
async def serverinfo_prefix(ctx):
    await ctx.send(file=await generar_serverinfo(ctx.guild, ctx.author))

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
async def ban_prefix(ctx, usuario: discord.Member = None, *, razon: str = "Sin razon"):
    usuario = await get_member_from_ctx(ctx, usuario)
    if usuario == ctx.author:
        await ctx.send("> No puedes banearte a ti mismo")
        return
    try:
        await usuario.ban(reason=razon)
        await ctx.send(file=await generar_ban(usuario, razon, ctx.author))
    except Exception as e:
        await ctx.send(f"Error:\n```{e}```")

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick_slash(i: discord.Interaction, usuario: discord.Member, razon: str = "Sin razon"):
    if usuario == i.user:
        await i.response.send_message("> No puedes expulsarte a ti mismo", ephemeral=True)
        return
    await i.response.defer()
    try:
        await usuario.kick(reason=razon)
        embed = discord.Embed(color=0xff69b4)
        embed.description = f"> **{usuario.display_name}** fue expulsado\n> Razon: {razon}\n> Moderador: {i.user.mention}"
        await i.followup.send(embed=embed)
    except Exception as e:
        await i.followup.send(f"Error:\n```{e}```", ephemeral=True)

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_prefix(ctx, usuario: discord.Member = None, *, razon: str = "Sin razon"):
    usuario = await get_member_from_ctx(ctx, usuario)
    if usuario == ctx.author:
        await ctx.send("> No puedes expulsarte a ti mismo")
        return
    try:
        await usuario.kick(reason=razon)
        embed = discord.Embed(color=0xff69b4)
        embed.description = f"> **{usuario.display_name}** fue expulsado\n> Razon: {razon}"
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error:\n```{e}```")

@bot.tree.command(name="timeout", description="Silencia a un usuario por X minutos")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout_slash(i: discord.Interaction, usuario: discord.Member, minutos: int, razon: str = "Sin razon"):
    await i.response.defer()
    try:
        import datetime as dt
        until = discord.utils.utcnow() + dt.timedelta(minutes=minutos)
        await usuario.timeout(until, reason=razon)
        embed = discord.Embed(color=0xff69b4)
        embed.description = f"> **{usuario.display_name}** silenciado por `{minutos}` minutos\n> Razon: {razon}"
        await i.followup.send(embed=embed)
    except Exception as e:
        await i.followup.send(f"Error:\n```{e}```", ephemeral=True)

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

@bot.tree.command(name="avatar")
async def avatar_slash(i: discord.Interaction, usuario: discord.Member = None):
    usuario = usuario or i.user
    embed = discord.Embed(title=f"Avatar de {usuario.name}", color=0xff69b4)
    embed.set_image(url=usuario.display_avatar.url)
    await i.response.send_message(embed=embed)

@bot.command(name="avatar")
async def avatar_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    embed = discord.Embed(title=f"Avatar de {usuario.name}", color=0xff69b4)
    embed.set_image(url=usuario.display_avatar.url)
    await ctx.send(embed=embed)

@bot.tree.command(name="spotify", description="Muestra la musica que escucha un usuario")
async def spotify_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    actividad = discord.utils.find(lambda a: isinstance(a, discord.Spotify), usuario.activities)
    if not actividad:
        await i.followup.send(f"> **{usuario.name} no esta escuchando Spotify**")
        return
    await i.followup.send(file=await generar_spotify(usuario, actividad))

@bot.command(name="spotify")
async def spotify_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    actividad = discord.utils.find(lambda a: isinstance(a, discord.Spotify), usuario.activities)
    if not actividad:
        await ctx.send(f"**{usuario.display_name} no esta escuchando Spotify**")
        return
    await ctx.send(file=await generar_spotify(usuario, actividad))

@bot.tree.command(name="nivel", description="Ve tu nivel actual")
async def nivel_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    data = get_xp(i.guild.id, usuario.id)
    await i.followup.send(file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.command(name="nivel")
async def nivel_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    data = get_xp(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.tree.command(name="balance", description="Ve tu cuenta bancaria")
async def balance_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    data = get_user_eco(i.guild.id, usuario.id)
    await i.followup.send(file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.command(name="balance")
async def balance_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    data = get_user_eco(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_balance(usuario, data["coins"], data["last_daily"]))

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

@bot.tree.command(name="warn")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn_slash(i: discord.Interaction, usuario: discord.Member, razon: str):
    await i.response.defer()
    gid, uid = str(i.guild.id), str(usuario.id)
    if gid not in warnings_data: warnings_data[gid] = {}
    if uid not in warnings_data[gid]: warnings_data[gid][uid] = []
    warnings_data[gid][uid].append({"razon": razon, "moderador": str(i.user), "fecha": str(datetime.now())})
    await i.followup.send(file=await generar_warn(usuario, razon, len(warnings_data[gid][uid])))

@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def warn_prefix(ctx, usuario: discord.Member = None, *, razon: str = "Sin razon"):
    usuario = await get_member_from_ctx(ctx, usuario)
    gid, uid = str(ctx.guild.id), str(usuario.id)
    if gid not in warnings_data: warnings_data[gid] = {}
    if uid not in warnings_data[gid]: warnings_data[gid][uid] = []
    warnings_data[gid][uid].append({"razon": razon, "moderador": str(ctx.author), "fecha": str(datetime.now())})
    await ctx.send(file=await generar_warn(usuario, razon, len(warnings_data[gid][uid])))

@bot.tree.command(name="warnings")
async def warnings_slash(i: discord.Interaction, usuario: discord.Member):
    await i.response.defer()
    gid, uid = str(i.guild.id), str(usuario.id)
    if gid not in warnings_data or uid not in warnings_data[gid]:
        await i.followup.send("> Ese usuario no tiene warnings", ephemeral=True)
        return
    await i.followup.send(file=await generar_warnings(usuario, warnings_data[gid][uid]))

@bot.command(name="warnings")
async def warnings_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    gid, uid = str(ctx.guild.id), str(usuario.id)
    if gid not in warnings_data or uid not in warnings_data[gid]:
        await ctx.send("> Ese usuario no tiene warnings")
        return
    await ctx.send(file=await generar_warnings(usuario, warnings_data[gid][uid]))

@bot.tree.command(name="clearwarns", description="Borra todos los warns de un usuario")
@app_commands.checks.has_permissions(manage_messages=True)
async def clearwarns_slash(i: discord.Interaction, usuario: discord.Member):
    gid, uid = str(i.guild.id), str(usuario.id)
    if gid in warnings_data and uid in warnings_data[gid]:
        warnings_data[gid][uid] = []
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Warns de **{usuario.display_name}** borrados"
    await i.response.send_message(embed=embed)

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

@bot.tree.command(name="nuke")
@app_commands.checks.has_permissions(manage_channels=True)
async def nuke_slash(i: discord.Interaction):
    canal = i.channel
    nuevo = await canal.clone()
    await canal.delete()
    await nuevo.send(embed=discord.Embed(title="Canal Nukeado", description="> Canal purificado exitosamente.", color=0xff69b4))

@bot.command(name="nuke")
@commands.has_permissions(manage_channels=True)
async def nuke_prefix(ctx):
    canal = ctx.channel
    nuevo = await canal.clone()
    await canal.delete()
    await nuevo.send(embed=discord.Embed(title="Canal Nukeado", description="> Canal purificado exitosamente.", color=0xff69b4))

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

@bot.tree.command(name="ship", description="Calcula la compatibilidad entre dos usuarios")
async def ship_slash(i: discord.Interaction, usuario1: discord.Member, usuario2: discord.Member):
    await i.response.defer()
    seed = (usuario1.id + usuario2.id) % 101
    random.seed(seed)
    porcentaje = random.randint(0, 100)
    random.seed()
    await i.followup.send(file=await generar_ship(usuario1, usuario2, porcentaje))

@bot.command(name="ship")
async def ship_prefix(ctx, usuario1: discord.Member, usuario2: discord.Member):
    seed = (usuario1.id + usuario2.id) % 101
    random.seed(seed)
    porcentaje = random.randint(0, 100)
    random.seed()
    await ctx.send(file=await generar_ship(usuario1, usuario2, porcentaje))

@bot.tree.command(name="ping", description="Latencia del bot")
async def ping_slash(i: discord.Interaction):
    ms = round(bot.latency * 1000)
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Pong! `{ms}ms`"
    await i.response.send_message(embed=embed)

@bot.command(name="ping")
async def ping_prefix(ctx):
    ms = round(bot.latency * 1000)
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Pong! `{ms}ms`"
    await ctx.send(embed=embed)

@bot.tree.command(name="moneda", description="Tira una moneda")
async def moneda_slash(i: discord.Interaction):
    resultado = random.choice(["Cara", "Cruz"])
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Resultado: **{resultado}**"
    await i.response.send_message(embed=embed)

@bot.command(name="moneda")
async def moneda_prefix(ctx):
    resultado = random.choice(["Cara", "Cruz"])
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Resultado: **{resultado}**"
    await ctx.send(embed=embed)

@bot.tree.command(name="dado", description="Tira un dado de N caras")
async def dado_slash(i: discord.Interaction, caras: int = 6):
    resultado = random.randint(1, caras)
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Dado de {caras} caras: **{resultado}**"
    await i.response.send_message(embed=embed)

@bot.command(name="dado")
async def dado_prefix(ctx, caras: int = 6):
    resultado = random.randint(1, caras)
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Dado de {caras} caras: **{resultado}**"
    await ctx.send(embed=embed)

@bot.tree.command(name="ask")
async def ask_slash(i: discord.Interaction, mensaje: str):
    await i.response.defer()
    try:
        if any(p in mensaje.lower() for p in ["imagen", "foto", "dibujo", "genera", "wallpaper"]):
            image_url = f"https://image.pollinations.ai/prompt/{mensaje.replace(' ', '%20')}"
            embed = discord.Embed(title="Imagen generada", description=f"> Prompt: {mensaje}", color=0xff69b4)
            embed.set_image(url=image_url)
            await i.followup.send(embed=embed)
            return
        respuesta = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Eres un Bot amigable, divertida y algo sarcastica, tu nombre es Misti."}, {"role": "user", "content": mensaje}]
        )
        texto = respuesta.choices[0].message.content
        embed = discord.Embed(color=0xff69b4)
        embed.description = f"### Emisor\n> {mensaje}\n\n### Receptor\n> {texto}"
        await i.followup.send(embed=embed)
    except Exception as e:
        await i.followup.send(f"Error:\n```{e}```")

@bot.command(name="ask")
async def ask_prefix(ctx, *, mensaje: str):
    try:
        respuesta = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Eres un Bot amigable, divertida y algo sarcastica, tu nombre es Misti."}, {"role": "user", "content": mensaje}]
        )
        texto = respuesta.choices[0].message.content
        embed = discord.Embed(color=0xff69b4)
        embed.description = f"### Emisor\n> {mensaje}\n\n### Receptor\n> {texto}"
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error:\n```{e}```")

# =========================================================
# SISTEMA DE CLAVES
# =========================================================

@bot.tree.command(name="clave", description="Crea una clave personalizada")
async def clave_slash(i: discord.Interaction, clave: str, mensaje: str):
    await i.response.defer()
    uid = str(i.user.id)
    gid = str(i.guild.id)
    
    claves = get_user_claves(gid, i.user.id)
    clave_lower = clave.lower()
    
    if clave_lower in claves:
        embed = discord.Embed(color=0xff69b4)
        embed.description = f"> La clave **{clave}** ya existe\n> Usa `/clave-delete` para eliminarla primero"
        await i.followup.send(embed=embed)
        return
    
    claves[clave_lower] = mensaje
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Clave **{clave}** creada exitosamente\n> Respuesta: `{mensaje}`"
    await i.followup.send(embed=embed)

@bot.command(name="clave")
async def clave_prefix(ctx, clave: str, *, mensaje: str):
    uid = str(ctx.author.id)
    gid = str(ctx.guild.id)
    
    claves = get_user_claves(gid, ctx.author.id)
    clave_lower = clave.lower()
    
    if clave_lower in claves:
        embed = discord.Embed(color=0xff69b4)
        embed.description = f"> La clave **{clave}** ya existe\n> Usa `>mt clave-delete` para eliminarla primero"
        await ctx.send(embed=embed)
        return
    
    claves[clave_lower] = mensaje
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Clave **{clave}** creada exitosamente\n> Respuesta: `{mensaje}`"
    await ctx.send(embed=embed)

@bot.tree.command(name="clave-list", description="Ver todas tus claves configuradas")
async def clave_list_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = usuario or i.user
    gid = str(i.guild.id)
    claves = get_user_claves(gid, usuario.id)
    
    usuario_obj = i.guild.get_member(usuario.id)
    await i.followup.send(file=await generar_claves_list(usuario_obj, claves))

@bot.command(name="clave-list")
async def clave_list_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    gid = str(ctx.guild.id)
    claves = get_user_claves(gid, usuario.id)
    
    await ctx.send(file=await generar_claves_list(usuario, claves))

@bot.tree.command(name="clave-delete", description="Elimina una clave")
async def clave_delete_slash(i: discord.Interaction, clave: str):
    await i.response.defer()
    gid = str(i.guild.id)
    claves = get_user_claves(gid, i.user.id)
    clave_lower = clave.lower()
    
    if clave_lower not in claves:
        embed = discord.Embed(color=0xff69b4)
        embed.description = f"> La clave **{clave}** no existe"
        await i.followup.send(embed=embed)
        return
    
    del claves[clave_lower]
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Clave **{clave}** eliminada exitosamente"
    await i.followup.send(embed=embed)

@bot.command(name="clave-delete")
async def clave_delete_prefix(ctx, clave: str):
    gid = str(ctx.guild.id)
    claves = get_user_claves(gid, ctx.author.id)
    clave_lower = clave.lower()
    
    if clave_lower not in claves:
        embed = discord.Embed(color=0xff69b4)
        embed.description = f"> La clave **{clave}** no existe"
        await ctx.send(embed=embed)
        return
    
    del claves[clave_lower]
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Clave **{clave}** eliminada exitosamente"
    await ctx.send(embed=embed)

# =========================================================
# WELC / BYE
# =========================================================

@bot.tree.command(name="welc", description="Configura el mensaje de bienvenida")
@app_commands.checks.has_permissions(administrator=True)
async def welc(i: discord.Interaction, canal: discord.TextChannel, titulo: str = None, descripcion: str = None, color: str = None, autor: str = None, autor_imagen: str = None, imagen: str = None, footer: str = None, footer_imagen: str = None):
    try:
        color_final = int(color.replace("#", ""), 16) if color else 0xFFFFFF
    except:
        color_final = 0xFFFFFF

    welc_config[i.guild.id] = {
        "canal": canal.id, "titulo": titulo, "desc": descripcion,
        "color": color_final, "autor": (autor, autor_imagen),
        "imagen": imagen, "footer": (footer, footer_imagen)
    }
    await i.response.send_message(f"> Bienvenida activada en {canal.mention}", ephemeral=True)

@bot.tree.command(name="bye", description="Configura el mensaje de despedida")
@app_commands.checks.has_permissions(administrator=True)
async def bye(i: discord.Interaction, canal: discord.TextChannel, titulo: str = None, descripcion: str = None, color: str = None, autor: str = None, autor_imagen: str = None, imagen: str = None, footer: str = None, footer_imagen: str = None):
    try:
        color_final = int(color.replace("#", ""), 16) if color else 0xFFFFFF
    except:
        color_final = 0xFFFFFF

    bye_config[i.guild.id] = {
        "canal": canal.id, "titulo": titulo, "desc": descripcion,
        "color": color_final, "autor": (autor, autor_imagen),
        "imagen": imagen, "footer": (footer, footer_imagen)
    }
    await i.response.send_message(f"> Despedida activada en {canal.mention}", ephemeral=True)

@bot.tree.command(name="reset-welc")
@app_commands.checks.has_permissions(administrator=True)
async def reset_welc(i: discord.Interaction):
    welc_config.pop(i.guild.id, None)
    await i.response.send_message("> Bienvenida desactivada", ephemeral=True)

@bot.tree.command(name="reset-bye")
@app_commands.checks.has_permissions(administrator=True)
async def reset_bye(i: discord.Interaction):
    bye_config.pop(i.guild.id, None)
    await i.response.send_message("> Despedida desactivada", ephemeral=True)

# =========================================================
# EMBED CREATE
# =========================================================

@bot.tree.command(name="embed-create")
@app_commands.checks.has_permissions(administrator=True)
async def embed_create(i: discord.Interaction, canal: discord.TextChannel = None, titulo: str = None, descripcion: str = None, color: str = None, imagen: str = None, footer_texto: str = None, autor_nombre: str = None):
    canal = canal or i.channel
    try:
        color_final = int(color.replace("#", ""), 16) if color else 0x000000
    except:
        color_final = 0x000000

    embed = discord.Embed(title=titulo or "", description=descripcion or "", color=color_final)
    if imagen:
        embed.set_image(url=imagen)
    if footer_texto:
        embed.set_footer(text=footer_texto)
    if autor_nombre:
        embed.set_author(name=autor_nombre)

    await canal.send(embed=embed)
    await i.response.send_message("Embed enviado", ephemeral=True)

# =========================================================
# SPOTIFY SEARCH
# =========================================================

async def buscar_spotify(query: str) -> list:
    url = "https://spotify23.p.rapidapi.com/search/"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": "spotify23.p.rapidapi.com"}
    params  = {"q": query, "type": "tracks", "limit": "4", "offset": "0"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as r:
            data = await r.json()

    tracks = []
    for item in data.get("tracks", {}).get("items", [])[:4]:
        track    = item.get("data", {})
        nombre   = track.get("name", "Sin nombre")
        artista  = ", ".join([a.get("profile", {}).get("name", "") for a in track.get("artists", {}).get("items", [])])
        covers   = track.get("albumOfTrack", {}).get("coverArt", {}).get("sources", [])
        cover    = covers[0].get("url", "") if covers else ""
        ms       = track.get("duration", {}).get("totalMilliseconds", 0)
        seg      = ms // 1000
        duracion = f"{seg // 60}:{seg % 60:02}"
        track_uri = track.get("uri", "")
        track_id  = track_uri.split(":")[-1] if track_uri else ""
        track_url = f"https://open.spotify.com/track/{track_id}" if track_id else "https://open.spotify.com"
        tracks.append({"nombre": nombre, "artista": artista, "cover": cover, "duracion": duracion, "url": track_url})

    return tracks

class SpotifySearchView(discord.ui.View):
    def __init__(self, tracks: list):
        super().__init__(timeout=None)
        for n, track in enumerate(tracks[:4]):
            nombre = track["nombre"][:40] + "..." if len(track["nombre"]) > 40 else track["nombre"]
            self.add_item(discord.ui.Button(label=f"{n+1}. {nombre}", url=track["url"], style=discord.ButtonStyle.link, emoji="🎵"))

@bot.tree.command(name="spotify-search", description="Busca una cancion en Spotify")
async def spotify_buscar_slash(i: discord.Interaction, cancion: str):
    await i.response.defer()
    try:
        tracks = await buscar_spotify(cancion)
        if not tracks:
            await i.followup.send("> No se encontraron resultados.", ephemeral=True)
            return
        await i.followup.send(file=await generar_spotify_search(tracks, cancion), view=SpotifySearchView(tracks))
    except Exception as e:
        await i.followup.send(f"Error:\n```{e}```", ephemeral=True)

@bot.command(name="spotify-search")
async def spotify_buscar_prefix(ctx, *, cancion: str):
    async with ctx.typing():
        try:
            tracks = await buscar_spotify(cancion)
            if not tracks:
                await ctx.send("> No se encontraron resultados.")
                return
            await ctx.send(file=await generar_spotify_search(tracks, cancion), view=SpotifySearchView(tracks))
        except Exception as e:
            await ctx.send(f"Error:\n```{e}```")

# =========================================================
# ROBLOX
# =========================================================

@bot.hybrid_command(name="roblox", description="Mira el perfil de roblox de alguien")
async def roblox(ctx: commands.Context, usuario: str):
    await ctx.defer() if ctx.interaction else None

    async with aiohttp.ClientSession() as session:
        data_user = {"usernames": [usuario], "excludeBannedUsers": False}
        async with session.post("https://users.roblox.com/v1/usernames/users", json=data_user) as resp:
            if resp.status != 200:
                return await ctx.send("> Error al conectar con la API de Roblox.")
            res_user = await resp.json()
            if not res_user["data"]:
                return await ctx.send(f"> El usuario **{usuario}** no existe en Roblox.")
            user_info   = res_user["data"][0]
            user_id     = user_info["id"]
            roblox_user = user_info["displayName"]

        async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as resp:
            res_details   = await resp.json()
            fecha_iso     = res_details["created"].split("T")[0]
            fecha_obj     = datetime.strptime(fecha_iso, "%Y-%m-%d")
            cuenta_creada = fecha_obj.strftime("%d/%m/%Y")

        async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count") as resp:
            res_friends     = await resp.json()
            cantidad_amigos = res_friends.get("count", 0)

        avatar_url = "https://images.rbxcdn.com/default_avatar.png"
        async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false") as resp:
            if resp.status == 200:
                res_thumb = await resp.json()
                if res_thumb["data"]:
                    avatar_url = res_thumb["data"][0]["imageUrl"]

    perfil_link = f"https://www.roblox.com/users/{user_id}/profile"
    embed = discord.Embed(
        description=(
            f"> **User:** {roblox_user}\n"
            f"> **Creada:** {cuenta_creada}\n"
            f"> **Amigos:** {cantidad_amigos}\n"
            f"> **Link:** [Visitar Perfil]({perfil_link})"
        ),
        color=0xff69b4
    )
    embed.set_image(url=avatar_url)

    if ctx.interaction:
        await ctx.interaction.followup.send(embed=embed)
    else:
        await ctx.send(embed=embed)

# =========================================================
# ON MESSAGE
# =========================================================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id in afk_data:
        tiempo_inicio = afk_data[message.author.id]["tiempo"]
        segundos_totales = int(time.time() - tiempo_inicio)
        m, s = divmod(segundos_totales, 60)
        h, m = divmod(m, 60)
        tiempo_texto = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s" if m > 0 else f"{s}s"
        await message.channel.send(f"**Bienvenido de nuevo {message.author.name}**\n> estuviste `{tiempo_texto}` inactivo")
        del afk_data[message.author.id]

    for user in message.mentions:
        if user.id in afk_data and user.id != message.author.id:
            await message.channel.send(f"**{user.name}** esta dormido...\n> Motivo: `{afk_data[user.id]['motivo']}`")

    # Sistema de claves
    if message.guild:
        gid = str(message.guild.id)
        uid = str(message.author.id)
        if gid in claves_data and uid in claves_data[gid]:
            mensaje_lower = message.content.lower()
            for clave, respuesta in claves_data[gid][uid].items():
                if mensaje_lower == clave:
                    await message.reply(respuesta, mention_author=False)
                    break

    await bot.process_commands(message)

    if message.guild:
        uid = str(message.author.id)
        if uid not in mensaje_count: mensaje_count[uid] = 0
        mensaje_count[uid] += 1
        if mensaje_count[uid] >= 5:
            mensaje_count[uid] = 0
            data = get_user_eco(str(message.guild.id), message.author.id)
            data["coins"] += random.randint(2, 4)

    if not message.reference:
        return

    try:
        replied = await message.channel.fetch_message(message.reference.message_id)
        if replied.author.id != bot.user.id:
            return
        mensaje_original = replied.content
        if replied.embeds and replied.embeds[0].description:
            mensaje_original = replied.embeds[0].description
        system_prompt = f"Tu nombre SIEMPRE es Misti. Eres un bot de Discord divertido, sarcastico y transexual. El usuario se llama {message.author.display_name} y estas en {message.guild.name}"
        respuesta = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}, {"role": "assistant", "content": mensaje_original}, {"role": "user", "content": message.content}]
        )
        texto = respuesta.choices[0].message.content
        embed = discord.Embed(color=0xff69b4)
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
    cfg = welc_config.get(member.guild.id)
    if not cfg:
        return
    canal = member.guild.get_channel(cfg["canal"])
    if not canal:
        return

    embed = discord.Embed(
        title=parse_text(cfg.get("titulo") or f"Bienvenido {member.name}", member),
        description=parse_text(cfg.get("desc") or "", member),
        color=cfg.get("color", 0xFFFFFF)
    )
    autor_n, autor_i = cfg.get("autor", (None, None))
    if autor_n:
        embed.set_author(name=parse_text(autor_n, member), icon_url=parse_text(autor_i or "", member) or None)
    if cfg.get("imagen"):
        embed.set_image(url=parse_text(cfg["imagen"], member))
    footer_t, footer_i = cfg.get("footer", (None, None))
    if footer_t:
        embed.set_footer(text=parse_text(footer_t, member), icon_url=parse_text(footer_i or "", member) or None)

    await canal.send(embed=embed)

@bot.event
async def on_member_remove(member):
    if member.bot:
        return
    cfg = bye_config.get(member.guild.id)
    if not cfg:
        return
    canal = member.guild.get_channel(cfg["canal"])
    if not canal:
        return

    embed = discord.Embed(
        title=parse_text(cfg.get("titulo") or f"Adios {member.name}", member),
        description=parse_text(cfg.get("desc") or "", member),
        color=cfg.get("color", 0xFFFFFF)
    )
    autor_n, autor_i = cfg.get("autor", (None, None))
    if autor_n:
        embed.set_author(name=parse_text(autor_n, member), icon_url=parse_text(autor_i or "", member) or None)
    if cfg.get("imagen"):
        embed.set_image(url=parse_text(cfg["imagen"], member))
    footer_t, footer_i = cfg.get("footer", (None, None))
    if footer_t:
        embed.set_footer(text=parse_text(footer_t, member), icon_url=parse_text(footer_i or "", member) or None)

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
# ADMIN COMMANDS - XP/DINERO
# =========================================================

@bot.tree.command(name="add-nivel", description="Agregar niveles a un usuario (ADMIN)")
@app_commands.checks.has_permissions(administrator=True)
async def add_nivel_slash(i: discord.Interaction, usuario: discord.Member, cantidad: int):
    await i.response.defer()
    data = get_xp(i.guild.id, usuario.id)
    data["level"] += cantidad
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Se agregaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await i.followup.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.command(name="add-nivel")
@commands.has_permissions(administrator=True)
async def add_nivel_prefix(ctx, usuario: discord.Member, cantidad: int):
    data = get_xp(ctx.guild.id, usuario.id)
    data["level"] += cantidad
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Se agregaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await ctx.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.tree.command(name="remove-nivel", description="Quitar niveles a un usuario (ADMIN)")
@app_commands.checks.has_permissions(administrator=True)
async def remove_nivel_slash(i: discord.Interaction, usuario: discord.Member, cantidad: int):
    await i.response.defer()
    data = get_xp(i.guild.id, usuario.id)
    data["level"] = max(1, data["level"] - cantidad)
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Se quitaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await i.followup.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.command(name="remove-nivel")
@commands.has_permissions(administrator=True)
async def remove_nivel_prefix(ctx, usuario: discord.Member, cantidad: int):
    data = get_xp(ctx.guild.id, usuario.id)
    data["level"] = max(1, data["level"] - cantidad)
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Se quitaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await ctx.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.tree.command(name="add-dinero", description="Agregar dinero a un usuario (ADMIN)")
@app_commands.checks.has_permissions(administrator=True)
async def add_dinero_slash(i: discord.Interaction, usuario: discord.Member, cantidad: int):
    await i.response.defer()
    data = get_user_eco(i.guild.id, usuario.id)
    data["coins"] += cantidad
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Se agregaron **${cantidad:,}** monedas a {usuario.mention}\n> Dinero actual: **${data['coins']:,}**"
    await i.followup.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.command(name="add-dinero")
@commands.has_permissions(administrator=True)
async def add_dinero_prefix(ctx, usuario: discord.Member, cantidad: int):
    data = get_user_eco(ctx.guild.id, usuario.id)
    data["coins"] += cantidad
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Se agregaron **${cantidad:,}** monedas a {usuario.mention}\n> Dinero actual: **${data['coins']:,}**"
    await ctx.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.tree.command(name="remove-dinero", description="Quitar dinero a un usuario (ADMIN)")
@app_commands.checks.has_permissions(administrator=True)
async def remove_dinero_slash(i: discord.Interaction, usuario: discord.Member, cantidad: int):
    await i.response.defer()
    data = get_user_eco(i.guild.id, usuario.id)
    data["coins"] = max(0, data["coins"] - cantidad)
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Se quitaron **${cantidad:,}** monedas a {usuario.mention}\n> Dinero actual: **${data['coins']:,}**"
    await i.followup.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.command(name="remove-dinero")
@commands.has_permissions(administrator=True)
async def remove_dinero_prefix(ctx, usuario: discord.Member, cantidad: int):
    data = get_user_eco(ctx.guild.id, usuario.id)
    data["coins"] = max(0, data["coins"] - cantidad)
    embed = discord.Embed(color=0xff69b4)
    embed.description = f"> Se quitaron **${cantidad:,}** monedas a {usuario.mention}\n> Dinero actual: **${data['coins']:,}**"
    await ctx.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

# =========================================================
# ERROR HANDLER
# =========================================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    embed = discord.Embed(title="Error", description=f"```{str(error)}```", color=0xff69b4)
    await ctx.send(embed=embed, delete_after=10)

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
