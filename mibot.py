import discord
import os
import io
from datetime import datetime
import asyncio
import random
import json
import time
import aiohttp
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
from groq import AsyncGroq
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading

PLAYLIST_FILE = "playlists.json"

def cargar_playlists():
    if not os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_playlists(data):
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
TOKEN        = os.getenv("TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

AZUL_OSCURO   = (43, 85, 181)
AZUL_IPOD     = (43, 85, 181)
AZUL_IPOD_NUM = 0x2B55B5
ROSA_RGB      = (255, 105, 180)
ROSA_HEX      = 0x2B55B5
BLANCO        = (255, 255, 255)
CELESTE       = 0x2B55B5
FONDO_G       = (10, 10, 10)
GRIS_G        = (42, 42, 42)
TEXTO_G       = (255, 255, 255)
SUB_G         = (136, 136, 136)
OSCU_G        = (15, 15, 15)

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

class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=">mt ", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()

bot = DarkyBot()

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")

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

async def generar_userinfo(usuario: discord.Member) -> discord.File:
    W, H = 700, 340
    FONDO_USER    = (30, 31, 34)
    TEXTO_USER    = (255, 255, 255)
    SUBTEXTO_USER = (180, 180, 190)
    CAMPO_FONDO   = (40, 43, 48)
    img  = Image.new("RGBA", (W, H), FONDO_USER)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (6, H)], fill=AZUL_OSCURO)
    avatar_img = await descargar_imagen(str(usuario.display_avatar.url))
    avatar_img = avatar_circular(avatar_img, 90)
    img.paste(avatar_img, (24, 20), avatar_img)
    draw.text((128, 22), usuario.display_name, font=fuente(26, bold=True), fill=TEXTO_USER)
    draw.text((128, 56), f"@{usuario.name}", font=fuente(16), fill=SUBTEXTO_USER)
    draw.rectangle([(24, 126), (W - 24, 128)], fill=(60, 63, 70))
    col1_x = 24
    col2_x = 370
    y = 148
    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, fill=CAMPO_FONDO)
        draw.text((x + 12, y + 8), titulo, font=fuente(13), fill=SUBTEXTO_USER)
        draw.text((x + 12, y + 30), valor, font=fuente(17, bold=True), fill=TEXTO_USER)
    campo(col1_x, y, "USUARIO", f"@{usuario.display_name}")
    campo(col2_x, y, "ID", str(usuario.id))
    y2 = y + 80
    creado = usuario.created_at.strftime("%d/%m/%Y")
    entro  = usuario.joined_at.strftime("%d/%m/%Y") if usuario.joined_at else "?"
    campo(col1_x, y2, "CUENTA CREADA", creado)
    campo(col2_x, y2, "ENTRO AL SERVER", entro)
    draw.text((24, H - 22), f"Solicitado por {usuario.display_name}", font=fuente(12), fill=SUBTEXTO_USER)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="userinfo.png")

async def generar_serverinfo(guild: discord.Guild, solicitante: discord.Member, color_barra=None, color_circulo=None) -> discord.File:
    c_barra   = color_barra   or AZUL_OSCURO
    c_circulo = color_circulo or AZUL_OSCURO
    W, H        = 700, 400
    CAMPO_FONDO = (20, 20, 20)
    CAMPO_BORDE = (50, 50, 60)
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (6, H)], fill=c_barra)
    if guild.icon:
        icon_img = await descargar_imagen(str(guild.icon.url))
        icon_img = avatar_circular(icon_img, 90)
        img.paste(icon_img, (24, 20), icon_img)
        nombre_x = 128
    else:
        nombre_x = 24
    draw.ellipse([(22, 18), (116, 112)], outline=c_circulo, width=2)
    draw.text((nombre_x, 22), guild.name, font=fuente(26, bold=True), fill=TEXTO_G)
    draw.text((nombre_x, 56), f"ID: {guild.id}", font=fuente(14), fill=SUB_G)
    draw.rectangle([(24, 126), (W - 24, 127)], fill=c_barra)
    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, fill=CAMPO_FONDO)
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, outline=CAMPO_BORDE, width=1)
        draw.rounded_rectangle([(x, y + 8), (x + 3, y + 56)], radius=2, fill=c_barra)
        draw.text((x + 12, y + 8), titulo, font=fuente(13), fill=SUB_G)
        draw.text((x + 12, y + 30), str(valor), font=fuente(17, bold=True), fill=TEXTO_G)
    y = 148
    campo(24, y, "OWNER", guild.owner.display_name if guild.owner else "?")
    campo(370, y, "CREADO", guild.created_at.strftime("%d/%m/%Y"))
    y2    = y + 80
    ancho3 = 204
    campo(24,       y2, "MIEMBROS", str(guild.member_count), ancho=ancho3)
    campo(24 + 224, y2, "ROLES",    str(len(guild.roles)),   ancho=ancho3)
    campo(24 + 448, y2, "EMOJIS",   str(len(guild.emojis)),  ancho=ancho3)
    y3 = y2 + 80
    campo(24,       y3, "TEXTO",  str(len(guild.text_channels)),  ancho=ancho3)
    campo(24 + 224, y3, "VOZ",    str(len(guild.voice_channels)), ancho=ancho3)
    campo(24 + 448, y3, "BOOSTS", f"{guild.premium_subscription_count} (nv {guild.premium_tier})", ancho=ancho3)
    draw.text((24, H - 22), f"Solicitado por {solicitante.display_name}", font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="serverinfo.png")

async def generar_nivel(usuario: discord.Member, nivel: int, xp: int, xp_needed: int) -> discord.File:
    W, H = 680, 180
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 100)
        img.paste(av, (38, 40), av)
    except:
        draw.ellipse([(38, 40), (138, 140)], fill=GRIS_G)
    draw.ellipse([(36, 38), (140, 142)], outline=AZUL_OSCURO, width=2)
    draw.text((162, 28), usuario.display_name, font=fuente(21, bold=True), fill=TEXTO_G)
    draw.rounded_rectangle([(162, 62), (242, 84)], radius=11, fill=AZUL_OSCURO)
    draw.text((202, 68), f"Nivel {nivel}", font=fuente(12, bold=True), fill=TEXTO_G, anchor="mt")
    draw.text((162, 100), f"{xp} / {xp_needed} XP", font=fuente(12), fill=SUB_G)
    draw.rounded_rectangle([(162, 118), (630, 130)], radius=6, fill=GRIS_G)
    progreso = min(xp / xp_needed, 1.0)
    fill_w   = int(162 + (468 * progreso))
    if fill_w > 162:
        draw.rounded_rectangle([(162, 118), (fill_w, 130)], radius=6, fill=AZUL_OSCURO)
    draw.text((162, 152), f"Subiste al nivel {nivel} — sigue asi!", font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="nivel.png")

async def generar_balance(usuario: discord.Member, coins: int, last_daily: float) -> discord.File:
    W, H = 680, 170
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 37), av)
    except:
        draw.ellipse([(37, 37), (133, 133)], fill=GRIS_G)
    draw.ellipse([(35, 35), (135, 135)], outline=AZUL_OSCURO, width=2)
    draw.text((158, 48), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO_G)
    draw.rectangle([(158, 90), (640, 91)], fill=GRIS_G)
    draw.text((158, 106), f"$ {coins:,} monedas", font=fuente(22, bold=True), fill=AZUL_OSCURO)
    if last_daily == 0:
        daily_texto = "Nunca reclamaste tu daily"
    else:
        hace = int(time.time() - last_daily)
        if hace < 3600:    daily_texto = f"Ultimo daily: hace {hace // 60} minutos"
        elif hace < 86400: daily_texto = f"Ultimo daily: hace {hace // 3600} horas"
        else:              daily_texto = f"Ultimo daily: hace {hace // 86400} dias"
    draw.text((158, 148), daily_texto, font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="balance.png")

async def generar_ranking(guild: discord.Guild, top: list) -> discord.File:
    filas = len(top)
    W, H  = 680, 130 + (filas * 46)
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    draw.text((34, 30), "Ranking", font=fuente(18, bold=True), fill=TEXTO_G)
    draw.text((34, 58), "Top usuarios con mas monedas", font=fuente(11), fill=SUB_G)
    draw.rectangle([(34, 72), (646, 73)], fill=GRIS_G)
    for n, (uid, data) in enumerate(top):
        member = guild.get_member(int(uid))
        nombre = member.display_name if member else f"Usuario {uid}"
        nombre = nombre[:20] + "..." if len(nombre) > 20 else nombre
        y = 82 + (n * 46)
        draw.rounded_rectangle([(34, y), (646, y + 36)], radius=8, fill=(26, 26, 26) if n == 0 else OSCU_G)
        medalla = f"#{n+1}" if n >= 3 else str(n+1)
        draw.text((54, y + 10), medalla, font=fuente(14, bold=True), fill=AZUL_OSCURO if n == 0 else SUB_G)
        draw.text((90, y + 10), nombre, font=fuente(13, bold=n == 0), fill=TEXTO_G)
        draw.text((620, y + 10), f"$ {data['coins']:,}", font=fuente(13), fill=AZUL_OSCURO if n == 0 else SUB_G, anchor="ra")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ranking.png")

async def generar_ban(usuario: discord.Member, razon: str, moderador: discord.Member) -> discord.File:
    W, H = 680, 190
    ROJO = (239, 68, 68)
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 47), av)
    except:
        draw.ellipse([(37, 47), (133, 143)], fill=GRIS_G)
    draw.ellipse([(35, 45), (135, 145)], outline=AZUL_OSCURO, width=2)
    draw.line([(50, 60), (120, 130)], fill=ROJO, width=3)
    draw.line([(120, 60), (50, 130)], fill=ROJO, width=3)
    draw.text((158, 42), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO_G)
    draw.rounded_rectangle([(158, 68), (228, 90)], radius=11, fill=AZUL_OSCURO)
    draw.text((193, 74), "Baneado", font=fuente(12, bold=True), fill=TEXTO_G, anchor="mt")
    draw.rectangle([(158, 104), (645, 105)], fill=GRIS_G)
    draw.text((158, 116), "RAZON", font=fuente(11), fill=SUB_G)
    razon_texto = razon[:50] + "..." if len(razon) > 50 else razon
    draw.text((158, 134), razon_texto, font=fuente(15, bold=True), fill=TEXTO_G)
    draw.text((158, 164), f"Moderador: {moderador.display_name}", font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ban.png")

async def generar_afk(usuario: discord.Member, motivo: str, color_barra=None) -> discord.File:
    c_barra = color_barra or AZUL_OSCURO
    W, H    = 680, 190
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=c_barra)
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 47), av)
    except:
        draw.ellipse([(37, 47), (133, 143)], fill=GRIS_G)
    draw.ellipse([(35, 45), (135, 145)], outline=c_barra, width=2)
    draw.text((98, 72),  "z", font=fuente(17, bold=True), fill=BLANCO)
    draw.text((110, 58), "z", font=fuente(14, bold=True), fill=BLANCO)
    draw.text((120, 46), "z", font=fuente(11),            fill=BLANCO)
    draw.text((158, 42), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO_G)
    draw.rounded_rectangle([(158, 68), (218, 90)], radius=11, fill=c_barra)
    draw.text((188, 74), "AFK", font=fuente(12, bold=True), fill=FONDO_G, anchor="mt")
    draw.rectangle([(158, 104), (645, 105)], fill=GRIS_G)
    draw.text((158, 116), "MOTIVO", font=fuente(11), fill=SUB_G)
    motivo_texto = motivo[:50] + "..." if len(motivo) > 50 else motivo
    draw.text((158, 134), motivo_texto, font=fuente(15, bold=True), fill=TEXTO_G)
    draw.text((158, 164), "Te avisare si te mencionan...", font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="afk.png")

async def generar_spotify(usuario: discord.Member, actividad: discord.Spotify) -> discord.File:
    W, H = 680, 180
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    try:
        portada = await descargar_imagen(actividad.album_cover_url)
        portada = portada.resize((130, 130)).convert("RGBA")
        mask    = Image.new("L", (130, 130), 0)
        ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (130, 130)], radius=10, fill=255)
        portada_r = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
        portada_r.paste(portada, (0, 0), mask)
        img.paste(portada_r, (30, 25), portada_r)
    except:
        draw.rounded_rectangle([(30, 25), (160, 155)], radius=10, fill=GRIS_G)
    draw.rounded_rectangle([(29, 24), (161, 156)], radius=10, outline=AZUL_OSCURO, width=2)
    draw.text((182, 28), f"{usuario.display_name} esta escuchando", font=fuente(13), fill=SUB_G)
    cancion = actividad.title[:30] + "..." if len(actividad.title) > 30 else actividad.title
    draw.text((182, 50), cancion, font=fuente(20, bold=True), fill=TEXTO_G)
    draw.text((182, 78), actividad.artist, font=fuente(14), fill=AZUL_OSCURO)
    album = actividad.album[:35] + "..." if len(actividad.album) > 35 else actividad.album
    draw.text((182, 100), album, font=fuente(12), fill=SUB_G)
    draw.rectangle([(182, 118), (645, 119)], fill=GRIS_G)
    ahora        = discord.utils.utcnow()
    duracion     = actividad.duration.total_seconds()
    transcurrido = (ahora - actividad.start).total_seconds()
    progreso     = min(transcurrido / duracion, 1.0) if duracion > 0 else 0
    draw.rounded_rectangle([(182, 128), (645, 136)], radius=4, fill=GRIS_G)
    fill_w = int(182 + (463 * progreso))
    if fill_w > 182:
        draw.rounded_rectangle([(182, 128), (fill_w, 136)], radius=4, fill=BLANCO)
    fmt = lambda s: f"{int(s) // 60}:{int(s) % 60:02}"
    draw.text((182, 148), fmt(max(transcurrido, 0)), font=fuente(11), fill=SUB_G)
    draw.text((645, 148), fmt(duracion), font=fuente(11), fill=SUB_G, anchor="ra")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="spotify.png")

async def generar_warn(usuario: discord.Member, razon: str, total: int) -> discord.File:
    W, H = 680, 180
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    draw.polygon([(80, 22), (138, 122), (22, 122)], fill=AZUL_OSCURO)
    draw.rounded_rectangle([(75, 44), (85, 90)], radius=5, fill=FONDO_G)
    draw.ellipse([(74, 102), (86, 114)], fill=FONDO_G)
    draw.text((162, 28), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO_G)
    draw.rounded_rectangle([(162, 56), (252, 78)], radius=11, fill=AZUL_OSCURO)
    draw.text((207, 62), "Advertido", font=fuente(12, bold=True), fill=FONDO_G, anchor="mt")
    draw.rectangle([(162, 92), (645, 93)], fill=GRIS_G)
    draw.text((162, 104), "RAZON", font=fuente(11), fill=SUB_G)
    razon_texto = razon[:50] + "..." if len(razon) > 50 else razon
    draw.text((162, 122), razon_texto, font=fuente(15, bold=True), fill=TEXTO_G)
    draw.text((162, 154), f"Total de warns: {total}", font=fuente(12), fill=AZUL_OSCURO)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="warn.png")

async def generar_warnings(usuario: discord.Member, warns: list) -> discord.File:
    filas = min(len(warns), 10)
    W, H  = 680, 90 + (filas * 44)
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    draw.text((34, 24), f"Warns de {usuario.display_name}", font=fuente(18, bold=True), fill=TEXTO_G)
    draw.rectangle([(34, 44), (646, 45)], fill=GRIS_G)
    for n, w in enumerate(warns[:10]):
        y = 54 + (n * 44)
        draw.rounded_rectangle([(34, y), (646, y + 34)], radius=8, fill=(26, 26, 26) if n % 2 == 0 else OSCU_G)
        draw.text((54, y + 8), f"#{n+1}", font=fuente(13, bold=True), fill=AZUL_OSCURO)
        razon = w["razon"][:40] + "..." if len(w["razon"]) > 40 else w["razon"]
        draw.text((88, y + 10), razon, font=fuente(13), fill=TEXTO_G)
        mod = w["moderador"][:20] + "..." if len(w["moderador"]) > 20 else w["moderador"]
        draw.text((634, y + 10), mod, font=fuente(11), fill=SUB_G, anchor="ra")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="warnings.png")

async def generar_lock(canal: discord.TextChannel, bloqueado: bool) -> discord.File:
    W, H = 680, 170
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    draw.rounded_rectangle([(44, 88), (116, 144)], radius=8, fill=AZUL_OSCURO)
    if bloqueado:
        draw.arc([(56, 42), (104, 98)], start=180, end=0, fill=AZUL_OSCURO, width=10)
    else:
        draw.arc([(68, 30), (116, 86)], start=180, end=360, fill=AZUL_OSCURO, width=10)
    draw.ellipse([(71, 103), (89, 121)], fill=FONDO_G)
    draw.rounded_rectangle([(76, 112), (84, 126)], radius=3, fill=FONDO_G)
    titulo = "Canal Bloqueado" if bloqueado else "Canal Desbloqueado"
    draw.text((144, 32), titulo, font=fuente(22, bold=True), fill=TEXTO_G)
    draw.rectangle([(144, 62), (654, 63)], fill=GRIS_G)
    draw.text((144, 76), "CANAL", font=fuente(12), fill=SUB_G)
    draw.text((144, 96), f"# {canal.name}", font=fuente(15, bold=True), fill=TEXTO_G)
    msg = "Nadie puede enviar mensajes." if bloqueado else "Ya pueden enviar mensajes."
    draw.text((144, 136), msg, font=fuente(13), fill=AZUL_OSCURO)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="lock.png")

async def generar_ship(usuario1: discord.Member, usuario2: discord.Member, porcentaje: int) -> discord.File:
    W, H = 680, 200
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    try:
        av1 = await descargar_imagen(str(usuario1.display_avatar.url))
        av1 = avatar_circular(av1, 110)
        img.paste(av1, (30, 45), av1)
    except:
        draw.ellipse([(30, 45), (140, 155)], fill=GRIS_G)
    draw.ellipse([(28, 43), (142, 157)], outline=AZUL_OSCURO, width=2)
    try:
        av2 = await descargar_imagen(str(usuario2.display_avatar.url))
        av2 = avatar_circular(av2, 110)
        img.paste(av2, (540, 45), av2)
    except:
        draw.ellipse([(540, 45), (650, 155)], fill=GRIS_G)
    draw.ellipse([(538, 43), (652, 157)], outline=AZUL_OSCURO, width=2)
    nombre1 = usuario1.display_name[:14] + "..." if len(usuario1.display_name) > 14 else usuario1.display_name
    nombre2 = usuario2.display_name[:14] + "..." if len(usuario2.display_name) > 14 else usuario2.display_name
    draw.text((85, 162),  nombre1, font=fuente(13, bold=True), fill=TEXTO_G, anchor="mt")
    draw.text((595, 162), nombre2, font=fuente(13, bold=True), fill=TEXTO_G, anchor="mt")
    draw.rounded_rectangle([(160, 82), (520, 118)], radius=18, fill=GRIS_G)
    fill_w = int(160 + (360 * porcentaje / 100))
    if fill_w > 160:
        draw.rounded_rectangle([(160, 82), (fill_w, 118)], radius=18, fill=AZUL_OSCURO)
    draw.text((340, 100), f"{porcentaje}%", font=fuente(20, bold=True), fill=TEXTO_G, anchor="mm")
    if porcentaje >= 90:   frase = "Almas gemelas de otra dimension"
    elif porcentaje >= 75: frase = "El amor es inevitable entre estos dos"
    elif porcentaje >= 60: frase = "Hay chispa, pero falta avivarlo"
    elif porcentaje >= 40: frase = "Podria funcionar... o no"
    elif porcentaje >= 20: frase = "Mejor como amigos"
    else:                  frase = "Incompatibles al maximo nivel"
    draw.text((340, 140), frase, font=fuente(12), fill=SUB_G, anchor="mt")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ship.png")

async def generar_spotify_search(tracks: list, query: str) -> discord.File:
    filas = min(len(tracks), 4)
    W, H  = 680, 110 + (filas * 80)
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    draw.rounded_rectangle([(24, 16), (656, 72)], radius=12, fill=(18, 18, 18))
    draw.rounded_rectangle([(24, 16), (656, 72)], radius=12, outline=GRIS_G, width=1)
    draw.text((42, 24), "Spotify Search", font=fuente(11), fill=SUB_G)
    query_texto = query[:55] + "..." if len(query) > 55 else query
    draw.text((42, 42), query_texto, font=fuente(15, bold=True), fill=TEXTO_G)
    draw.rectangle([(24, 86), (656, 87)], fill=GRIS_G)
    for n, track in enumerate(tracks[:4]):
        y = 96 + (n * 80)
        draw.rounded_rectangle([(24, y), (656, y + 68)], radius=10, fill=(20, 20, 20) if n % 2 == 0 else OSCU_G)
        draw.rounded_rectangle([(24, y), (656, y + 68)], radius=10, outline=GRIS_G, width=1)
        try:
            cover = await descargar_imagen(track["cover"])
            cover = cover.resize((52, 52)).convert("RGBA")
            mask  = Image.new("L", (52, 52), 0)
            ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (52, 52)], radius=6, fill=255)
            cover_r = Image.new("RGBA", (52, 52), (0, 0, 0, 0))
            cover_r.paste(cover, (0, 0), mask)
            img.paste(cover_r, (36, y + 8), cover_r)
        except:
            draw.rounded_rectangle([(36, y + 8), (88, y + 60)], radius=6, fill=GRIS_G)
        draw.text((100, y + 8), f"{n+1}.", font=fuente(12, bold=True), fill=AZUL_OSCURO)
        nombre  = track["nombre"][:38] + "..." if len(track["nombre"]) > 38 else track["nombre"]
        draw.text((118, y + 8), nombre, font=fuente(14, bold=True), fill=TEXTO_G)
        artista = track["artista"][:45] + "..." if len(track["artista"]) > 45 else track["artista"]
        draw.text((118, y + 30), artista, font=fuente(12), fill=BLANCO)
        draw.text((634, y + 28), track.get("duracion", ""), font=fuente(11), fill=SUB_G, anchor="ra")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="spotify_search.png")

async def generar_claves_list(usuario: discord.Member, claves: dict) -> discord.File:
    filas = min(len(claves), 8)
    W, H  = 680, 90 + (filas * 50)
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    draw.text((34, 24), f"Claves de {usuario.display_name}", font=fuente(18, bold=True), fill=TEXTO_G)
    draw.rectangle([(34, 44), (646, 45)], fill=GRIS_G)
    if not claves:
        draw.text((340, H//2), "No tienes claves configuradas", font=fuente(14), fill=SUB_G, anchor="mm")
    else:
        for n, (clave, mensaje) in enumerate(list(claves.items())[:8]):
            y = 54 + (n * 50)
            draw.rounded_rectangle([(34, y), (646, y + 38)], radius=8, fill=(26, 26, 26) if n % 2 == 0 else OSCU_G)
            draw.text((54, y + 8),  f" {clave}", font=fuente(12, bold=True), fill=AZUL_OSCURO)
            msg = mensaje[:45] + "..." if len(mensaje) > 45 else mensaje
            draw.text((54, y + 24), msg, font=fuente(10), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="claves_list.png")

async def generar_playlist_img(usuario: discord.Member, canciones: list) -> discord.File:
    filas = len(canciones)
    W, H  = 680, 110 + (filas * 46)
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    draw.text((34, 24), f"Playlist de {usuario.display_name}", font=fuente(18, bold=True), fill=TEXTO_G)
    draw.text((34, 52), f"Total: {filas}/15 canciones", font=fuente(11), fill=SUB_G)
    draw.rectangle([(34, 68), (646, 69)], fill=GRIS_G)
    for n, cancion in enumerate(canciones):
        y = 78 + (n * 46)
        color_fila = (26, 26, 26) if n % 2 == 0 else OSCU_G
        draw.rounded_rectangle([(34, y), (646, y + 36)], radius=8, fill=color_fila)
        draw.text((54, y + 10), f"#{n+1}", font=fuente(13, bold=True), fill=AZUL_OSCURO)
        texto_recortado = cancion[:50] + "..." if len(cancion) > 50 else cancion
        draw.text((90, y + 10), texto_recortado, font=fuente(13), fill=TEXTO_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="playlist.png")

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
        embed = discord.Embed(color=0x2B55B5)
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
        embed = discord.Embed(color=0x2B55B5)
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
        embed = discord.Embed(color=0x2B55B5)
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
    embed   = discord.Embed(title=f"Avatar de {usuario.name}", color=0x2B55B5)
    embed.set_image(url=usuario.display_avatar.url)
    await i.response.send_message(embed=embed)

@bot.command(name="avatar")
async def avatar_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    embed   = discord.Embed(title=f"Avatar de {usuario.name}", color=0x2B55B5)
    embed.set_image(url=usuario.display_avatar.url)
    await ctx.send(embed=embed)

@bot.tree.command(name="spotify", description="Muestra la musica que escucha un usuario")
async def spotify_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario   = i.guild.get_member((usuario or i.user).id)
    actividad = discord.utils.find(lambda a: isinstance(a, discord.Spotify), usuario.activities)
    if not actividad:
        await i.followup.send(f"> **{usuario.name} no esta escuchando Spotify**")
        return
    await i.followup.send(file=await generar_spotify(usuario, actividad))

@bot.command(name="spotify")
async def spotify_prefix(ctx, usuario: discord.Member = None):
    usuario   = await get_member_from_ctx(ctx, usuario)
    actividad = discord.utils.find(lambda a: isinstance(a, discord.Spotify), usuario.activities)
    if not actividad:
        await ctx.send(f"**{usuario.display_name} no esta escuchando Spotify**")
        return
    await ctx.send(file=await generar_spotify(usuario, actividad))

@bot.tree.command(name="nivel", description="Ve tu nivel actual")
async def nivel_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    data    = get_xp(i.guild.id, usuario.id)
    await i.followup.send(file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.command(name="nivel")
async def nivel_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    data    = get_xp(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.tree.command(name="balance", description="Ve tu cuenta bancaria")
async def balance_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    data    = get_user_eco(i.guild.id, usuario.id)
    await i.followup.send(file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.command(name="balance")
async def balance_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    data    = get_user_eco(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.tree.command(name="daily", description="Reclama tus monedas diarias")
async def daily_slash(i: discord.Interaction):
    await i.response.defer()
    data  = get_user_eco(i.guild.id, i.user.id)
    ahora = time.time()
    if ahora - data["last_daily"] < 86400:
        restante = int(86400 - (ahora - data["last_daily"]))
        h, m, s  = restante // 3600, (restante % 3600) // 60, restante % 60
        await i.followup.send(f"> Vuelve en `{h:02}:{m:02}:{s:02}`", ephemeral=True)
        return
    recompensa        = random.randint(100, 500)
    data["coins"]    += recompensa
    data["last_daily"] = ahora
    await i.followup.send(content=f"> Recibiste **{recompensa}** monedas!", file=await generar_balance(i.guild.get_member(i.user.id), data["coins"], data["last_daily"]))

@bot.command(name="daily")
async def daily_prefix(ctx):
    data  = get_user_eco(ctx.guild.id, ctx.author.id)
    ahora = time.time()
    if ahora - data["last_daily"] < 86400:
        restante = int(86400 - (ahora - data["last_daily"]))
        h, m, s  = restante // 3600, (restante % 3600) // 60, restante % 60
        await ctx.send(f"> Vuelve en `{h:02}:{m:02}:{s:02}`")
        return
    recompensa        = random.randint(100, 500)
    data["coins"]    += recompensa
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
    usuario  = await get_member_from_ctx(ctx, usuario)
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
    usuario  = await get_member_from_ctx(ctx, usuario)
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
    embed = discord.Embed(color=0x2B55B5)
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
    await nuevo.send(embed=discord.Embed(title="Canal Nukeado", description="> Canal purificado exitosamente.", color=0x2B55B5))

@bot.command(name="nuke")
@commands.has_permissions(manage_channels=True)
async def nuke_prefix(ctx):
    canal = ctx.channel
    nuevo = await canal.clone()
    await canal.delete()
    await nuevo.send(embed=discord.Embed(title="Canal Nukeado", description="> Canal purificado exitosamente.", color=0x2B55B5))

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
    ms    = round(bot.latency * 1000)
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Pong! `{ms}ms`"
    await i.response.send_message(embed=embed)

@bot.command(name="ping")
async def ping_prefix(ctx):
    ms    = round(bot.latency * 1000)
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Pong! `{ms}ms`"
    await ctx.send(embed=embed)

@bot.tree.command(name="moneda", description="Tira una moneda")
async def moneda_slash(i: discord.Interaction):
    resultado = random.choice(["Cara", "Cruz"])
    embed     = discord.Embed(color=0x2B55B5)
    embed.description = f"> Resultado: **{resultado}**"
    await i.response.send_message(embed=embed)

@bot.command(name="moneda")
async def moneda_prefix(ctx):
    resultado = random.choice(["Cara", "Cruz"])
    embed     = discord.Embed(color=0x2B55B5)
    embed.description = f"> Resultado: **{resultado}**"
    await ctx.send(embed=embed)

@bot.tree.command(name="dado", description="Tira un dado de N caras")
async def dado_slash(i: discord.Interaction, caras: int = 6):
    resultado = random.randint(1, caras)
    embed     = discord.Embed(color=0x2B55B5)
    embed.description = f"> Dado de {caras} caras: **{resultado}**"
    await i.response.send_message(embed=embed)

@bot.command(name="dado")
async def dado_prefix(ctx, caras: int = 6):
    resultado = random.randint(1, caras)
    embed     = discord.Embed(color=0x2B55B5)
    embed.description = f"> Dado de {caras} caras: **{resultado}**"
    await ctx.send(embed=embed)

# =========================================================
# SISTEMA DE CLAVES
# =========================================================

@bot.tree.command(name="clave", description="Crea una clave personalizada")
async def clave_slash(i: discord.Interaction, clave: str, mensaje: str):
    await i.response.defer()
    gid         = str(i.guild.id)
    claves      = get_user_claves(gid, i.user.id)
    clave_lower = clave.lower()
    if clave_lower in claves:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"> La clave **{clave}** ya existe\n> Usa `/clave-delete` para eliminarla primero"
        await i.followup.send(embed=embed)
        return
    claves[clave_lower] = mensaje
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Clave **{clave}** creada exitosamente\n> Respuesta: `{mensaje}`"
    await i.followup.send(embed=embed)

@bot.command(name="clave")
async def clave_prefix(ctx, clave: str, *, mensaje: str):
    gid         = str(ctx.guild.id)
    claves      = get_user_claves(gid, ctx.author.id)
    clave_lower = clave.lower()
    if clave_lower in claves:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"> La clave **{clave}** ya existe\n> Usa `>mt clave-delete` para eliminarla primero"
        await ctx.send(embed=embed)
        return
    claves[clave_lower] = mensaje
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Clave **{clave}** creada exitosamente\n> Respuesta: `{mensaje}`"
    await ctx.send(embed=embed)

@bot.tree.command(name="clave-list", description="Ver todas tus claves configuradas")
async def clave_list_slash(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario     = usuario or i.user
    gid         = str(i.guild.id)
    claves      = get_user_claves(gid, usuario.id)
    usuario_obj = i.guild.get_member(usuario.id)
    await i.followup.send(file=await generar_claves_list(usuario_obj, claves))

@bot.command(name="clave-list")
async def clave_list_prefix(ctx, usuario: discord.Member = None):
    usuario = await get_member_from_ctx(ctx, usuario)
    gid     = str(ctx.guild.id)
    claves  = get_user_claves(gid, usuario.id)
    await ctx.send(file=await generar_claves_list(usuario, claves))

@bot.tree.command(name="clave-delete", description="Elimina una clave")
async def clave_delete_slash(i: discord.Interaction, clave: str):
    await i.response.defer()
    gid         = str(i.guild.id)
    claves      = get_user_claves(gid, i.user.id)
    clave_lower = clave.lower()
    if clave_lower not in claves:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"> La clave **{clave}** no existe"
        await i.followup.send(embed=embed)
        return
    del claves[clave_lower]
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Clave **{clave}** eliminada exitosamente"
    await i.followup.send(embed=embed)

@bot.command(name="clave-delete")
async def clave_delete_prefix(ctx, clave: str):
    gid         = str(ctx.guild.id)
    claves      = get_user_claves(gid, ctx.author.id)
    clave_lower = clave.lower()
    if clave_lower not in claves:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"> La clave **{clave}** no existe"
        await ctx.send(embed=embed)
        return
    del claves[clave_lower]
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Clave **{clave}** eliminada exitosamente"
    await ctx.send(embed=embed)

# =========================================================
# WELC / BYE
# =========================================================

@bot.tree.command(name="welc", description="Configura el mensaje de bienvenida")
@app_commands.checks.has_permissions(administrator=True)
async def welc(i: discord.Interaction, canal: discord.TextChannel, titulo: str = None, descripcion: str = None, color: str = None, autor: str = None, autor_imagen: str = None, imagen: str = None, footer: str = None, footer_imagen: str = None):
    try:
        color_final = int(color.replace("#", ""), 16) if color else 0x2B55B5
    except:
        color_final = 0x2B55B5
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
        color_final = int(color.replace("#", ""), 16) if color else 0x2B55B5
    except:
        color_final = 0x2B55B5
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
        color_final = int(color.replace("#", ""), 16) if color else 0x2B55B5
    except:
        color_final = 0x2B55B5
    embed = discord.Embed(title=titulo or "", description=descripcion or "", color=color_final)
    if imagen:       embed.set_image(url=imagen)
    if footer_texto: embed.set_footer(text=footer_texto)
    if autor_nombre: embed.set_author(name=autor_nombre)
    await canal.send(embed=embed)
    await i.response.send_message("Embed enviado", ephemeral=True)

# =========================================================
# SPOTIFY SEARCH
# =========================================================

async def buscar_spotify(query: str) -> list:
    url     = "https://spotify23.p.rapidapi.com/search/"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": "spotify23.p.rapidapi.com"}
    params  = {"q": query, "type": "tracks", "limit": "4", "offset": "0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as r:
            data = await r.json()
    tracks = []
    for item in data.get("tracks", {}).get("items", [])[:4]:
        track     = item.get("data", {})
        nombre    = track.get("name", "Sin nombre")
        artista   = ", ".join([a.get("profile", {}).get("name", "") for a in track.get("artists", {}).get("items", [])])
        covers    = track.get("albumOfTrack", {}).get("coverArt", {}).get("sources", [])
        cover     = covers[0].get("url", "") if covers else ""
        ms        = track.get("duration", {}).get("totalMilliseconds", 0)
        seg       = ms // 1000
        duracion  = f"{seg // 60}:{seg % 60:02}"
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
            self.add_item(discord.ui.Button(label=f"{n+1}. {nombre}", url=track["url"], style=discord.ButtonStyle.link, emoji="<:music:1504691247619641404>"))

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
async def roblox_prefix(ctx: commands.Context, usuario: str):
    if ctx.interaction:
        await ctx.defer()
    try:
        async with aiohttp.ClientSession() as session:
            data_user = {"usernames": [usuario], "excludeBannedUsers": False}
            async with session.post("https://users.roblox.com/v1/usernames/users", json=data_user) as resp:
                if resp.status != 200:
                    embed = discord.Embed(color=0x2B55B5)
                    embed.description = "> Error al conectar con la API de Roblox"
                    if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
                    else: await ctx.send(embed=embed)
                    return
                res_user = await resp.json()
                if not res_user["data"]:
                    embed = discord.Embed(color=0x2B55B5)
                    embed.description = f"> El usuario **{usuario}** no existe en Roblox"
                    if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
                    else: await ctx.send(embed=embed)
                    return
                user_info    = res_user["data"][0]
                user_id      = user_info["id"]
                roblox_user  = user_info["name"]
                display_name = user_info["displayName"]
            async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as resp:
                res_details  = await resp.json()
                fecha_iso    = res_details["created"].split("T")[0]
                fecha_obj    = datetime.strptime(fecha_iso, "%Y-%m-%d")
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
        embed = discord.Embed(color=0x2B55B5, title="Perfil de Roblox")
        embed.add_field(name="Usuario",        value=roblox_user,    inline=True)
        embed.add_field(name="ID",             value=user_id,        inline=True)
        embed.add_field(name="Apodo",          value=display_name,   inline=False)
        embed.add_field(name="Cuenta Creada",  value=cuenta_creada,  inline=True)
        embed.add_field(name="Amigos",         value=cantidad_amigos, inline=True)
        embed.add_field(name="Perfil",         value=f"[ver]({perfil_link})", inline=False)
        embed.set_thumbnail(url=avatar_url)
        if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
        else: await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"Error: {str(e)}"
        if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
        else: await ctx.send(embed=embed)

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
        color=cfg.get("color", 0x2B55B5)
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
        color=cfg.get("color", 0x2B55B5)
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
    uid   = message.author.id
    ahora = time.time()
    if ahora - xp_cooldown.get(uid, 0) < 120:
        return
    xp_cooldown[uid] = ahora
    data             = get_xp(message.guild.id, uid)
    data["xp"]      += random.randint(10, 20)
    xp_needed        = xp_para_nivel(data["level"])
    if data["xp"] >= xp_needed:
        data["xp"]    -= xp_needed
        data["level"] += 1
        canal_id = nivel_canal.get(message.guild.id)
        canal    = message.guild.get_channel(canal_id) if canal_id else message.channel
        try:
            await canal.send(content=message.author.mention, file=await generar_nivel(message.author, data["level"], data["xp"], xp_para_nivel(data["level"])))
        except Exception as e:
            print(f"Error nivel: {e}")

# =========================================================
# ADMIN COMMANDS - XP / DINERO
# =========================================================

@bot.tree.command(name="add-nivel", description="Agregar niveles a un usuario (ADMIN)")
@app_commands.checks.has_permissions(administrator=True)
async def add_nivel_slash(i: discord.Interaction, usuario: discord.Member, cantidad: int):
    await i.response.defer()
    data = get_xp(i.guild.id, usuario.id)
    data["level"] += cantidad
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Se agregaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await i.followup.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.command(name="add-nivel")
@commands.has_permissions(administrator=True)
async def add_nivel_prefix(ctx, usuario: discord.Member, cantidad: int):
    data = get_xp(ctx.guild.id, usuario.id)
    data["level"] += cantidad
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Se agregaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await ctx.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.tree.command(name="remove-nivel", description="Quitar niveles a un usuario (ADMIN)")
@app_commands.checks.has_permissions(administrator=True)
async def remove_nivel_slash(i: discord.Interaction, usuario: discord.Member, cantidad: int):
    await i.response.defer()
    data = get_xp(i.guild.id, usuario.id)
    data["level"] = max(1, data["level"] - cantidad)
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Se quitaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await i.followup.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.command(name="remove-nivel")
@commands.has_permissions(administrator=True)
async def remove_nivel_prefix(ctx, usuario: discord.Member, cantidad: int):
    data = get_xp(ctx.guild.id, usuario.id)
    data["level"] = max(1, data["level"] - cantidad)
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Se quitaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await ctx.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.tree.command(name="add-dinero", description="Agregar dinero a un usuario (ADMIN)")
@app_commands.checks.has_permissions(administrator=True)
async def add_dinero_slash(i: discord.Interaction, usuario: discord.Member, cantidad: int):
    await i.response.defer()
    data = get_user_eco(i.guild.id, usuario.id)
    data["coins"] += cantidad
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Se agregaron **${cantidad:,}** monedas a {usuario.mention}\n> Dinero actual: **${data['coins']:,}**"
    await i.followup.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.command(name="add-dinero")
@commands.has_permissions(administrator=True)
async def add_dinero_prefix(ctx, usuario: discord.Member, cantidad: int):
    data = get_user_eco(ctx.guild.id, usuario.id)
    data["coins"] += cantidad
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Se agregaron **${cantidad:,}** monedas a {usuario.mention}\n> Dinero actual: **${data['coins']:,}**"
    await ctx.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.tree.command(name="remove-dinero", description="Quitar dinero a un usuario (ADMIN)")
@app_commands.checks.has_permissions(administrator=True)
async def remove_dinero_slash(i: discord.Interaction, usuario: discord.Member, cantidad: int):
    await i.response.defer()
    data = get_user_eco(i.guild.id, usuario.id)
    data["coins"] = max(0, data["coins"] - cantidad)
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Se quitaron **${cantidad:,}** monedas a {usuario.mention}\n> Dinero actual: **${data['coins']:,}**"
    await i.followup.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.command(name="remove-dinero")
@commands.has_permissions(administrator=True)
async def remove_dinero_prefix(ctx, usuario: discord.Member, cantidad: int):
    data = get_user_eco(ctx.guild.id, usuario.id)
    data["coins"] = max(0, data["coins"] - cantidad)
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Se quitaron **${cantidad:,}** monedas a {usuario.mention}\n> Dinero actual: **${data['coins']:,}**"
    await ctx.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

# =========================================================
# YOUTUBE
# =========================================================

@bot.hybrid_command(name="youtube", description="busca un video en youtube")
async def reproducir(ctx, *, busqueda: str):
    await ctx.defer() if ctx.interaction else None
    try:
        url     = "https://www.youtube.com/youtubei/v1/search?key=AIzaSyAO90d0o_cqFbnSa2Bx0-Dmp5BaM9aW0uM"
        payload = {
            "context": {"client": {"clientName": "WEB", "clientVersion": "2.20230101.00.00"}},
            "query":   busqueda,
            "params":  "EgIQAQ%3D%3D"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    data     = await resp.json()
                    contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
                    if contents and 'itemSectionRenderer' in contents[0]:
                        videos = contents[0]['itemSectionRenderer']['contents']
                        if videos:
                            v         = videos[0].get('videoRenderer', {})
                            titulo    = v.get('title', {}).get('runs', [{}])[0].get('text', 'Sin titulo')
                            video_id  = v.get('videoId', '')
                            duracion  = v.get('lengthText', {}).get('simpleText', '0:00')
                            canal     = v.get('longBylineText', {}).get('runs', [{}])[0].get('text', 'Desconocido')
                            thumbnail = v.get('thumbnail', {}).get('thumbnails', [{}])[-1].get('url', '')
                            vistas    = v.get('viewCountText', {}).get('simpleText', '0 vistas')
                            url_video = f"https://www.youtube.com/watch?v={video_id}"
                            embed = discord.Embed(color=0x2B55B5, title="Video Encontrado")
                            embed.add_field(name="> Titulo",   value=titulo[:100], inline=False)
                            embed.add_field(name="> Duracion", value=duracion,     inline=True)
                            embed.add_field(name="> Canal",    value=canal[:50],   inline=True)
                            embed.add_field(name="> Vistas",   value=vistas,       inline=True)
                            embed.add_field(name="> Link",     value=f"[Abrir en YouTube]({url_video})", inline=False)
                            if thumbnail: embed.set_thumbnail(url=thumbnail)
                            embed.set_footer(text=f"Solicitado por {ctx.author.name}")
                            if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
                            else: await ctx.send(embed=embed)
                            return
        embed = discord.Embed(color=0x2B55B5)
        embed.description = "> No se encontraron resultados"
        if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
        else: await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"```{str(e)[:200]}```"
        if ctx.interaction: await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else: await ctx.send(embed=embed)

# =========================================================
# LYRICS
# =========================================================

@bot.hybrid_command(name="lyrics", description="Obtén la letra de una cancion")
async def lyrics(ctx, *, cancion: str):
    await ctx.defer() if ctx.interaction else None
    try:
        url = f"https://lrclib.net/api/search?q={cancion.replace(' ', '+')}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Error {resp.status}")
                data = await resp.json()
        if not data:
            embed = discord.Embed(color=0x2B55B5)
            embed.description = "> No se encontraron resultados para esa cancion."
            if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
            else: await ctx.send(embed=embed)
            return
        resultado = data[0]
        nombre    = resultado.get("trackName", "Sin nombre")
        artista   = resultado.get("artistName", "Desconocido")
        album     = resultado.get("albumName", "")
        letra     = resultado.get("plainLyrics") or resultado.get("syncedLyrics") or "Letra no disponible"
        if letra and letra.startswith("["):
            import re
            letra = re.sub(r'\[\d+:\d+\.\d+\]', '', letra).strip()
        if len(letra) > 4096:
            letra = letra[:4000] + "\n\n*[Letra cortada]*"
        embed = discord.Embed(title=nombre, description=letra, color=0x2B55B5)
        embed.set_author(name=artista)
        if album: embed.set_footer(text=f"Album: {album}")
        if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
        else: await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"> Error: `{str(e)[:100]}`"
        if ctx.interaction: await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else: await ctx.send(embed=embed)

# =========================================================
# BUSCAR LIBRO
# =========================================================

@bot.hybrid_command(name="buscar-libro", description="Busca información de un libro en Google Books")
async def buscar_libro(ctx: commands.Context, *, query: str):
    await ctx.defer() if ctx.interaction else None
    
    query_encoded = urllib.parse.quote(query)
    url = f"https://www.googleapis.com/books/v1/volumes?q={query_encoded}&maxResults=1"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 429:
                    embed = discord.Embed(
                        description="> Limite de busquedas alcanzado. Espera unos minutos.",
                        color=AZUL_IPOD_NUM
                    )
                    return await ctx.send(embed=embed)
                
                if response.status != 200:
                    embed = discord.Embed(
                        description=f"> Error de conexion ({response.status})",
                        color=AZUL_IPOD_NUM
                    )
                    return await ctx.send(embed=embed)
                
                data = await response.json()
        
        if "items" not in data:
            embed = discord.Embed(
                description=f"> No encontre ningun libro para: **{query}**",
                color=AZUL_IPOD_NUM
            )
            return await ctx.send(embed=embed)
        
        # Extraer datos del libro
        info = data["items"][0]["volumeInfo"]
        
        titulo = info.get("title", "Sin titulo")
        autores = ", ".join(info.get("authors", ["Desconocido"]))
        
        # Descripción
        raw_desc = info.get("description", "Sin descripcion disponible.")
        descripcion = (raw_desc[:500] + "...") if len(raw_desc) > 500 else raw_desc
        
        fecha = info.get("publishedDate", "Desconocida")
        paginas = info.get("pageCount", "N/A")
        
        # Categorías/géneros
        categorias = ", ".join(info.get("categories", ["Sin categoria"]))
        
        # Editorial
        editorial = info.get("publisher", "Desconocida")
        
        # Idioma
        idioma = info.get("language", "Desconocido")
        if idioma == "es":
            idioma = "Español"
        elif idioma == "en":
            idioma = "Inglés"
        elif idioma == "fr":
            idioma = "Francés"
        elif idioma == "pt":
            idioma = "Portugués"
        elif idioma == "de":
            idioma = "Alemán"
        
        # Portada
        portada = info.get("imageLinks", {}).get("thumbnail", "")
        if portada:
            portada = portada.replace("http://", "https://")
        
        # Enlace para comprar/ver
        enlace = info.get("infoLink", "")
        
        # Crear embed
        embed = discord.Embed(
            title=f"{titulo}",
            description=descripcion,
            color=AZUL_IPOD_NUM,
            url=enlace
        )
        embed.add_field(name="> Autor(es)", value=autores, inline=False)
        embed.add_field(name="> Publicacion", value=fecha, inline=True)
        embed.add_field(name="> Paginas", value=str(paginas), inline=True)
        embed.add_field(name="> Editorial", value=editorial, inline=True)
        embed.add_field(name="> Idioma", value=idioma, inline=True)
        embed.add_field(name="> Categorias", value=categorias[:50], inline=False)
        
        if portada:
            embed.set_thumbnail(url=portada)
        
        embed.set_footer(
            text=f"Solicitado por {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)
        
    except asyncio.TimeoutError:
        embed = discord.Embed(
            description="> Tiempo de espera agotado. Intenta de nuevo.",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            description=f"> Error inesperado: `{str(e)[:100]}`",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

# =========================================================
# TRIVIA
# =========================================================

PREGUNTAS_TRIVIA = [
    {"pregunta": "Cual es la capital de Francia?",               "respuestas": ["Paris", "Londres", "Berlin"],           "correcta": 0},
    {"pregunta": "Cual es el planeta mas grande?",               "respuestas": ["Jupiter", "Saturno", "Tierra"],         "correcta": 0},
    {"pregunta": "En que año termino la 2da Guerra Mundial?",    "respuestas": ["1943", "1944", "1945"],                  "correcta": 2},
    {"pregunta": "Cual es el elemento quimico con simbolo Au?",  "respuestas": ["Plata", "Oro", "Aluminio"],             "correcta": 1},
    {"pregunta": "Quien escribio Don Quijote?",                  "respuestas": ["Borges", "Cervantes", "Garcia Marquez"], "correcta": 1},
]

puntuaciones_trivia = {}

class TriviaView(discord.ui.View):
    def __init__(self, pregunta_data, user_id):
        super().__init__(timeout=30)
        self.pregunta_data = pregunta_data
        self.user_id       = user_id
        self.respondio     = False
        for n, respuesta in enumerate(pregunta_data['respuestas']):
            button          = discord.ui.Button(label=respuesta, style=discord.ButtonStyle.primary, custom_id=f"trivia_{n}")
            button.callback = self.responder
            self.add_item(button)

    async def responder(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Esta no es tu trivia", ephemeral=True)
            return
        if self.respondio:
            return
        self.respondio    = True
        respuesta_num     = int(interaction.data['custom_id'].split('_')[1])
        correcta          = respuesta_num == self.pregunta_data['correcta']
        gid, uid          = str(interaction.guild.id), str(self.user_id)
        if gid not in puntuaciones_trivia: puntuaciones_trivia[gid] = {}
        if uid not in puntuaciones_trivia[gid]: puntuaciones_trivia[gid][uid] = 0
        if correcta:
            puntuaciones_trivia[gid][uid] += 10
            embed = discord.Embed(color=0x2B55B5)
            embed.description = "> Correcto! +10 puntos"
        else:
            embed = discord.Embed(color=0x2B55B5)
            embed.description = f"> Incorrecto! La respuesta era: **{self.pregunta_data['respuestas'][self.pregunta_data['correcta']]}**"
        embed.add_field(name="Puntos Totales", value=puntuaciones_trivia[gid][uid])
        await interaction.response.edit_message(embed=embed, view=None)

@bot.hybrid_command(name="trivia", description="Juega una trivia")
async def trivia(ctx):
    pregunta_data = random.choice(PREGUNTAS_TRIVIA)
    embed         = discord.Embed(color=0x2B55B5, title="Trivia")
    embed.description = pregunta_data['pregunta']
    await ctx.send(embed=embed, view=TriviaView(pregunta_data, ctx.author.id))

@bot.hybrid_command(name="mi-puntuacion-trivia", description="Ver tu puntuacion en trivia")
async def mi_puntuacion_trivia(ctx):
    puntos = puntuaciones_trivia.get(str(ctx.guild.id), {}).get(str(ctx.author.id), 0)
    embed  = discord.Embed(color=0x2B55B5, title="Tu Puntuacion de Trivia")
    embed.description = f"> Puntos: **{puntos}**"
    await ctx.send(embed=embed)

# =========================================================
# COMANDOS UTILES
# =========================================================

@bot.hybrid_command(name="calcular", description="Calcula una operacion matematica")
async def calcular(ctx, *, operacion: str):
    try:
        resultado = eval(operacion)
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"> **Operacion:** {operacion}\n> **Resultado:** {resultado}"
        await ctx.send(embed=embed)
    except:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = "> Operacion invalida"
        await ctx.send(embed=embed, ephemeral=True if ctx.interaction else None)

@bot.hybrid_command(name="generar-password", description="Genera una contrasena segura")
async def generar_password(ctx, longitud: int = 16):
    import string
    password = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(longitud))
    embed    = discord.Embed(color=0x2B55B5)
    embed.description = f"> Contrasena: `{password}`"
    await ctx.send(embed=embed, ephemeral=True if ctx.interaction else None)

@bot.hybrid_command(name="base64-codificar", description="Codifica un texto en base64")
async def base64_codificar(ctx, *, texto: str):
    import base64
    codificado = base64.b64encode(texto.encode()).decode()
    embed = discord.Embed(color=0x2B55B5)
    embed.add_field(name="Original", value=texto,              inline=False)
    embed.add_field(name="Base64",   value=f"`{codificado}`", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="base64-decodificar", description="Decodifica un texto base64")
async def base64_decodificar(ctx, *, texto: str):
    try:
        import base64
        decodificado = base64.b64decode(texto).decode()
        embed = discord.Embed(color=0x2B55B5)
        embed.add_field(name="Base64",   value=texto,        inline=False)
        embed.add_field(name="Original", value=decodificado, inline=False)
        await ctx.send(embed=embed)
    except:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = "> Texto base64 invalido"
        await ctx.send(embed=embed, ephemeral=True if ctx.interaction else None)

# =========================================================
# MINIJUEGOS
# =========================================================

@bot.hybrid_command(name="adivina-numero", description="Adivina un numero del 1 al 100")
async def adivina_numero(ctx):
    numero_secreto = random.randint(1, 100)
    embed          = discord.Embed(color=0x2B55B5, title="Adivina el Numero")
    embed.description = "> Piensa un numero entre 1 y 100. Tienes 10 intentos"
    await ctx.send(embed=embed)
    def check(m): return m.author == ctx.author and ctx.channel == m.channel
    for intento in range(10):
        try:
            mensaje = await bot.wait_for('message', check=check, timeout=60)
            numero  = int(mensaje.content)
            if numero == numero_secreto:
                embed = discord.Embed(color=0x2B55B5)
                embed.description = f"> Correcto! El numero era **{numero_secreto}**\n> Intentaste **{intento + 1}** veces"
                await ctx.send(embed=embed)
                return
            elif numero < numero_secreto:
                embed = discord.Embed(color=0x2B55B5)
                embed.description = f"> El numero es **mayor** ({intento + 1}/10)"
            else:
                embed = discord.Embed(color=0x2B55B5)
                embed.description = f"> El numero es **menor** ({intento + 1}/10)"
            await ctx.send(embed=embed)
        except (ValueError, asyncio.TimeoutError):
            break
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Se acabaron los intentos! El numero era **{numero_secreto}**"
    await ctx.send(embed=embed)

@bot.hybrid_command(name="ppt", description="Piedra papel o tijera")
async def ppt_mejorado(ctx):
    opciones = ["Piedra", "Papel", "Tijera"]
    async def ppt_seleccionar(interaction: discord.Interaction, opcion_usuario: str):
        opcion_bot = random.choice(opciones)
        if opcion_usuario == opcion_bot:
            resultado = "EMPATE"
        elif (opcion_usuario == "Piedra" and opcion_bot == "Tijera") or \
             (opcion_usuario == "Papel"  and opcion_bot == "Piedra") or \
             (opcion_usuario == "Tijera" and opcion_bot == "Papel"):
            resultado = "GANASTE"
        else:
            resultado = "PERDISTE"
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"> Tu: **{opcion_usuario}**\n> Bot: **{opcion_bot}**\n> **{resultado}**"
        await interaction.response.send_message(embed=embed, ephemeral=True)
    view = discord.ui.View()
    for opcion in opciones:
        button          = discord.ui.Button(label=opcion, style=discord.ButtonStyle.primary)
        button.callback = lambda interaction, op=opcion: ppt_seleccionar(interaction, op)
        view.add_item(button)
    embed = discord.Embed(color=0x2B55B5, title="Piedra, Papel o Tijera")
    embed.description = "> Elige tu opcion"
    await ctx.send(embed=embed, view=view)

@bot.hybrid_command(name="ahorcado", description="Juega al ahorcado")
async def ahorcado(ctx):
    palabras           = ["frutas", "mantequilla", "computadora", "celular", "pais", "diva", "musica", "discord", "python", "servidor"]
    palabra_secreta    = random.choice(palabras).upper()
    letras_adivinadas  = set()
    intentos           = 6
    def mostrar_palabra():
        return ' '.join([l if l in letras_adivinadas else '_' for l in palabra_secreta])
    embed = discord.Embed(color=0x2B55B5, title="Ahorcado")
    embed.description = f"> `{mostrar_palabra()}`\n> Intentos: **{intentos}**"
    await ctx.send(embed=embed)
    def check(m): return m.author == ctx.author and ctx.channel == m.channel and len(m.content) == 1
    while intentos > 0 and set(palabra_secreta) != letras_adivinadas:
        try:
            mensaje = await bot.wait_for('message', check=check, timeout=60)
            letra   = mensaje.content.upper()
            if letra in letras_adivinadas:
                embed = discord.Embed(color=0x2B55B5)
                embed.description = "> Ya adivinaste esa letra"
                await ctx.send(embed=embed)
                continue
            letras_adivinadas.add(letra)
            if letra not in palabra_secreta:
                intentos -= 1
            embed = discord.Embed(color=0x2B55B5)
            embed.description = f"> `{mostrar_palabra()}`\n> Intentos: **{intentos}**"
            await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            break
    embed = discord.Embed(color=0x2B55B5)
    if set(palabra_secreta) == letras_adivinadas:
        embed.description = f"> GANASTE! La palabra era: **{palabra_secreta}**"
    else:
        embed.description = f"> PERDISTE! La palabra era: **{palabra_secreta}**"
    await ctx.send(embed=embed)

# =========================================================
# CUPONES
# =========================================================

cupones_data = {}

@bot.hybrid_command(name="crear-cupon", description="Crea un cupon (ADMIN)")
@commands.has_permissions(administrator=True)
async def crear_cupon(ctx, codigo: str, recompensa: int):
    gid = str(ctx.guild.id)
    if gid not in cupones_data: cupones_data[gid] = {}
    cupones_data[gid][codigo.upper()] = {"recompensa": recompensa, "usado_por": []}
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Cupon `{codigo.upper()}` creado\n> Recompensa: **${recompensa:,}**"
    await ctx.send(embed=embed)

@bot.hybrid_command(name="canjear-cupon", description="Canjea un cupon")
async def canjear_cupon(ctx, codigo: str):
    gid = str(ctx.guild.id)
    if gid not in cupones_data or codigo.upper() not in cupones_data[gid]:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = "> Cupon invalido"
        await ctx.send(embed=embed, ephemeral=True if ctx.interaction else None)
        return
    cupon = cupones_data[gid][codigo.upper()]
    if ctx.author.id in cupon["usado_por"]:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = "> Ya usaste este cupon"
        await ctx.send(embed=embed, ephemeral=True if ctx.interaction else None)
        return
    cupon["usado_por"].append(ctx.author.id)
    eco = get_user_eco(ctx.guild.id, ctx.author.id)
    eco["coins"] += cupon["recompensa"]
    embed = discord.Embed(color=0x2B55B5)
    embed.description = f"> Cupon canjeado! Ganaste: **${cupon['recompensa']:,}**"
    await ctx.send(embed=embed)

# =========================================================
# DOCTOR
# =========================================================

@bot.hybrid_command(name="doctor", description="Verifica si el bot tiene activos todos los permisos necesarios.")
async def doctor(ctx: commands.Context):
    await ctx.defer()
    guild = ctx.guild
    me    = guild.me if guild else None
    if not me:
        embed = discord.Embed(title="Doctor - Diagnóstico", description="**Este comando solo puede ser ejecutado dentro de un servidor.**", color=0x2B55B5)
        return await ctx.send(embed=embed)
    channel_permissions = ctx.channel.permissions_for(me)
    permisos_canal = {
        "Ver Canal (Read Messages)":              channel_permissions.view_channel,
        "Enviar Mensajes (Send Messages)":        channel_permissions.send_messages,
        "Crear Embeds (Embed Links)":             channel_permissions.embed_links,
        "Adjuntar Archivos (Attach Files)":       channel_permissions.attach_files,
        "Usar Emojis Externos (External Emojis)": channel_permissions.use_external_emojis,
        "Añadir Reacciones (Add Reactions)":      channel_permissions.add_reactions,
        "Leer Historial (Read Message History)":  channel_permissions.read_message_history,
    }
    guild_permissions = me.guild_permissions
    permisos_servidor = {
        "Administrador (Administrator)":        guild_permissions.administrator,
        "Gestionar Mensajes (Manage Messages)": guild_permissions.manage_messages,
        "Gestionar Canales (Manage Channels)":  guild_permissions.manage_channels,
        "Gestionar Roles (Manage Roles)":       guild_permissions.manage_roles,
        "Expulsar Miembros (Kick Members)":     guild_permissions.kick_members,
        "Banear Miembros (Ban Members)":        guild_permissions.ban_members,
        "Silenciar Miembros (Mute Members)":    guild_permissions.mute_members,
    }
    def formatear_permisos(lista_permisos):
        texto = ""
        for nombre, activo in lista_permisos.items():
            emoji  = "<:Check:1504584129302499399>" if activo else "<:fail:1504584129302499399>"
            texto += f"{emoji} **{nombre}**\n"
        return texto
    embed = discord.Embed(title="Diagnóstico de Salud del Bot", description="Estado de permisos del bot.", color=0x2B55B5)
    embed.add_field(name="Permisos en este Canal",       value=formatear_permisos(permisos_canal),    inline=False)
    embed.add_field(name="Permisos Globales (Servidor)", value=formatear_permisos(permisos_servidor), inline=False)
    errores_canal = [k for k, v in permisos_canal.items() if not v]
    if me.guild_permissions.administrator:
        diagnostico = "> **Diagnóstico:** El bot tiene el permiso de **Administrador**. Todos los sistemas operan sin restricciones."
    elif not errores_canal:
        diagnostico = "> **Diagnóstico:** ¡Excelente! El bot cuenta con todos los permisos fundamentales."
    else:
        diagnostico = f"> **Diagnóstico:** Al bot le faltan permisos clave: **{', '.join(errores_canal[:2])}**"
    embed.add_field(name="Conclusión Médica", value=diagnostico, inline=False)
    embed.set_footer(text=f"Misti Doctor • Latencia: {round(bot.latency * 1000)}ms", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# =========================================================
# IPOD PLAYER
# =========================================================

async def generar_ipod_player_img(cancion: str, artista: str, duracion: str, progreso_pct: int) -> discord.File:
    W, H = 340, 500
    PANTALLA_FONDO = (173, 232, 244)
    PANTALLA_TEXTO = (3, 4, 94)
    img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(10, 10), (W - 10, H - 10)], radius=30, fill=AZUL_IPOD)
    draw.rounded_rectangle([(10, 10), (W - 10, H - 10)], radius=30, outline=BLANCO, width=2)
    draw.rounded_rectangle([(30, 30), (W - 30, 210)],    radius=10, fill=PANTALLA_FONDO)
    draw.rounded_rectangle([(30, 30), (W - 30, 210)],    radius=10, outline=(100, 200, 255), width=2)
    draw.text((45, 45), "Ahora Sonando", font=fuente(12, bold=True), fill=(10, 50, 120))
    titulo_recortado  = cancion[:20] + "..." if len(cancion) > 20 else cancion
    artista_recortado = artista[:24] + "..." if len(artista) > 24 else artista
    draw.text((45, 75),  titulo_recortado,  font=fuente(18, bold=True), fill=PANTALLA_TEXTO)
    draw.text((45, 105), artista_recortado, font=fuente(13),            fill=PANTALLA_TEXTO)
    draw.rounded_rectangle([(45, 140), (W - 45, 148)], radius=4, fill=(210, 210, 210))
    progreso_px = 45 + int((W - 90) * (progreso_pct / 100))
    draw.rounded_rectangle([(45, 140), (progreso_px, 148)], radius=4, fill=AZUL_IPOD)
    draw.text((45, 160),     "0:00",   font=fuente(11), fill=PANTALLA_TEXTO)
    draw.text((W - 45, 160), duracion, font=fuente(11), fill=PANTALLA_TEXTO, anchor="ra")
    draw.rectangle([(W - 65, 45), (W - 45, 55)], outline=PANTALLA_TEXTO, width=1)
    draw.rectangle([(W - 63, 47), (W - 49, 53)], fill=PANTALLA_TEXTO)
    centro_x, centro_y = W // 2, 350
    radio_rueda        = 90
    draw.ellipse([(centro_x - radio_rueda, centro_y - radio_rueda), (centro_x + radio_rueda, centro_y + radio_rueda)], fill=(240, 240, 240))
    draw.ellipse([(centro_x - radio_rueda, centro_y - radio_rueda), (centro_x + radio_rueda, centro_y + radio_rueda)], outline=(200, 200, 200), width=3)
    radio_central = 30
    draw.ellipse([(centro_x - radio_central, centro_y - radio_central), (centro_x + radio_central, centro_y + radio_central)], fill=(210, 210, 210))
    draw.text((centro_x, centro_y - 75), "MENU", font=fuente(12, bold=True), fill=(120, 120, 120), anchor="mm")
    draw.text((centro_x, centro_y + 70), "▶||",  font=fuente(12, bold=True), fill=(120, 120, 120), anchor="mm")
    draw.text((centro_x - 65, centro_y), "|◀◀",  font=fuente(11, bold=True), fill=(120, 120, 120), anchor="mm")
    draw.text((centro_x + 65, centro_y), "▶▶|",  font=fuente(11, bold=True), fill=(120, 120, 120), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ipod.png")

@bot.hybrid_command(name="ipod-player", description="Genera una simulación de reproductor iPod Classic.")
async def ipod_player(ctx: commands.Context, cancion: str, artista: str, duracion: str = "3:45", progreso: int = 45):
    await ctx.defer()
    progreso_seguro = max(0, min(progreso, 100))
    file = await generar_ipod_player_img(cancion, artista, duracion, progreso_seguro)
    await ctx.send(file=file)

# =========================================================
# CLIMA
# =========================================================

@bot.hybrid_command(name="clima", description="Muestra el clima actual de una ciudad")
async def clima(ctx: commands.Context, *, ciudad: str):
    API_KEY = os.getenv("WEATHER_API_KEY")
    if not API_KEY:
        embed = discord.Embed(title="Error de configuración", description="> WEATHER_API_KEY no configurada.", color=0x2B55B5)
        await ctx.send(embed=embed)
        return
    await ctx.defer() if ctx.interaction else None
    mensaje_carga = await ctx.send("> Buscando información del clima...")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={API_KEY}&units=metric&lang=es"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as respuesta:
                if respuesta.status == 404:
                    await mensaje_carga.delete()
                    embed = discord.Embed(title="Ciudad no encontrada", description=f"> No se encontró la ciudad **{ciudad}**.", color=0x2B55B5)
                    await ctx.send(embed=embed)
                    return
                if respuesta.status != 200:
                    await mensaje_carga.delete()
                    embed = discord.Embed(title="Error", description=f"> Error al obtener el clima. Código: {respuesta.status}", color=0x2B55B5)
                    await ctx.send(embed=embed)
                    return
                datos = await respuesta.json()
    except Exception as e:
        await mensaje_carga.delete()
        embed = discord.Embed(title="Error de conexión", description=f"> No se pudo conectar.\n```{str(e)}```", color=0x2B55B5)
        await ctx.send(embed=embed)
        return
    nombre_ciudad     = datos['name']
    pais              = datos['sys']['country']
    temperatura       = datos['main']['temp']
    sensacion_termica = datos['main']['feels_like']
    humedad           = datos['main']['humidity']
    descripcion       = datos['weather'][0]['description'].capitalize()
    viento            = datos['wind']['speed']
    icono             = datos['weather'][0]['icon']
    embed = discord.Embed(title=f"Clima en {nombre_ciudad}, {pais}", color=0x2B55B5)
    embed.add_field(name="> Temperatura", value=f"{temperatura}°C",       inline=True)
    embed.add_field(name="> Sensación",   value=f"{sensacion_termica}°C", inline=True)
    embed.add_field(name="> Humedad",     value=f"{humedad}%",            inline=True)
    embed.add_field(name="> Viento",      value=f"{viento} m/s",          inline=True)
    embed.add_field(name="> Descripción", value=descripcion,              inline=False)
    embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{icono}@2x.png")
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await mensaje_carga.delete()
    await ctx.send(embed=embed)

# =========================================================
# PAIS
# =========================================================

@bot.hybrid_command(name="pais", description="Muestra informacion de un pais")
async def pais(ctx: commands.Context, *, nombre: str):
    await ctx.defer() if ctx.interaction else None
    try:
        url = f"https://restcountries.com/v3.1/name/{nombre}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    embed = discord.Embed(color=0x2B55B5)
                    embed.description = f"> Pais **{nombre}** no encontrado."
                    if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
                    else: await ctx.send(embed=embed)
                    return
                data = await resp.json()
        pais_data      = data[0]
        nombre_oficial = pais_data.get('name', {}).get('official', 'Desconocido')
        capital        = ", ".join(pais_data.get('capital', ['Desconocida']))
        poblacion      = f"{pais_data.get('population', 0):,}"
        area           = f"{pais_data.get('area', 0):,} km"
        idiomas        = ", ".join(pais_data.get('languages', {}).values())
        moneda         = list(pais_data.get('currencies', {}).values())[0].get('name', 'Desconocida') if pais_data.get('currencies') else 'Desconocida'
        bandera        = pais_data.get('flags', {}).get('png', '')
        mapa           = pais_data.get('maps', {}).get('googleMaps', '')
        embed = discord.Embed(title=nombre_oficial, color=0x2B55B5)
        embed.add_field(name="> Capital",   value=capital,      inline=True)
        embed.add_field(name="> Poblacion", value=poblacion,    inline=True)
        embed.add_field(name="> Area",      value=area,         inline=True)
        embed.add_field(name="> Idiomas",   value=idiomas[:50], inline=True)
        embed.add_field(name="> Moneda",    value=moneda,       inline=True)
        if mapa:    embed.add_field(name="> Google Maps", value=f"[Ver mapa]({mapa})", inline=False)
        if bandera: embed.set_thumbnail(url=bandera)
        if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
        else: await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(color=0x2B55B5)
        embed.description = f"> Error: `{str(e)[:100]}`"
        if ctx.interaction: await ctx.interaction.followup.send(embed=embed)
        else: await ctx.send(embed=embed)

# =========================================================
# JUEGOS GRATIS
# =========================================================

@bot.hybrid_command(name="juegos", description="Muestra juegos gratis disponibles")
async def juegos_gratis(ctx: commands.Context):
    await ctx.defer() if ctx.interaction else None
    url = "https://www.freetogame.com/api/games?sort-by=release-date"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send("Error al obtener juegos.")
                return
            juegos = await resp.json()
            juegos = juegos[:5]
    embed = discord.Embed(title="Juegos Gratis Recomendados", color=0x2B55B5)
    for juego in juegos:
        titulo     = juego.get('title', 'Sin título')
        genero     = juego.get('genre', 'Desconocido')
        plataforma = juego.get('platform', 'PC')
        url_juego  = juego.get('game_url', '')
        embed.add_field(name=titulo, value=f"{genero} | {plataforma}\n[Descargar]({url_juego})", inline=False)
    embed.set_footer(text="Juegos gratis de FreeToGame.com")
    await ctx.send(embed=embed)

# =========================================================
# PELICULA
# =========================================================

@bot.hybrid_command(name="pelicula", description="Busca información de una película")
async def pelicula(ctx: commands.Context, *, nombre: str):
    await ctx.defer() if ctx.interaction else None
    API_KEY = os.getenv("TMDB_API_KEY")
    if not API_KEY:
        await ctx.send("**API Key de TMDB no configurada**")
        return
    url_buscar = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={nombre}&language=es"
    async with aiohttp.ClientSession() as session:
        async with session.get(url_buscar) as resp:
            data       = await resp.json()
            resultados = data.get('results', [])
            if not resultados:
                await ctx.send(f"> No se encontró la película: **{nombre}**")
                return
            peli = resultados[0]
    peli_id      = peli.get('id')
    url_detalles = f"https://api.themoviedb.org/3/movie/{peli_id}?api_key={API_KEY}&language=es"
    async with aiohttp.ClientSession() as session:
        async with session.get(url_detalles) as resp:
            detalles = await resp.json()
    titulo      = detalles.get('title', 'Sin título')
    fecha       = detalles.get('release_date', 'Desconocida')[:4]
    duracion    = detalles.get('runtime', 0)
    generos     = ", ".join([g.get('name', '') for g in detalles.get('genres', [])])
    descripcion = detalles.get('overview', 'Sin descripción')
    puntaje     = detalles.get('vote_average', 0)
    poster      = detalles.get('poster_path', '')
    url_imagen  = f"https://image.tmdb.org/t/p/w500{poster}" if poster else ""
    embed = discord.Embed(title=f"{titulo} ({fecha})", description=descripcion[:300] + "..." if len(descripcion) > 300 else descripcion, color=0x2B55B5)
    embed.add_field(name="> Puntuación", value=f"{puntaje}/10",  inline=True)
    embed.add_field(name="> Duración",   value=f"{duracion} min", inline=True)
    embed.add_field(name="> Géneros",    value=generos[:50],      inline=True)
    if url_imagen: embed.set_thumbnail(url=url_imagen)
    await ctx.send(embed=embed)

# =========================================================
# POKEMON
# =========================================================

@bot.hybrid_command(name="pokemon", description="Información de un Pokémon")
async def pokemon(ctx: commands.Context, *, nombre: str):
    await ctx.defer() if ctx.interaction else None
    nombre = nombre.lower().strip()
    url    = f"https://pokeapi.co/api/v2/pokemon/{nombre}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send(f"> No se encontró el Pokémon: **{nombre}**")
                return
            data = await resp.json()
    nombre_oficial = data.get('name', nombre).capitalize()
    id_pokemon     = data.get('id', 0)
    altura         = data.get('height', 0) / 10
    peso           = data.get('weight', 0) / 10
    tipos          = ", ".join([t['type']['name'].capitalize() for t in data.get('types', [])])
    habilidades    = ", ".join([h['ability']['name'].capitalize() for h in data.get('abilities', [])[:3]])
    stats = {}
    for s in data.get('stats', []):
        stats[s['stat']['name']] = s['base_stat']
    sprite = data.get('sprites', {}).get('front_default', '')
    embed = discord.Embed(title=f"{nombre_oficial} #{id_pokemon}", color=0x2B55B5)
    embed.add_field(name="> Altura",      value=f"{altura} m",  inline=True)
    embed.add_field(name="> Peso",        value=f"{peso} kg",   inline=True)
    embed.add_field(name="> Tipo",        value=tipos,          inline=True)
    embed.add_field(name="> Habilidades", value=habilidades,    inline=False)
    if stats:
        embed.add_field(name="> HP",      value=stats.get('hp', 0),      inline=True)
        embed.add_field(name="> Ataque",  value=stats.get('attack', 0),  inline=True)
        embed.add_field(name="> Defensa", value=stats.get('defense', 0), inline=True)
    if sprite: embed.set_thumbnail(url=sprite)
    await ctx.send(embed=embed)

# =========================================================
# NASA
# =========================================================

@bot.hybrid_command(name="nasa", description="Foto astronómica del día (NASA APOD)")
async def nasa(ctx: commands.Context):
    await ctx.defer() if ctx.interaction else None
    traducciones = {
        "Earth": "Tierra", "Moon": "Luna", "Sun": "Sol", "Mars": "Marte",
        "Jupiter": "Júpiter", "Saturn": "Saturno", "Neptune": "Neptuno",
        "Uranus": "Urano", "Venus": "Venus", "Mercury": "Mercurio",
        "Galaxy": "Galaxia", "Star": "Estrella", "Stars": "Estrellas",
        "Nebula": "Nebulosa", "Nebulae": "Nebulosas", "Black Hole": "Agujero Negro",
        "Supernova": "Supernova", "Comet": "Cometa", "Asteroid": "Asteroide",
        "Space": "Espacio", "Telescope": "Telescopio", "Astronaut": "Astronauta",
        "Planet": "Planeta", "Planets": "Planetas", "Constellation": "Constelación",
        "Cluster": "Cúmulo", "Orbit": "Órbita", "Milky Way": "Vía Láctea",
        "Solar System": "Sistema Solar", "Rocket": "Cohete", "Spacecraft": "Nave Espacial",
        "Satellite": "Satélite", "Observatory": "Observatorio",
    }
    def traducir_texto(texto):
        resultado = texto
        for en, es in traducciones.items():
            resultado = resultado.replace(en, es).replace(en.lower(), es.lower())
        return resultado
    años            = list(range(1995, 2025))
    mes             = random.randint(1, 12)
    dia             = random.randint(1, 28)
    fecha_aleatoria = f"{random.choice(años)}-{mes:02d}-{dia:02d}"
    fecha_actual    = datetime.now().strftime("%Y-%m-%d")
    usar_actual     = random.choice([True, False])
    fecha           = fecha_actual if usar_actual else fecha_aleatoria
    tipo            = "Imagen del Día" if usar_actual else "Imagen Aleatoria (Archivo NASA)"
    url = f"https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&date={fecha}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send("Error al obtener imagen de la NASA.")
                return
            data = await resp.json()
    if 'error' in data:
        await ctx.send(f"{data.get('error', {}).get('message', 'Error desconocido')}")
        return
    titulo      = traducir_texto(data.get('title', 'Imagen del día'))
    explicacion = traducir_texto(data.get('explanation', 'Sin explicación disponible'))
    if len(explicacion) > 500:
        explicacion = explicacion[:500] + "..."
    imagen       = data.get('url', '')
    fecha_nasa   = data.get('date', fecha)
    copyright_nt = traducir_texto(data.get('copyright', 'NASA'))
    if imagen.endswith('.mp4') or 'youtube' in imagen or 'vimeo' in imagen:
        embed = discord.Embed(title=titulo, description=f"**Video del día**\n\n{explicacion}", color=0x2B55B5)
        embed.add_field(name="**Ver video**", value=f"[Haz clic aquí]({imagen})", inline=False)
    else:
        embed = discord.Embed(title=titulo, description=explicacion, color=0x2B55B5, url=imagen)
        embed.set_image(url=imagen)
    embed.add_field(name="> Fecha",   value=fecha_nasa,   inline=True)
    embed.add_field(name="> Crédito", value=copyright_nt, inline=True)
    embed.add_field(name="> Tipo",    value=tipo,         inline=True)
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name} | NASA APOD")
    await ctx.send(embed=embed)

# =========================================================
# TRADUCIR
# =========================================================

@bot.hybrid_command(name="traducir", description="Traduce texto a cualquier idioma")
async def traducir(ctx: commands.Context, idioma: str, *, texto: str):
    await ctx.defer() if ctx.interaction else None
    idiomas_nombres = {
        "es": "Español", "en": "Inglés", "fr": "Francés", "de": "Alemán",
        "it": "Italiano", "pt": "Portugués", "ja": "Japonés", "ko": "Coreano",
        "zh": "Chino", "ru": "Ruso", "ar": "Árabe", "hi": "Hindi",
        "nl": "Holandés", "pl": "Polaco", "tr": "Turco", "vi": "Vietnamita",
        "th": "Tailandés", "el": "Griego", "he": "Hebreo", "sv": "Sueco",
        "no": "Noruego", "da": "Danés", "fi": "Finlandés",
    }
    idioma = idioma.lower()
    if idioma not in idiomas_nombres:
        codigos = ", ".join(list(idiomas_nombres.keys())[:15])
        await ctx.send(f"> Idioma **{idioma}** no válido.\nCódigos disponibles: {codigos}...")
        return
    url_detectar = f"https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&dt=ld&dt=rm&dj=1&q={urllib.parse.quote(texto)}&sl=auto&tl={idioma}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url_detectar) as resp:
                if resp.status != 200:
                    await ctx.send("**Error al conectar con el traductor.**")
                    return
                data = await resp.json()
        traduccion = ""
        idioma_detectado = ""
        if 'sentences' in data:
            for sentence in data['sentences']:
                if 'trans' in sentence:
                    traduccion += sentence['trans']
        if 'src' in data:
            idioma_detectado = data['src']
        if not traduccion:
            await ctx.send("**No se pudo traducir el texto.**")
            return
        texto_original  = texto[:500] + "..."      if len(texto) > 500      else texto
        texto_traducido = traduccion[:500] + "..." if len(traduccion) > 500 else traduccion
        idioma_origen_nombre  = idiomas_nombres.get(idioma_detectado, idioma_detectado.upper())
        idioma_destino_nombre = idiomas_nombres.get(idioma, idioma.upper())
        embed = discord.Embed(title="Traductor de Google", color=0x2B55B5)
        embed.add_field(name=f"Texto original ({idioma_origen_nombre})",  value=f"```{texto_original}```",  inline=False)
        embed.add_field(name=f"> Traducción ({idioma_destino_nombre})", value=f"```{texto_traducido}```", inline=False)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"**Error al traducir**: ```{str(e)}```")

# =========================================================
# DEFINIR
# =========================================================

@bot.hybrid_command(name="definir", description="Busca el significado de una palabra")
async def definir(ctx: commands.Context, *, palabra: str):
    await ctx.defer() if ctx.interaction else None
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{palabra}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send(f"> No se encontró la palabra **{palabra}**")
                return
            data = await resp.json()
    if not data:
        await ctx.send(f"> No se encontró la palabra **{palabra}**")
        return
    palabra_info   = data[0]
    palabra_nombre = palabra_info.get('word', palabra)
    significados   = palabra_info.get('meanings', [])
    embed = discord.Embed(title=f"{palabra_nombre.capitalize()}", color=0x2B55B5)
    for significado in significados[:3]:
        tipo         = significado.get('partOfSpeech', 'Desconocido')
        definiciones = significado.get('definitions', [])
        if definiciones:
            definicion = definiciones[0].get('definition', 'Sin definición')
            ejemplo    = definiciones[0].get('example', '')
            texto      = f"**{tipo}**\n{definicion[:200]}"
            if ejemplo:
                texto += f"\n*Ejemplo: {ejemplo[:100]}*"
            embed.add_field(name=f"{tipo.capitalize()}", value=texto[:250], inline=False)
    await ctx.send(embed=embed)

# =========================================================
# STEAM
# =========================================================

@bot.hybrid_command(name="steam", description="Busca información de un juego en Steam")
async def steam(ctx: commands.Context, *, juego: str):
    await ctx.defer() if ctx.interaction else None
    url_buscar = "https://steamcommunity.com/api/ISteamApps/GetAppList/v2/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url_buscar) as resp:
            if resp.status != 200:
                await ctx.send("> Error al conectar con Steam")
                return
            data = await resp.json()
            apps = data.get('applist', {}).get('apps', [])
    juego_lower = juego.lower()
    resultados  = [app for app in apps if juego_lower in app['name'].lower()]
    if not resultados:
        await ctx.send(f"> No se encontró el juego: **{juego}**")
        return
    juego_info = resultados[0]
    app_id     = juego_info['appid']
    nombre     = juego_info['name']
    url_detalles = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url_detalles) as resp:
            data = await resp.json()
    detalles = data.get(str(app_id), {})
    if not detalles.get('success'):
        await ctx.send(f"> No se pudieron obtener detalles de `{nombre}`")
        return
    info        = detalles.get('data', {})
    descripcion = info.get('short_description', 'Sin descripción')
    precio      = info.get('price_overview', {})
    precio_final = precio.get('final_formatted', 'Gratis') if precio else 'No disponible'
    plataformas = []
    if info.get('platforms', {}).get('windows'): plataformas.append("🪟 Windows")
    if info.get('platforms', {}).get('mac'):     plataformas.append("🍎 Mac")
    if info.get('platforms', {}).get('linux'):   plataformas.append("🐧 Linux")
    plataformas_texto = ", ".join(plataformas) if plataformas else "No disponible"
    generos       = [g['description'] for g in info.get('genres', [])]
    generos_texto = ", ".join(generos[:3]) if generos else "No disponible"
    puntaje       = info.get('metacritic', {}).get('score', 'No disponible')
    url_imagen    = info.get('header_image', '')
    embed = discord.Embed(title=nombre, description=descripcion[:200] + "..." if len(descripcion) > 200 else descripcion, color=0x2B55B5, url=f"https://store.steampowered.com/app/{app_id}")
    embed.add_field(name="> Precio",      value=precio_final,  inline=True)
    embed.add_field(name="> Metacritic",  value=f"{puntaje}/100" if puntaje != 'No disponible' else puntaje, inline=True)
    embed.add_field(name="> Géneros",     value=generos_texto,  inline=False)
    embed.add_field(name="> Plataformas", value=plataformas_texto, inline=True)
    if url_imagen: embed.set_thumbnail(url=url_imagen)
    embed.set_footer(text=f"ID: {app_id} | Steam Store")
    await ctx.send(embed=embed)

# =========================================================
# QR
# =========================================================

@bot.hybrid_command(name="qr", description="Genera un código QR")
async def generar_qr(ctx: commands.Context, *, texto: str):
    await ctx.defer() if ctx.interaction else None
    url   = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(texto)}"
    embed = discord.Embed(title="Código QR Generado", description=f"**Contenido:** {texto[:100]}{'...' if len(texto) > 100 else ''}", color=0x2B55B5)
    embed.set_image(url=url)
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    await ctx.send(embed=embed)

# =========================================================
# COLOR
# =========================================================

@bot.hybrid_command(name="color", description="Muestra un color por código HEX (o genera uno aleatorio)")
async def mostrar_color(ctx: commands.Context, hex_code: str = None):
    import re
    if not hex_code:
        hex_code = ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
        es_aleatorio = True
    else:
        hex_code = hex_code.strip().lstrip('#').upper()
        es_aleatorio = False
    if not re.match(r'^[0-9A-F]{6}$', hex_code):
        embed = discord.Embed(title="Error", description=f"> Código HEX inválido: `{hex_code}`", color=0x2B55B5)
        await ctx.send(embed=embed)
        return
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    r_comp, g_comp, b_comp = 255 - r, 255 - g, 255 - b
    hex_comp = f"{r_comp:02X}{g_comp:02X}{b_comp:02X}"
    img  = Image.new("RGB", (400, 200), (r, g, b))
    draw = ImageDraw.Draw(img)
    draw.text((200, 80),  f"#{hex_code}",      font=fuente(24, bold=True), fill=(255, 255, 255), anchor="mm")
    draw.text((200, 120), f"RGB({r}, {g}, {b})", font=fuente(16),           fill=(255, 255, 255), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    archivo = discord.File(buf, filename="color.png")
    nombres_colores = {
        "FF0000": "Rojo", "00FF00": "Verde", "0000FF": "Azul", "FFFFFF": "Blanco", "000000": "Negro",
        "FFFF00": "Amarillo", "FF00FF": "Magenta", "00FFFF": "Cian", "FF5733": "Naranja", "5AC8FA": "Celeste"
    }
    nombre_color = nombres_colores.get(hex_code, "Color personalizado")
    embed = discord.Embed(title=f"{nombre_color}" if not es_aleatorio else "Color Aleatorio", color=int(hex_code, 16))
    embed.add_field(name="> Código HEX",  value=f"`#{hex_code}`",        inline=True)
    embed.add_field(name="> RGB",         value=f"`({r}, {g}, {b})`",    inline=True)
    embed.add_field(name="> Complementario", value=f"`#{hex_comp}`",     inline=True)
    embed.set_image(url="attachment://color.png")
    if es_aleatorio:
        embed.set_footer(text="Usa /color [HEX] para ver un color específico")
    await ctx.send(embed=embed, file=archivo)

# =========================================================
# IP INFO
# =========================================================

@bot.hybrid_command(name="ip", description="Obtiene información de una dirección IP")
async def ip_info(ctx: commands.Context, direccion_ip: str):
    await ctx.defer() if ctx.interaction else None
    url = f"http://ip-api.com/json/{direccion_ip}?lang=es"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send("> Error al obtener información de la IP")
                return
            data = await resp.json()
    if data.get('status') == 'fail':
        await ctx.send(f"> IP **{direccion_ip}** no válida o no encontrada")
        return
    embed = discord.Embed(title=f"Información de IP: {direccion_ip}", color=0x2B55B5)
    embed.add_field(name="> País",          value=data.get('country', 'Desconocido'),    inline=True)
    embed.add_field(name="> Ciudad",        value=data.get('city', 'Desconocida'),       inline=True)
    embed.add_field(name="> ISP",           value=data.get('isp', 'Desconocido'),        inline=True)
    embed.add_field(name="> Región",        value=data.get('regionName', 'Desconocida'), inline=True)
    embed.add_field(name="> Código Postal", value=data.get('zip', 'Desconocido'),        inline=True)
    embed.add_field(name="> Tipo",          value="Móvil" if data.get('mobile') else "Fijo", inline=True)
    await ctx.send(embed=embed)

# =========================================================
# ACERTIJO
# =========================================================

acertijos = [
    {"pregunta": "Blanco por dentro, verde por fuera. Si quieres que te lo diga, espera.",  "respuesta": "pera"},
    {"pregunta": "Oro parece, plata no es. Abre las cortinas y verás lo que es.",           "respuesta": "plátano"},
    {"pregunta": "Tiene dientes pero no come, tiene cabeza pero no es hombre.",             "respuesta": "ajo"},
    {"pregunta": "Viste de verde y vive en el mar, si te pilla te hará llorar.",            "respuesta": "cebolla"},
    {"pregunta": "¿Qué cosa es que cuanto más le quitas, más grande se hace?",             "respuesta": "agujero"},
    {"pregunta": "Vuelo sin alas, lloro sin ojos. ¿Quién soy?",                            "respuesta": "nube"},
    {"pregunta": "Siempre en la boca pero nunca se come.",                                  "respuesta": "sonrisa"},
]

@bot.hybrid_command(name="acertijo", description="Resuelve un acertijo")
async def acertijo(ctx: commands.Context):
    acertijo_actual = random.choice(acertijos)
    embed = discord.Embed(title="Acertijo", description=f"**{acertijo_actual['pregunta']}**", color=0x2B55B5)
    embed.set_footer(text="Responde con >respuesta [tu respuesta] (tienes 30 segundos)")
    await ctx.send(embed=embed)
    def check(m):
        return m.author == ctx.author and m.content.startswith(">respuesta")
    try:
        msg               = await bot.wait_for("message", timeout=30.0, check=check)
        respuesta_usuario = msg.content.replace(">respuesta", "").strip().lower()
        if respuesta_usuario == acertijo_actual["respuesta"]:
            data       = get_user_eco(ctx.guild.id, ctx.author.id)
            recompensa = random.randint(50, 150)
            data["coins"] += recompensa
            await msg.reply(f"> **¡Correcto!** \nGanaste **${recompensa}**")
        else:
            await msg.reply(f"> **Incorrecto**\nLa respuesta era: **{acertijo_actual['respuesta']}**")
    except asyncio.TimeoutError:
        await ctx.send(f"> Tiempo agotado. La respuesta era: **{acertijo_actual['respuesta']}**")

# =========================================================
# COVID
# =========================================================

@bot.hybrid_command(name="covid", description="Datos actualizados de COVID-19")
async def covid(ctx: commands.Context, pais: str = "mexico"):
    await ctx.defer() if ctx.interaction else None
    url = f"https://disease.sh/v3/covid-19/countries/{pais}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send(f"> No se encontraron datos para: {pais}")
                return
            data = await resp.json()
    nombre       = data.get('country', pais.capitalize())
    casos        = data.get('cases', 0)
    casos_hoy    = data.get('todayCases', 0)
    muertes      = data.get('deaths', 0)
    muertes_hoy  = data.get('todayDeaths', 0)
    recuperados  = data.get('recovered', 0)
    activos      = data.get('active', 0)
    criticos     = data.get('critical', 0)
    pruebas      = data.get('tests', 0)
    poblacion    = data.get('population', 0)
    bandera      = data.get('countryInfo', {}).get('flag', '')
    tasa_mortalidad   = (muertes / casos * 100)      if casos > 0     else 0
    tasa_recuperacion = (recuperados / casos * 100)   if casos > 0     else 0
    casos_por_millon  = (casos / poblacion * 1000000) if poblacion > 0 else 0
    embed = discord.Embed(title=f"COVID-19: {nombre}", color=0x2B55B5)
    if bandera: embed.set_thumbnail(url=bandera)
    embed.add_field(name="> Casos totales",     value=f"{casos:,}",               inline=True)
    embed.add_field(name="> Casos hoy",         value=f"+{casos_hoy:,}",          inline=True)
    embed.add_field(name="> Muertes",           value=f"{muertes:,}",             inline=True)
    embed.add_field(name="> Muertes hoy",       value=f"+{muertes_hoy:,}",        inline=True)
    embed.add_field(name="> Recuperados",       value=f"{recuperados:,}",         inline=True)
    embed.add_field(name="> Activos",           value=f"{activos:,}",             inline=True)
    embed.add_field(name="> Críticos",          value=f"{criticos:,}",            inline=True)
    embed.add_field(name="> Pruebas",           value=f"{pruebas:,}",             inline=True)
    embed.add_field(name="> Tasa mortalidad",   value=f"{tasa_mortalidad:.2f}%",  inline=True)
    embed.add_field(name="> Tasa recuperación", value=f"{tasa_recuperacion:.2f}%",inline=True)
    embed.add_field(name="> Población",         value=f"{poblacion:,}",           inline=True)
    embed.add_field(name="> Casos/1M",          value=f"{casos_por_millon:.0f}",  inline=True)
    embed.set_footer(text="Actualizado | disease.sh API")
    await ctx.send(embed=embed)

# =========================================================
# MEMORIA POR USUARIO
# =========================================================

memoria_usuarios = {}

def get_memoria(user_id: int) -> list:
    if user_id not in memoria_usuarios:
        memoria_usuarios[user_id] = []
    return memoria_usuarios[user_id]

def agregar_memoria(user_id: int, role: str, content: str):
    memoria = get_memoria(user_id)
    memoria.append({"role": role, "content": content})
    if len(memoria) > 30:
        memoria.pop(0)

def limpiar_memoria(user_id: int):
    memoria_usuarios.pop(user_id, None)

# =========================================================
# GENERADOR DE IMÁGENES
# =========================================================

PALABRAS_IMAGEN = ["imagen", "foto", "dibujo", "genera", "wallpaper", "crea", "hazme", "dibujame", "pintame", "ilustra", "generame", "muestrame"]

async def generar_imagen_ia(mensaje: str):
    import urllib.parse, re
    prompt = mensaje.lower()
    for p in PALABRAS_IMAGEN:
        prompt = prompt.replace(p, "")
    prompt = re.sub(r'\s+', ' ', prompt).strip() or mensaje
    prompt_encoded = urllib.parse.quote(prompt[:500])
    seed = random.randint(1, 999999)
    url  = f"https://image.pollinations.ai/prompt/{prompt_encoded}?w=512&h=512&seed={seed}&nologo=true"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    return await resp.read(), prompt, seed
    except:
        pass
    return None, None, None

async def generar_respuesta_groq(user_id: int, mensaje: str, nombre_usuario: str, nombre_servidor: str) -> str:
    historial = get_memoria(user_id)
    system_prompt = f"""Tu nombre es Misti. Eres un asistente inteligente, amable y util.
Estas hablando con {nombre_usuario} en {nombre_servidor}.
No uses emojis en tus respuestas.
Recuerdas conversaciones anteriores con cada usuario.
Responde de forma natural, clara y directa."""
    mensajes_api = [{"role": "system", "content": system_prompt}]
    for msg in historial[-15:]:
        mensajes_api.append({"role": msg["role"], "content": msg["content"]})
    mensajes_api.append({"role": "user", "content": mensaje})
    try:
        respuesta = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensajes_api,
            temperature=0.8,
            max_tokens=500
        )
        texto = respuesta.choices[0].message.content
        return texto[:500] + "..." if len(texto) > 500 else texto
    except Exception as e:
        print(f"Error Groq: {e}")
        return "Tuve un problema al procesar tu mensaje, intentalo de nuevo."

class RegenerarButton(discord.ui.View):
    def __init__(self, user_id: int, mensaje_original: str):
        super().__init__(timeout=60)
        self.user_id          = user_id
        self.mensaje_original = mensaje_original

    @discord.ui.button(label="Regenerar", style=discord.ButtonStyle.primary, emoji="<:retry:1505394236906799165>")
    async def regenerar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("> Solo quien hizo la pregunta puede regenerar.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            nombre_servidor = interaction.guild.name if interaction.guild else "DM"
            respuesta = await generar_respuesta_groq(interaction.user.id, self.mensaje_original, interaction.user.display_name, nombre_servidor)
            agregar_memoria(interaction.user.id, "assistant", respuesta)
            embed = discord.Embed(color=0x2B55B5)
            user_text = self.mensaje_original[:500] + "..." if len(self.mensaje_original) > 500 else self.mensaje_original
            embed.add_field(name=f"**{interaction.user.display_name}**", value=f"> {user_text}", inline=False)
            bot_text = respuesta[:500] + "..." if len(respuesta) > 500 else respuesta
            embed.add_field(name="**Misti**", value=f"> {bot_text}", inline=False)
            await interaction.edit_original_response(embed=embed, view=RegenerarButton(interaction.user.id, self.mensaje_original))
        except Exception as e:
            embed = discord.Embed(color=0x2B55B5)
            embed.description = f"> Error: `{str(e)[:100]}`"
            await interaction.edit_original_response(embed=embed, view=None)

async def responder_ask(destino, autor, mensaje: str, es_reply: bool = False):
    nombre_servidor = autor.guild.name if hasattr(autor, 'guild') and autor.guild else "DM"
    if any(p in mensaje.lower() for p in PALABRAS_IMAGEN):
        img_data, prompt, seed = await generar_imagen_ia(mensaje)
        if img_data:
            archivo = discord.File(io.BytesIO(img_data), filename="misti_art.png")
            embed   = discord.Embed(title="Imagen generada", description=f"> **Prompt:** {prompt[:200]}", color=0x2B55B5)
            embed.set_image(url="attachment://misti_art.png")
            if seed: embed.set_footer(text=f"Seed: {seed}")
            if es_reply: await destino.reply(embed=embed, file=archivo, mention_author=False)
            else:        await destino.send(embed=embed, file=archivo)
        else:
            embed = discord.Embed(color=0x2B55B5)
            embed.description = "> No pude generar la imagen, intenta con otro prompt."
            if es_reply: await destino.reply(embed=embed, mention_author=False)
            else:        await destino.send(embed=embed)
        return
    agregar_memoria(autor.id, "user", mensaje)
    respuesta = await generar_respuesta_groq(autor.id, mensaje, autor.display_name, nombre_servidor)
    agregar_memoria(autor.id, "assistant", respuesta)
    embed = discord.Embed(color=0x2B55B5)
    user_text = mensaje[:500] + "..." if len(mensaje) > 500 else mensaje
    embed.add_field(name=f"**{autor.display_name}**", value=f"> {user_text}", inline=False)
    bot_text  = respuesta[:500] + "..." if len(respuesta) > 500 else respuesta
    embed.add_field(name="**Misti**", value=f"> {bot_text}", inline=False)
    view = RegenerarButton(autor.id, mensaje)
    if es_reply: await destino.reply(embed=embed, view=view, mention_author=False)
    else:        await destino.send(embed=embed, view=view)

@bot.tree.command(name="ask", description="Habla con Misti")
async def ask_slash(i: discord.Interaction, texto: str):
    await i.response.defer()
    nombre_servidor = i.guild.name if i.guild else "DM"
    if any(p in texto.lower() for p in PALABRAS_IMAGEN):
        img_data, prompt, seed = await generar_imagen_ia(texto)
        if img_data:
            archivo = discord.File(io.BytesIO(img_data), filename="misti_art.png")
            embed   = discord.Embed(title="Imagen generada", description=f"> **Prompt:** {prompt[:200]}", color=0x2B55B5)
            embed.set_image(url="attachment://misti_art.png")
            if seed: embed.set_footer(text=f"Seed: {seed}")
            await i.followup.send(embed=embed, file=archivo)
        else:
            embed = discord.Embed(color=0x2B55B5)
            embed.description = "> No pude generar la imagen, intenta con otro prompt."
            await i.followup.send(embed=embed)
        return
    agregar_memoria(i.user.id, "user", texto)
    respuesta = await generar_respuesta_groq(i.user.id, texto, i.user.display_name, nombre_servidor)
    agregar_memoria(i.user.id, "assistant", respuesta)
    embed = discord.Embed(color=0x2B55B5)
    user_text = texto[:500] + "..." if len(texto) > 500 else texto
    embed.add_field(name=f"**{i.user.display_name}**", value=f"> {user_text}", inline=False)
    bot_text  = respuesta[:500] + "..." if len(respuesta) > 500 else respuesta
    embed.add_field(name="**Misti**", value=f"> {bot_text}", inline=False)
    await i.followup.send(embed=embed, view=RegenerarButton(i.user.id, texto))

@bot.command(name="ask")
async def ask_prefix(ctx, *, texto: str):
    await responder_ask(ctx, ctx.author, texto, es_reply=False)

# =========================================================
# ON MESSAGE — unico, completo
# =========================================================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # QUITAR AFK
    if message.author.id in afk_data:
        tiempo_inicio    = afk_data[message.author.id]["tiempo"]
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

    # MONEDAS CADA 5 MENSAJES
    if message.guild:
        uid = str(message.author.id)
        if uid not in mensaje_count: mensaje_count[uid] = 0
        mensaje_count[uid] += 1
        if mensaje_count[uid] >= 5:
            mensaje_count[uid] = 0
            data = get_user_eco(str(message.guild.id), message.author.id)
            data["coins"] += random.randint(2, 4)

    # MENCION AL BOT
    if bot.user in message.mentions:
        mensaje_limpio = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if not mensaje_limpio:
            await message.reply("> Mencioname con un mensaje para que te responda.", mention_author=False)
            return
        await responder_ask(message, message.author, mensaje_limpio, es_reply=True)
        return

    # REPLY AL BOT
    if message.reference:
        try:
            replied = await message.channel.fetch_message(message.reference.message_id)
            if replied.author.id == bot.user.id:
                await responder_ask(message, message.author, message.content, es_reply=True)
                return
        except:
            pass

# =========================================================
# FORGET
# =========================================================

@bot.hybrid_command(name="forget", description="Borra tu memoria con Misti")
async def forget(ctx: commands.Context):
    limpiar_memoria(ctx.author.id)
    embed = discord.Embed(color=0x2B55B5)
    embed.description = "> Misti ya no recuerda nada de ti."
    await ctx.send(embed=embed)

# =========================================================
# RECORDATORIO
# =========================================================

recordatorios_activos = {}

@bot.hybrid_command(name="recordar", description="Crea un recordatorio (10s, 5m, 2h, 1d)")
async def recordar(ctx: commands.Context, tiempo: str, *, mensaje: str):
    unidad         = tiempo[-1].lower()
    cantidad_texto = tiempo[:-1]
    try:
        cantidad = int(cantidad_texto)
    except:
        embed = discord.Embed(title="Error", description="> Formato inválido. Usa: `10s`, `5m`, `2h`, `1d`", color=0x2B55B5)
        await ctx.send(embed=embed)
        return
    if unidad == 's':
        segundos = cantidad
        texto_unidad = "segundo" if cantidad == 1 else "segundos"
    elif unidad == 'm':
        segundos = cantidad * 60
        texto_unidad = "minuto" if cantidad == 1 else "minutos"
    elif unidad == 'h':
        segundos = cantidad * 3600
        texto_unidad = "hora" if cantidad == 1 else "horas"
    elif unidad == 'd':
        segundos = cantidad * 86400
        texto_unidad = "día" if cantidad == 1 else "días"
    else:
        embed = discord.Embed(title="Error", description="> Unidad inválida. Usa: `s`, `m`, `h`, `d`", color=0x2B55B5)
        await ctx.send(embed=embed)
        return
    if segundos > 604800:
        embed = discord.Embed(title="Error", description="> El recordatorio no puede ser mayor a 7 días", color=0x2B55B5)
        await ctx.send(embed=embed)
        return
    if segundos < 5:
        embed = discord.Embed(title="Error", description="> El tiempo mínimo es 5 segundos", color=0x2B55B5)
        await ctx.send(embed=embed)
        return
    recordatorios_activos[ctx.author.id] = {"mensaje": mensaje, "tiempo": segundos, "canal_id": ctx.channel.id}
    embed_confirmacion = discord.Embed(title="Recordatorio creado", description=f"Te recordaré **{mensaje}** en **{cantidad} {texto_unidad}**", color=0x2B55B5)
    await ctx.send(embed=embed_confirmacion)
    await asyncio.sleep(segundos)
    embed_recordatorio = discord.Embed(title="RECORDATORIO", description=f"> {ctx.author.mention}\n**{mensaje}**", color=0x2B55B5)
    await ctx.channel.send(content=ctx.author.mention, embed=embed_recordatorio)
    recordatorios_activos.pop(ctx.author.id, None)

# =========================================================
# ANIMALES
# =========================================================

async def _animal_embed(ctx, datos: dict, query_unsplash: str, fallback_url: str):
    await ctx.defer()
    img_url = fallback_url
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.unsplash.com/photos/random?query={query_unsplash}&orientation=landscape") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img_url = data.get('urls', {}).get('regular', fallback_url)
    except:
        pass
    embed = discord.Embed(title=f"{datos['nombre']} ({datos['cientifico']})", color=0x2B55B5)
    embed.add_field(name="> Hábitat",         value=datos['habitat'],      inline=False)
    embed.add_field(name="> Alimentación",    value=datos['alimentacion'], inline=True)
    embed.add_field(name="> Longevidad",      value=datos['longevidad'],   inline=True)
    embed.add_field(name="> Dato curioso",    value=datos['curiosidad'],   inline=False)
    embed.add_field(name="> Más información", value=datos['dato_extra'],   inline=False)
    embed.set_image(url=img_url)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="leon",     description="Información y foto de un león")
async def leon(ctx):
    await _animal_embed(ctx, {"nombre":"León","cientifico":"Panthera leo","habitat":"Sabanas y pastizales de África","alimentacion":"Carnívoro (cazan en manada)","curiosidad":"Los leones duermen entre 16 y 20 horas al día","longevidad":"10-14 años en libertad","dato_extra":"La melena del macho le sirve para atraer hembras"}, "lion", "https://cdn.pixabay.com/photo/2017/07/24/19/57/lion-2535885_640.jpg")

@bot.hybrid_command(name="elefante", description="Información y foto de un elefante")
async def elefante(ctx):
    await _animal_embed(ctx, {"nombre":"Elefante Africano","cientifico":"Loxodonta africana","habitat":"Sabanas, bosques y desiertos de África","alimentacion":"Herbívoro (come hasta 150kg al día)","curiosidad":"Tienen la memoria más larga de los animales terrestres","longevidad":"60-70 años","dato_extra":"Su trompa tiene más de 40,000 músculos"}, "elephant", "https://cdn.pixabay.com/photo/2016/03/27/22/16/elephant-1284299_640.jpg")

@bot.hybrid_command(name="jirafa",   description="Información y foto de una jirafa")
async def jirafa(ctx):
    await _animal_embed(ctx, {"nombre":"Jirafa","cientifico":"Giraffa camelopardalis","habitat":"Sabanas y bosques abiertos de África","alimentacion":"Herbívoro (come hojas de acacia)","curiosidad":"Las jirafas duermen solo 30 minutos al día","longevidad":"20-25 años","dato_extra":"Su lengua mide hasta 45 cm y es de color negro"}, "giraffe", "https://cdn.pixabay.com/photo/2020/07/05/12/08/giraffe-5372115_640.jpg")

@bot.hybrid_command(name="pinguino", description="Información y foto de un pingüino")
async def pinguino(ctx):
    await _animal_embed(ctx, {"nombre":"Pingüino Emperador","cientifico":"Aptenodytes forsteri","habitat":"Antártida y costas del hemisferio sur","alimentacion":"Carnívoro (peces, calamares y krill)","curiosidad":"No pueden volar pero nadan a 25 km/h","longevidad":"15-20 años","dato_extra":"El macho incuba el huevo 60 días sin comer"}, "penguin", "https://cdn.pixabay.com/photo/2017/06/28/12/53/penguins-2450977_640.jpg")

@bot.hybrid_command(name="delfin",   description="Información y foto de un delfín")
async def delfin(ctx):
    await _animal_embed(ctx, {"nombre":"Delfín Nariz de Botella","cientifico":"Tursiops truncatus","habitat":"Océanos de todo el mundo","alimentacion":"Carnívoro (peces y calamares)","curiosidad":"Duermen con un ojo abierto","longevidad":"40-50 años","dato_extra":"Se reconocen en un espejo"}, "dolphin", "https://cdn.pixabay.com/photo/2014/11/19/21/49/dolphin-537891_640.jpg")

@bot.hybrid_command(name="panda",    description="Información y foto de un panda")
async def panda(ctx):
    await _animal_embed(ctx, {"nombre":"Panda Gigante","cientifico":"Ailuropoda melanoleuca","habitat":"Bosques de bambú de China","alimentacion":"Herbívoro (99% bambú)","curiosidad":"Pasan 12 horas al día comiendo","longevidad":"15-20 años en libertad","dato_extra":"Tienen un hueso extra en la muñeca para sujetar el bambú"}, "panda", "https://cdn.pixabay.com/photo/2017/09/13/01/08/panda-2744094_640.jpg")

@bot.hybrid_command(name="tiburon",  description="Información y foto de un tiburón")
async def tiburon(ctx):
    await _animal_embed(ctx, {"nombre":"Tiburón Blanco","cientifico":"Carcharodon carcharias","habitat":"Océanos de todo el mundo","alimentacion":"Carnívoro (focas, peces, calamares)","curiosidad":"Tienen electroreceptores para detectar presas","longevidad":"30-40 años","dato_extra":"Pueden perder hasta 30,000 dientes en su vida"}, "shark", "https://cdn.pixabay.com/photo/2013/10/02/23/10/shark-190274_640.jpg")

@bot.hybrid_command(name="buho",     description="Información y foto de un búho")
async def buho(ctx):
    await _animal_embed(ctx, {"nombre":"Búho Real","cientifico":"Bubo bubo","habitat":"Bosques y montañas de Europa, Asia y África","alimentacion":"Carnívoro (roedores, aves, insectos)","curiosidad":"Pueden girar la cabeza 270 grados","longevidad":"10-20 años","dato_extra":"Su vuelo es silencioso gracias a sus plumas"}, "owl", "https://cdn.pixabay.com/photo/2017/03/02/16/00/owl-2111222_640.jpg")

@bot.hybrid_command(name="cangrejo", description="Información y foto de un cangrejo")
async def cangrejo(ctx):
    await _animal_embed(ctx, {"nombre":"Cangrejo Ermitaño","cientifico":"Paguroidea","habitat":"Playas y océanos de todo el mundo","alimentacion":"Omnívoro (algas, restos de animales)","curiosidad":"Usan conchas de otros animales como casa","longevidad":"10-30 años","dato_extra":"Pueden regenerar sus pinzas"}, "crab", "https://cdn.pixabay.com/photo/2020/06/07/19/48/crab-5270499_640.jpg")

@bot.hybrid_command(name="mariposa", description="Información y foto de una mariposa")
async def mariposa(ctx):
    await _animal_embed(ctx, {"nombre":"Mariposa Monarca","cientifico":"Danaus plexippus","habitat":"América del Norte, bosques y jardines","alimentacion":"Néctar de flores","curiosidad":"Saborean con sus patas","longevidad":"2-6 semanas (migratorias hasta 8 meses)","dato_extra":"Vuelan hasta 4,000 km durante la migración"}, "butterfly", "https://cdn.pixabay.com/photo/2016/03/23/16/19/butterfly-1274974_640.jpg")

# =========================================================
# COMANDO PRIMER MENSAJE - Ver el primer mensaje del canal
# =========================================================

@bot.hybrid_command(name="primer-mensaje", description="Muestra el primer mensaje del canal")
async def primer_mensaje(ctx: commands.Context):
    """
    Muestra el primer mensaje enviado en el canal actual
    """
    
    await ctx.defer() if ctx.interaction else None
    
    try:
        # Obtener el historial del canal desde el principio
        async for message in ctx.channel.history(limit=1, oldest_first=True):
            primer_msg = message
            break
        else:
            embed = discord.Embed(
                title="Error",
                description="> No se pudo encontrar el primer mensaje del canal",
                color=AZUL_IPOD_NUM
            )
            await ctx.send(embed=embed)
            return
        
        # Información del primer mensaje
        autor = primer_msg.author
        contenido = primer_msg.content if primer_msg.content else "*[Sin texto, solo embed/imagen]*"
        fecha = primer_msg.created_at.strftime("%d/%m/%Y %H:%M:%S")
        enlace = primer_msg.jump_url
        
        # Limitar contenido si es muy largo
        if len(contenido) > 400:
            contenido = contenido[:400] + "..."
        
        # Crear embed
        embed = discord.Embed(
            title="Primer mensaje del canal",
            description=f"**Canal:** {ctx.channel.mention}\n**Autor:** {autor.mention}\n**Fecha:** {fecha}",
            color=AZUL_IPOD_NUM
        )
        embed.add_field(name="> Contenido", value=f"```{contenido}```", inline=False)
        embed.add_field(name="> Enlace", value=f"[Ir al mensaje]({enlace})", inline=False)
        
        if autor.avatar:
            embed.set_thumbnail(url=autor.display_avatar.url)
        
        embed.set_footer(text=f"ID del mensaje: {primer_msg.id}")
        
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        embed = discord.Embed(
            title="Error",
            description="> No tengo permisos para leer el historial de este canal",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="Error",
            description=f"> Error: `{str(e)[:100]}`",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@bot.hybrid_command(name="meme", description="Meme aleatorio de Reddit")
async def meme(ctx: commands.Context):
    await ctx.defer()
    subreddits = ["memes", "dankmemes", "memesESP", "goodanimemes"]
    subreddit = random.choice(subreddits)
    url = f"https://www.reddit.com/r/{subreddit}/random/.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                await ctx.send("> No se pudo obtener un meme")
                return
            data = await resp.json()
            post = data[0]['data']['children'][0]['data']
            embed = discord.Embed(title=post['title'], url=f"https://reddit.com{post['permalink']}", color=AZUL_IPOD_NUM)
            embed.set_image(url=post['url'])
            embed.set_footer(text=f"{post['ups']} | r/{subreddit}")
            await ctx.send(embed=embed)

@bot.hybrid_command(name="8ball", description="Preguntale algo al futuro")
async def eightball(ctx: commands.Context, *, pregunta: str):
    respuestas = ["Si", "No", "Tal vez", "Definitivamente si", "Ni lo sueñes", "Claro que si", "Las estrellas dicen que no", "Pregunta mas tarde", "No cuentes con ello"]
    embed = discord.Embed(title="Pregunta Magica", description=f"> **Pregunta:** {pregunta}\n> **Respuesta:** {random.choice(respuestas)}", color=AZUL_IPOD_NUM)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="horoscopo", description="Horoscopo del dia")
async def horoscopo(ctx: commands.Context, signo: str):
    signos = ["aries", "tauro", "geminis", "cancer", "leo", "virgo", "libra", "escorpio", "sagitario", "capricornio", "acuario", "piscis"]
    if signo.lower() not in signos:
        await ctx.send("> Signo no valido. Usa: aries, tauro, geminis, cancer, leo, virgo, libra, escorpio, sagitario, capricornio, acuario, piscis")
        return
    mensajes = ["Hoy es un buen dia para tomar decisiones importantes.", "El universo tiene planes positivos para ti.", "Evita conflictos innecesarios.", "Una oportunidad inesperada llegara a tu vida.", "La suerte esta de tu lado."]
    embed = discord.Embed(title=f"Horoscopo de {signo.capitalize()}", description=f"> {random.choice(mensajes)}", color=AZUL_IPOD_NUM)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="say", description="El bot repite tu mensaje")
async def say(ctx: commands.Context, *, mensaje: str):
    await ctx.send(mensaje)
    if ctx.interaction:
        await ctx.interaction.followup.send("> Mensaje enviado", ephemeral=True)
    else:
        await ctx.message.delete()

@bot.hybrid_command(name="roll", description="Elige un usuario al azar")
async def roll(ctx: commands.Context):
    miembros = [m for m in ctx.guild.members if not m.bot]
    if miembros:
        elegido = random.choice(miembros)
        embed = discord.Embed(title="Usuario aleatorio", description=f"> {elegido.mention} ha sido seleccionado", color=AZUL_IPOD_NUM)
        await ctx.send(embed=embed)

@bot.hybrid_command(name="timestamp", description="Convierte timestamp a fecha")
async def timestamp(ctx: commands.Context, timestamp: int):
    from datetime import datetime
    fecha = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
    embed = discord.Embed(title="Conversor de Timestamp", description=f"> Timestamp: `{timestamp}`\n> Fecha: `{fecha}`", color=AZUL_IPOD_NUM)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="banner", description="Banner del servidor")
async def banner(ctx: commands.Context):
    if ctx.guild.banner:
        embed = discord.Embed(title=f"Banner de {ctx.guild.name}", color=AZUL_IPOD_NUM)
        embed.set_image(url=ctx.guild.banner.url)
        await ctx.send(embed=embed)
    else:
        await ctx.send("> Este servidor no tiene banner")

@bot.hybrid_command(name="tragamonedas", description="Juego de tragamonedas")
async def tragamonedas(ctx: commands.Context, apuesta: int):
    data = get_user_eco(ctx.guild.id, ctx.author.id)
    if apuesta <= 0:
        return await ctx.send("> La apuesta debe ser positiva")
    if apuesta > data["coins"]:
        return await ctx.send(f"> No tenes suficientes monedas. Tenes ${data['coins']}")
    
    emojis = ["🐬", "🧊", "🌊", "🐳", "🐋", "💎", "🪼"]
    slot1 = random.choice(emojis)
    slot2 = random.choice(emojis)
    slot3 = random.choice(emojis)
    
    ganancia = 0
    if slot1 == slot2 == slot3 == "7️⃣":
        ganancia = apuesta * 10
        mensaje = "> JACKPOT! 3 SIETES!"
    elif slot1 == slot2 == slot3 == "💎":
        ganancia = apuesta * 5
        mensaje = "> PREMIO MAYOR! 3 DIAMANTES!"
    elif slot1 == slot2 == slot3:
        ganancia = apuesta * 3
        mensaje = "> 3 IGUALES!"
    elif slot1 == slot2 or slot2 == slot3 or slot1 == slot3:
        ganancia = apuesta * 1
        mensaje = "> PAR! Recuperas tu apuesta"
    else:
        ganancia = 0
        mensaje = "> Nada, perdiste"
    
    data["coins"] += ganancia - apuesta
    
    embed = discord.Embed(title="TRAGAMONEDAS", color=AZUL_IPOD_NUM)
    embed.add_field(name="> Resultado", value=f"```| {slot1} | {slot2} | {slot3} |```", inline=False)
    embed.add_field(name="> Apuesta", value=f"${apuesta}", inline=True)
    embed.add_field(name="> Ganancia", value=f"${ganancia}", inline=True)
    embed.add_field(name="> Resultado", value=mensaje, inline=False)
    embed.add_field(name="> Nuevo saldo", value=f"${data['coins']}", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="gayrate", description="Nivel de gay (broma)")
async def gayrate(ctx: commands.Context, usuario: discord.Member = None):
    usuario = usuario or ctx.author
    porcentaje = (usuario.id % 101)
    barra = "█" * (porcentaje // 10) + "░" * (10 - (porcentaje // 10))
    
    if porcentaje >= 80:
        texto = "> FOLLO CON UN CHICO"
    elif porcentaje >= 50:
        texto = "> Un poco... bastante"
    elif porcentaje >= 20:
        texto = "> Normal, nada del otro mundo"
    else:
        texto = "> Hetero nivel Dios"
    
    embed = discord.Embed(title=f"Nivel de gay de {usuario.display_name}", color=AZUL_IPOD_NUM)
    embed.add_field(name="> Porcentaje", value=f"```{barra} {porcentaje}%```", inline=False)
    embed.add_field(name="> Veredicto", value=texto, inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="insulto", description="Insulto creativo")
async def insulto(ctx: commands.Context, usuario: discord.Member = None):
    insultos = [
        "es mas lento que el inicio de Windows 95",
        "tiene menos memoria que un pez dorado",
        "es como un termo: util pero sin contenido propio",
        "le falta un hervor",
        "nacio de noche pero ese dia fue muy oscuro",
        "le pifian las ideas",
        "tiene menos neuronas que un pulpo en una ferreteria"
    ]
    insulto_elegido = random.choice(insultos)
    if usuario:
        await ctx.send(f"{usuario.mention} {insulto_elegido}")
    else:
        await ctx.send(f"{ctx.author.mention} {insulto_elegido}")

@bot.hybrid_command(name="robux", description="robux gratis de parte de Ron Weasley!!")
async def robux(ctx: commands.Context):
    await ctx.send("> Te dirigire a mi cuenta de Bankup y te dara una oferta, dale click [aqui](https://www.youtube.com/watch?v=dQw4w9WgXcQ)")

@bot.hybrid_command(name="secreto", description="Mensaje secreto")
async def secreto(ctx: commands.Context, *, mensaje: str):
    embed = discord.Embed(description=f"> {mensaje}", color=AZUL_IPOD_NUM)
    await ctx.send(embed=embed, ephemeral=True)

# =========================================================
# MENSAJES ANONIMOS
# Agrega este bloque a tu bot.py
# =========================================================

# --- DATA (agregar junto a tus otras variables globales) ---
# anon_config   = {}   # guild_id -> {"canal_id": int}
# anon_data     = {}   # guild_id -> [{"numero": int, "user_id": int, "contenido": str}, ...]
# anon_count    = {}   # guild_id -> int  (contador global)

anon_config = {}
anon_data   = {}
anon_count  = {}


# =========================================================
# MODAL — Escribir mensaje anonimo
# =========================================================

class ModalAnonimo(discord.ui.Modal, title="Mensaje Anónimo"):
    contenido = discord.ui.TextInput(
        label="Tu mensaje",
        style=discord.TextStyle.long,
        placeholder="Escribe aquí tu mensaje anónimo...",
        min_length=1,
        max_length=1000,
    )

    def __init__(self, canal_destino: discord.TextChannel):
        super().__init__()
        self.canal_destino = canal_destino

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)

        # Inicializar estructuras si no existen
        if gid not in anon_data:  anon_data[gid]  = []
        if gid not in anon_count: anon_count[gid] = 0

        # Incrementar contador y guardar registro
        anon_count[gid] += 1
        numero = anon_count[gid]

        anon_data[gid].append({
            "numero":    numero,
            "user_id":   interaction.user.id,
            "username":  str(interaction.user),
            "contenido": str(self.contenido),
        })

        # Embed del mensaje anonimo
        embed = discord.Embed(
            description=str(self.contenido),
            color=0x2B55B5
        )
        embed.set_footer(text=f"#{numero:03d}")

        # Vista con el boton para seguir enviando
        view = VistaBotonAnonimo(self.canal_destino)

        await self.canal_destino.send(embed=embed, view=view)

        # Confirmar al usuario en privado
        await interaction.response.send_message(
            "> Tu mensaje anónimo fue enviado correctamente.",
            ephemeral=True
        )


# =========================================================
# VISTA — Boton azul bajo cada mensaje
# =========================================================

class VistaBotonAnonimo(discord.ui.View):
    def __init__(self, canal_destino: discord.TextChannel):
        super().__init__(timeout=None)
        self.canal_destino = canal_destino

     @discord.ui.button(
        label="Enviar Anónimo",
        style=discord.ButtonStyle.primary,
        custom_id="btn_panel_anonimo",
        emoji="<:share:1505393406707372104>"
    )
    async def enviar_anonimo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalAnonimo(self.canal_destino))


# =========================================================
# VISTA — Boton del panel principal (persistente)
# =========================================================

class VistaPanelAnonimo(discord.ui.View):
    """
    Esta vista se adjunta al embed del panel.
    Usa custom_id fijo para que sobreviva reinicios si implementas
    persistencia; aquí se recrea en memoria al ejecutar /set-anonimos.
    """
    def __init__(self, canal_destino: discord.TextChannel):
        super().__init__(timeout=None)
        self.canal_destino = canal_destino

    @discord.ui.button(
        label="Enviar Anónimo",
        style=discord.ButtonStyle.primary,
        custom_id="btn_panel_anonimo",
        emoji="<:share:1505393406707372104>"
    )
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalAnonimo(self.canal_destino))


# =========================================================
# COMANDO — Configurar canal y enviar panel
# =========================================================

@bot.hybrid_command(
    name="set-anonimos",
    description="Configura el canal de mensajes anónimos y envía el panel."
)
@commands.has_permissions(administrator=True)
async def set_anonimos(ctx: commands.Context, canal: discord.TextChannel):
    await ctx.defer(ephemeral=True)

    gid = str(ctx.guild.id)
    anon_config[gid] = {"canal_id": canal.id}

    embed_panel = discord.Embed(
        title="Mensajes Anónimos",
        description=(
            "Estos son los mensajes anónimos, mensajes de cualquier usuario serán enviados aquí.\n\n"
            "> Interactúa con el botón de abajo para mandar tu mensaje anónimo."
        ),
        color=0x2B55B5
    )

    vista = VistaPanelAnonimo(canal)
    await canal.send(embed=embed_panel, view=vista)

    await ctx.followup.send(
        f"> Panel de mensajes anónimos enviado en {canal.mention}",
        ephemeral=True
    )


# =========================================================
# COMANDO — Revelar autor de un mensaje anonimo (solo admin)
# =========================================================

@bot.hybrid_command(
    name="revelar-anonimo",
    description="(ADMIN) Revela quién envió un mensaje anónimo por su número."
)
@commands.has_permissions(administrator=True)
async def revelar_anonimo(ctx: commands.Context, numero: int):
    await ctx.defer(ephemeral=True)

    gid = str(ctx.guild.id)

    if gid not in anon_data or not anon_data[gid]:
        await ctx.followup.send("> No hay mensajes anónimos registrados en este servidor.", ephemeral=True)
        return

    # Buscar el mensaje por número
    registro = next((r for r in anon_data[gid] if r["numero"] == numero), None)

    if not registro:
        await ctx.followup.send(f"> No se encontró el mensaje anónimo **#{numero:03d}**.", ephemeral=True)
        return

    miembro = ctx.guild.get_member(registro["user_id"])
    mencion = miembro.mention if miembro else f"ID: `{registro['user_id']}`"

    embed = discord.Embed(
        title=f"Revelación — Mensaje #{numero:03d}",
        color=0x2B55B5
    )
    embed.add_field(name="> Usuario",   value=f"{mencion}\n`{registro['username']}`", inline=False)
    embed.add_field(name="> Contenido", value=registro["contenido"][:1000],           inline=False)
    embed.set_footer(text="Esta información es solo visible para ti.")

    await ctx.followup.send(embed=embed, ephemeral=True)
        
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
