import discord
import os
import io
from datetime import datetime
import asyncio
import random
import json
import re
import time
import xml.etree.ElementTree as ET
import aiohttp
import urllib.parse
import hashlib
import datetime as dt
from email.utils import parsedate_to_datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from groq import AsyncGroq
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading
from dotenv import load_dotenv
import math
import copy
import textwrap

load_dotenv()

# =========================================================
# ARCHIVOS DE DATOS
# =========================================================

DB_WARNINGS = "data_warnings.json"
DB_XP = "data_xp.json"
DB_ECONOMIA = "data_economia.json"
DB_CLAVES = "data_claves.json"
DB_ANONIMOS = "data_anonimos.json"
DB_CONFIG = "data_config.json"
PLAYLIST_FILE = "playlists.json"
PERFILES_FILE = "data_perfiles.json"
PERFIL_SOCIAL_FILE = "data_perfil_social.json"
BUZON_FILE = "buzon.json"
CONFIG_FILE = "embed_configs.json"

# =========================================================
# FUNCIONES DE CARGA / GUARDADO
# =========================================================

def _cargar(archivo: str, default=None):
    if default is None:
        default = {}
    if not os.path.exists(archivo):
        return default
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def _guardar(archivo: str, data):
    try:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] No se pudo guardar {archivo}: {e}")

def _cargar_json(archivo, default=None):
    if default is None:
        default = {}
    if not os.path.exists(archivo):
        return default
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _guardar_json(archivo, data):
    try:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Guardando {archivo}: {e}")

# =========================================================
# CARGA INICIAL
# =========================================================

warnings_data = _cargar(DB_WARNINGS)
xp_data = _cargar(DB_XP)
economia_data = _cargar(DB_ECONOMIA)
claves_data = _cargar(DB_CLAVES)

_anon_raw = _cargar(DB_ANONIMOS, {"data": {}, "count": {}})
anon_data = _anon_raw.get("data", {})
anon_count = {k: int(v) for k, v in _anon_raw.get("count", {}).items()}

_cfg = _cargar(DB_CONFIG, {"nivel_canal": {}, "welc": {}, "bye": {}, "anon_config": {}})
nivel_canal = {int(k): v for k, v in _cfg.get("nivel_canal", {}).items()}
welc_config = {int(k): v for k, v in _cfg.get("welc", {}).items()}
bye_config = {int(k): v for k, v in _cfg.get("bye", {}).items()}
anon_config = _cfg.get("anon_config", {})

perfiles_data = _cargar_json(PERFILES_FILE)
social_data = _cargar_json(PERFIL_SOCIAL_FILE)
buzon_data = _cargar_json(BUZON_FILE)
configs = _cargar_json(CONFIG_FILE)

afk_data = {}
mensaje_count = {}
xp_cooldown = {}
cupones_data = {}
giveaways_activos = {}
puntuaciones_trivia = {}
memoria_usuarios = {}
autosay_users = {}

# =========================================================
# FUNCIONES DE GUARDADO
# =========================================================

def guardar_warnings(): _guardar(DB_WARNINGS, warnings_data)
def guardar_xp(): _guardar(DB_XP, xp_data)
def guardar_economia(): _guardar(DB_ECONOMIA, economia_data)
def guardar_claves(): _guardar(DB_CLAVES, claves_data)
def guardar_perfiles(): _guardar_json(PERFILES_FILE, perfiles_data)
def guardar_social(): _guardar_json(PERFIL_SOCIAL_FILE, social_data)
def guardar_buzon(): _guardar_json(BUZON_FILE, buzon_data)
def guardar_configs(): _guardar_json(CONFIG_FILE, configs)

def guardar_anonimos():
    _guardar(DB_ANONIMOS, {"data": anon_data, "count": anon_count})

def guardar_config():
    _guardar(DB_CONFIG, {
        "nivel_canal": {str(k): v for k, v in nivel_canal.items()},
        "welc": {str(k): v for k, v in welc_config.items()},
        "bye": {str(k): v for k, v in bye_config.items()},
        "anon_config": anon_config,
    })

def cargar_playlists():
    if not os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_playlists(data):
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =========================================================
# CONFIGURACION
# =========================================================

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
TOKEN = os.getenv("TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

AZUL_OSCURO = (25, 66, 156)
AZUL_IPOD = (25, 66, 156)
AZUL_IPOD_NUM = 0x19429c
BLANCO = (255, 255, 255)
FONDO_G = (10, 10, 10)
GRIS_G = (42, 42, 42)
TEXTO_G = (255, 255, 255)
SUB_G = (136, 136, 136)
OSCU_G = (15, 15, 15)

_CALC_ALLOWED = re.compile(r'^[\d\s\+\-\*\/\(\)\.\%\*\*]+$')
PALABRAS_IMAGEN = ["imagen", "foto", "dibujo", "genera", "wallpaper", "crea", "hazme",
                   "dibujame", "pintame", "ilustra", "generame", "muestrame"]
PALABRAS_AUDIO = ["audio", "habla", "di", "dime", "lee", "voz"]

_PERFIL_DEFAULT = {
    "nickname": "",
    "foto_url": "",
    "color_base": "c8a028",
    "estilo": "ninguno",
}

_SOCIAL_DEFAULT = {
    "seguidores": [],
    "likes": 0,
    "donaciones": 0,
    "comentarios": [],
}

ESTILOS_VALIDOS = [
    "ninguno", "basic", "futurista", "amor",
    "san patricio", "fuego", "horror", "sangre", "dark",
]

# =========================================================
# FUNCIONES DE SEPARADOR
# =========================================================

def sep():
    return "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

def crear_separador():
    return "─" * 45

def crear_titulo(texto: str) -> str:
    return f"**{texto.upper()}**"

# =========================================================
# BOT
# =========================================================

class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=">mt ", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()
        self.loop.create_task(tarea_autoguardado())

bot = DarkyBot()

# =========================================================
# AUTOGUARDADO CADA 5 MINUTOS
# =========================================================

async def tarea_autoguardado():
    await bot.wait_until_ready()
    while not bot.is_closed():
        guardar_warnings()
        guardar_xp()
        guardar_economia()
        guardar_claves()
        guardar_anonimos()
        guardar_config()
        guardar_perfiles()
        guardar_social()
        guardar_buzon()
        guardar_configs()
        await asyncio.sleep(300)

# =========================================================
# UTILIDADES DE IMAGEN
# =========================================================

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

def _avatar_cuadrado(av_img: Image.Image, size: int,
                     borde_color: tuple, radio: int = 8) -> Image.Image:
    av = av_img.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (size, size)],
                                           radius=radio, fill=255)
    res = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    res.paste(av, (0, 0), mask)

    bw = 3
    bs = size + bw * 2
    bi = Image.new("RGBA", (bs, bs), (0, 0, 0, 0))
    bm = Image.new("L", (bs, bs), 0)
    ImageDraw.Draw(bm).rounded_rectangle([(0, 0), (bs, bs)],
                                         radius=radio + bw, fill=255)
    bc = Image.new("RGBA", (bs, bs), (*borde_color, 255))
    bc.putalpha(bm)
    bi.paste(bc, (0, 0), bc)
    bi.paste(res, (bw, bw), res)
    return bi

def _avatar_gris(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (80, 80, 80, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 - 4
    r = size // 5
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(170, 170, 170))
    draw.ellipse([
        (int(cx - r * 1.4), int(cy + r * 0.6)),
        (int(cx + r * 1.4), int(cy + r * 2.6))
    ], fill=(150, 150, 150))
    return img

def _hex_rgb(hex_str: str) -> tuple:
    h = hex_str.strip().lstrip("#")
    if len(h) != 6:
        return (200, 160, 40)
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (200, 160, 40)

def _gradiente_v(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img

# =========================================================
# HELPERS DE DATOS
# =========================================================

def get_xp(guild_id, user_id):
    gid, uid = str(guild_id), str(user_id)
    if gid not in xp_data:
        xp_data[gid] = {}
    if uid not in xp_data[gid]:
        xp_data[gid][uid] = {"xp": 0, "level": 1}
    return xp_data[gid][uid]

def xp_para_nivel(nivel):
    return nivel * 100

def get_user_eco(guild_id, user_id):
    gid, uid = str(guild_id), str(user_id)
    if gid not in economia_data:
        economia_data[gid] = {}
    if uid not in economia_data[gid]:
        economia_data[gid][uid] = {"coins": 0, "last_daily": 0}
    return economia_data[gid][uid]

def get_user_claves(guild_id, user_id):
    gid, uid = str(guild_id), str(user_id)
    if gid not in claves_data:
        claves_data[gid] = {}
    if uid not in claves_data[gid]:
        claves_data[gid][uid] = {}
    return claves_data[gid][uid]

def get_perfil(guild_id, user_id) -> dict:
    gid, uid = str(guild_id), str(user_id)
    perfiles_data.setdefault(gid, {})
    if uid not in perfiles_data[gid]:
        perfiles_data[gid][uid] = copy.deepcopy(_PERFIL_DEFAULT)
    for k, v in _PERFIL_DEFAULT.items():
        perfiles_data[gid][uid].setdefault(k, v)
    return perfiles_data[gid][uid]

def get_social(guild_id, user_id) -> dict:
    gid, uid = str(guild_id), str(user_id)
    social_data.setdefault(gid, {})
    if uid not in social_data[gid]:
        social_data[gid][uid] = copy.deepcopy(_SOCIAL_DEFAULT)
    for k, v in _SOCIAL_DEFAULT.items():
        social_data[gid][uid].setdefault(k, v)
    return social_data[gid][uid]

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

def parse_text(texto, member):
    if not texto:
        return ""
    return texto.replace("{user_name}", member.name) \
        .replace("{user_mention}", member.mention) \
        .replace("{user_id}", str(member.id)) \
        .replace("{server_name}", member.guild.name) \
        .replace("{user_avatar}", str(member.display_avatar.url))

def reemplazar_variables(texto: str, member: discord.Member = None, guild: discord.Guild = None) -> str:
    if not texto:
        return texto

    if member:
        texto = texto.replace("{user_name}", member.display_name)
        texto = texto.replace("{user_avatar}", str(member.display_avatar.url))
        texto = texto.replace("{user_id}", str(member.id))

    if guild:
        texto = texto.replace("{server_name}", guild.name)
        texto = texto.replace("{server_avatar}", str(guild.icon.url) if guild.icon else "")
        texto = texto.replace("{server_id}", str(guild.id))
        texto = texto.replace("{user_count}", str(guild.member_count))

    texto = texto.replace("{date}", datetime.now().strftime("%d/%m/%Y %H:%M"))
    return texto

# =========================================================
# GENERADORES DE IMAGEN
# =========================================================

async def generar_userinfo(usuario: discord.Member) -> discord.File:
    W, H = 700, 340
    FONDO_USER = (30, 31, 34)
    TEXTO_USER = (255, 255, 255)
    SUBTEXTO_USER = (180, 180, 190)
    CAMPO_FONDO = (40, 43, 48)
    img = Image.new("RGBA", (W, H), FONDO_USER)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (6, H)], fill=AZUL_OSCURO)
    avatar_img = await descargar_imagen(str(usuario.display_avatar.url))
    avatar_img = avatar_circular(avatar_img, 90)
    img.paste(avatar_img, (24, 20), avatar_img)
    draw.text((128, 22), usuario.display_name, font=fuente(26, bold=True), fill=TEXTO_USER)
    draw.text((128, 56), f"@{usuario.name}", font=fuente(16), fill=SUBTEXTO_USER)
    draw.rectangle([(24, 126), (W - 24, 128)], fill=(60, 63, 70))
    col1_x, col2_x, y = 24, 370, 148

    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, fill=CAMPO_FONDO)
        draw.text((x + 12, y + 8), titulo, font=fuente(13), fill=SUBTEXTO_USER)
        draw.text((x + 12, y + 30), valor, font=fuente(17, bold=True), fill=TEXTO_USER)

    campo(col1_x, y, "USUARIO", f"@{usuario.display_name}")
    campo(col2_x, y, "ID", str(usuario.id))
    y2 = y + 80
    campo(col1_x, y2, "CUENTA CREADA", usuario.created_at.strftime("%d/%m/%Y"))
    campo(col2_x, y2, "ENTRO AL SERVER", usuario.joined_at.strftime("%d/%m/%Y") if usuario.joined_at else "?")
    draw.text((24, H - 22), f"Solicitado por {usuario.display_name}", font=fuente(12), fill=SUBTEXTO_USER)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="userinfo.png")

async def generar_serverinfo(guild: discord.Guild, solicitante: discord.Member) -> discord.File:
    W, H = 700, 400
    CAMPO_FONDO = (20, 20, 20)
    CAMPO_BORDE = (50, 50, 60)
    img = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (6, H)], fill=AZUL_OSCURO)
    if guild.icon:
        icon_img = await descargar_imagen(str(guild.icon.url))
        icon_img = avatar_circular(icon_img, 90)
        img.paste(icon_img, (24, 20), icon_img)
        nombre_x = 128
    else:
        nombre_x = 24
    draw.ellipse([(22, 18), (116, 112)], outline=AZUL_OSCURO, width=2)
    draw.text((nombre_x, 22), guild.name, font=fuente(26, bold=True), fill=TEXTO_G)
    draw.text((nombre_x, 56), f"ID: {guild.id}", font=fuente(14), fill=SUB_G)
    draw.rectangle([(24, 126), (W - 24, 127)], fill=AZUL_OSCURO)

    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, fill=CAMPO_FONDO)
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, outline=CAMPO_BORDE, width=1)
        draw.text((x + 12, y + 8), titulo, font=fuente(13), fill=SUB_G)
        draw.text((x + 12, y + 30), str(valor), font=fuente(17, bold=True), fill=TEXTO_G)

    y = 148
    campo(24, y, "OWNER", guild.owner.display_name if guild.owner else "?")
    campo(370, y, "CREADO", guild.created_at.strftime("%d/%m/%Y"))
    y2, a3 = y + 80, 204
    campo(24, y2, "MIEMBROS", str(guild.member_count), ancho=a3)
    campo(24 + 224, y2, "ROLES", str(len(guild.roles)), ancho=a3)
    campo(24 + 448, y2, "EMOJIS", str(len(guild.emojis)), ancho=a3)
    y3 = y2 + 80
    campo(24, y3, "TEXTO", str(len(guild.text_channels)), ancho=a3)
    campo(24 + 224, y3, "VOZ", str(len(guild.voice_channels)), ancho=a3)
    campo(24 + 448, y3, "BOOSTS", f"{guild.premium_subscription_count} (nv {guild.premium_tier})", ancho=a3)
    draw.text((24, H - 22), f"Solicitado por {solicitante.display_name}", font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="serverinfo.png")

async def generar_nivel(usuario: discord.Member, nivel: int, xp: int, xp_needed: int) -> discord.File:
    W, H = 680, 180
    img = Image.new("RGBA", (W, H), FONDO_G)
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
    progreso = min(xp / xp_needed, 1.0) if xp_needed > 0 else 0
    fill_w = int(162 + (468 * progreso))
    if fill_w > 162:
        draw.rounded_rectangle([(162, 118), (fill_w, 130)], radius=6, fill=AZUL_OSCURO)
    draw.text((162, 152), f"Subiste al nivel {nivel} — sigue asi!", font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="nivel.png")

async def generar_balance(usuario: discord.Member, coins: int, last_daily: float) -> discord.File:
    W, H = 680, 170
    img = Image.new("RGBA", (W, H), FONDO_G)
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
        if hace < 3600:
            daily_texto = f"Ultimo daily: hace {hace // 60} minutos"
        elif hace < 86400:
            daily_texto = f"Ultimo daily: hace {hace // 3600} horas"
        else:
            daily_texto = f"Ultimo daily: hace {hace // 86400} dias"
    draw.text((158, 148), daily_texto, font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="balance.png")

async def generar_ranking(guild: discord.Guild, top: list) -> discord.File:
    filas = len(top)
    W, H = 680, 130 + (filas * 46)
    img = Image.new("RGBA", (W, H), FONDO_G)
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
        draw.text((54, y + 10), f"#{n+1}", font=fuente(14, bold=True), fill=AZUL_OSCURO if n == 0 else SUB_G)
        draw.text((90, y + 10), nombre, font=fuente(13, bold=n == 0), fill=TEXTO_G)
        draw.text((620, y + 10), f"$ {data['coins']:,}", font=fuente(13), fill=AZUL_OSCURO if n == 0 else SUB_G, anchor="ra")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ranking.png")

async def generar_ban(usuario: discord.Member, razon: str, moderador: discord.Member) -> discord.File:
    W, H = 680, 190
    img = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 47), av)
    except:
        draw.ellipse([(37, 47), (133, 143)], fill=GRIS_G)
    draw.ellipse([(35, 45), (135, 145)], outline=AZUL_OSCURO, width=2)
    draw.line([(50, 60), (120, 130)], fill=AZUL_OSCURO, width=3)
    draw.line([(120, 60), (50, 130)], fill=AZUL_OSCURO, width=3)
    draw.text((158, 42), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO_G)
    draw.rounded_rectangle([(158, 68), (228, 90)], radius=11, fill=AZUL_OSCURO)
    draw.text((193, 74), "Baneado", font=fuente(12, bold=True), fill=TEXTO_G, anchor="mt")
    draw.rectangle([(158, 104), (645, 105)], fill=GRIS_G)
    draw.text((158, 116), "RAZON", font=fuente(11), fill=SUB_G)
    draw.text((158, 134), (razon[:50] + "..." if len(razon) > 50 else razon), font=fuente(15, bold=True), fill=TEXTO_G)
    draw.text((158, 164), f"Moderador: {moderador.display_name}", font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ban.png")

async def generar_afk(usuario: discord.Member, motivo: str) -> discord.File:
    W, H = 680, 190
    img = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 47), av)
    except:
        draw.ellipse([(37, 47), (133, 143)], fill=GRIS_G)
    draw.ellipse([(35, 45), (135, 145)], outline=AZUL_OSCURO, width=2)
    draw.text((98, 72), "z", font=fuente(17, bold=True), fill=BLANCO)
    draw.text((110, 58), "z", font=fuente(14, bold=True), fill=BLANCO)
    draw.text((120, 46), "z", font=fuente(11), fill=BLANCO)
    draw.text((158, 42), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO_G)
    draw.rounded_rectangle([(158, 68), (218, 90)], radius=11, fill=AZUL_OSCURO)
    draw.text((188, 74), "AFK", font=fuente(12, bold=True), fill=FONDO_G, anchor="mt")
    draw.rectangle([(158, 104), (645, 105)], fill=GRIS_G)
    draw.text((158, 116), "MOTIVO", font=fuente(11), fill=SUB_G)
    draw.text((158, 134), (motivo[:50] + "..." if len(motivo) > 50 else motivo), font=fuente(15, bold=True), fill=TEXTO_G)
    draw.text((158, 164), "Te avisare si te mencionan...", font=fuente(12), fill=SUB_G)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="afk.png")

async def generar_warn(usuario: discord.Member, razon: str, total: int) -> discord.File:
    W, H = 680, 180
    img = Image.new("RGBA", (W, H), FONDO_G)
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
    draw.text((162, 122), (razon[:50] + "..." if len(razon) > 50 else razon), font=fuente(15, bold=True), fill=TEXTO_G)
    draw.text((162, 154), f"Total de warns: {total}", font=fuente(12), fill=AZUL_OSCURO)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="warn.png")

async def generar_warnings_img(usuario: discord.Member, warns: list) -> discord.File:
    filas = min(len(warns), 10)
    W, H = 680, 90 + (filas * 44)
    img = Image.new("RGBA", (W, H), FONDO_G)
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

async def generar_ship(u1: discord.Member, u2: discord.Member, pct: int) -> discord.File:
    W, H = 680, 200
    img = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    for av_data, x in [(u1, 30), (u2, 540)]:
        try:
            av = await descargar_imagen(str(av_data.display_avatar.url))
            av = avatar_circular(av, 110)
            img.paste(av, (x, 45), av)
        except:
            draw.ellipse([(x, 45), (x+110, 155)], fill=GRIS_G)
        draw.ellipse([(x-2, 43), (x+112, 157)], outline=AZUL_OSCURO, width=2)
    n1 = u1.display_name[:14] + "..." if len(u1.display_name) > 14 else u1.display_name
    n2 = u2.display_name[:14] + "..." if len(u2.display_name) > 14 else u2.display_name
    draw.text((85, 162), n1, font=fuente(13, bold=True), fill=TEXTO_G, anchor="mt")
    draw.text((595, 162), n2, font=fuente(13, bold=True), fill=TEXTO_G, anchor="mt")
    draw.rounded_rectangle([(160, 82), (520, 118)], radius=18, fill=GRIS_G)
    fill_w = int(160 + (360 * pct / 100))
    if fill_w > 160:
        draw.rounded_rectangle([(160, 82), (fill_w, 118)], radius=18, fill=AZUL_OSCURO)
    draw.text((340, 100), f"{pct}%", font=fuente(20, bold=True), fill=TEXTO_G, anchor="mm")
    if pct >= 90:
        frase = "Almas gemelas de otra dimension"
    elif pct >= 75:
        frase = "El amor es inevitable entre estos dos"
    elif pct >= 60:
        frase = "Hay chispa, pero falta avivarlo"
    elif pct >= 40:
        frase = "Podria funcionar... o no"
    elif pct >= 20:
        frase = "Mejor como amigos"
    else:
        frase = "Incompatibles al maximo nivel"
    draw.text((340, 140), frase, font=fuente(12), fill=SUB_G, anchor="mt")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ship.png")

async def generar_logro(usuario: discord.Member, titulo: str, descripcion: str) -> discord.File:
    W, H = 680, 160
    img = Image.new("RGBA", (W, H), (10, 10, 10))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    cx, cy, radio = 80, 76, 48
    draw.ellipse([(cx-radio, cy-radio), (cx+radio, cy+radio)], fill=(25, 25, 25), outline=AZUL_OSCURO, width=2)
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, radio * 2)
        img.paste(av, (cx-radio, cy-radio), av)
        draw.ellipse([(cx-radio, cy-radio), (cx+radio, cy+radio)], outline=AZUL_OSCURO, width=2)
    except:
        draw.ellipse([(cx-14, cy-28), (cx+14, cy)], fill=GRIS_G)
        draw.ellipse([(cx-26, cy+2), (cx+26, cy+46)], fill=GRIS_G)
    tx = 155
    draw.text((tx, 18), "LOGRO DESBLOQUEADO", font=fuente(12, bold=True), fill=AZUL_OSCURO)
    draw.rectangle([(tx, 38), (W-24, 39)], fill=GRIS_G)
    draw.text((tx, 48), (titulo[:38] + "..." if len(titulo) > 38 else titulo), font=fuente(20, bold=True), fill=TEXTO_G)
    draw.text((tx, 80), (descripcion[:60] + "..." if len(descripcion) > 60 else descripcion), font=fuente(13), fill=(160, 163, 172))
    nombre = usuario.display_name[:22] + "..." if len(usuario.display_name) > 22 else usuario.display_name
    draw.text((tx, 114), f"Logrado por {nombre}", font=fuente(12), fill=(160, 163, 172))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="logro.png")

async def generar_spotify_card(usuario: discord.Member, actividad: discord.Spotify) -> discord.File:
    W, H = 680, 180
    img = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    try:
        portada = await descargar_imagen(actividad.album_cover_url)
        portada = portada.resize((130, 130)).convert("RGBA")
        mask = Image.new("L", (130, 130), 0)
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
    ahora = discord.utils.utcnow()
    duracion = actividad.duration.total_seconds()
    transcurrido = (ahora - actividad.start).total_seconds()
    progreso = min(transcurrido / duracion, 1.0) if duracion > 0 else 0
    draw.rounded_rectangle([(182, 128), (645, 136)], radius=4, fill=GRIS_G)
    fill_w = int(182 + (463 * progreso))
    if fill_w > 182:
        draw.rounded_rectangle([(182, 128), (fill_w, 136)], radius=4, fill=BLANCO)
    fmt = lambda s: f"{int(s)//60}:{int(s)%60:02}"
    draw.text((182, 148), fmt(max(transcurrido, 0)), font=fuente(11), fill=SUB_G)
    draw.text((645, 148), fmt(duracion), font=fuente(11), fill=SUB_G, anchor="ra")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="spotify.png")

# =========================================================
# GENERADOR DE TARJETA DE PERFIL
# =========================================================

def _dibujar_estilo(draw: ImageDraw.Draw, img: Image.Image,
                    estilo: str, cb: tuple, W: int, H: int):
    if estilo == "ninguno":
        return

    elif estilo == "basic":
        for i in range(3):
            draw.rectangle([(i, i), (W-1-i, H-1-i)], outline=(255, 255, 255))
        for i in range(3, 6):
            draw.rectangle([(i, i), (W-1-i, H-1-i)], outline=(0, 0, 0))
        sq = 10
        corners = [(0, 0), (W-sq, 0), (0, H-sq), (W-sq, H-sq)]
        for cx2, cy2 in corners:
            draw.rectangle([(cx2, cy2), (cx2+sq, cy2+sq)], fill=(255, 255, 255))
        sq2 = 6
        corners2 = [(2, 2), (W-sq2-2, 2), (2, H-sq2-2), (W-sq2-2, H-sq2-2)]
        for cx2, cy2 in corners2:
            draw.rectangle([(cx2, cy2), (cx2+sq2, cy2+sq2)], fill=(0, 0, 0))
        draw.line([(0, H//2), (W, H//2)], fill=(255, 255, 255, 40), width=1)

    elif estilo == "futurista":
        c = (0, 220, 255)
        corner = 24
        lw = 2
        for off in range(3):
            o = off
            draw.line([(o, o), (o+corner, o)], fill=c, width=lw)
            draw.line([(o, o), (o, o+corner)], fill=c, width=lw)
            draw.line([(W-1-o, o), (W-1-o-corner, o)], fill=c, width=lw)
            draw.line([(W-1-o, o), (W-1-o, o+corner)], fill=c, width=lw)
            draw.line([(o, H-1-o), (o+corner, H-1-o)], fill=c, width=lw)
            draw.line([(o, H-1-o), (o, H-1-o-corner)], fill=c, width=lw)
            draw.line([(W-1-o, H-1-o), (W-1-o-corner, H-1-o)], fill=c, width=lw)
            draw.line([(W-1-o, H-1-o), (W-1-o, H-1-o-corner)], fill=c, width=lw)
        draw.line([(corner+8, 1), (W-corner-8, 1)], fill=(*c, 80), width=1)
        draw.line([(corner+8, H-2), (W-corner-8, H-2)], fill=(*c, 80), width=1)
        draw.ellipse([(W//2-3, H-8), (W//2+3, H-2)], fill=c)

    elif estilo == "amor":
        c = (255, 100, 160)
        for i in range(3):
            draw.rectangle([(i, i), (W-1-i, H-1-i)], outline=(*c, 160))

        def corazon(x, y, s=16):
            draw.ellipse([(x, y), (x+s, y+s)], fill=(*c, 200))
            draw.ellipse([(x+s, y), (x+s*2, y+s)], fill=(*c, 200))
            draw.polygon([
                (x, y+s//2),
                (x+s, y+s*2),
                (x+s*2, y+s//2)
            ], fill=(*c, 200))

        corazon(4, 4)
        corazon(W-38, 4)
        corazon(4, H-38)
        corazon(W-38, H-38)
        for bx in range(80, W-80, 60):
            draw.ellipse([(bx-4, 1), (bx+2, 7)], fill=(*c, 120))
            draw.ellipse([(bx+2, 1), (bx+8, 7)], fill=(*c, 120))
            draw.polygon([(bx-4, 5), (bx+2, 12), (bx+8, 5)], fill=(*c, 120))

    elif estilo == "san patricio":
        c = (60, 200, 80)
        for i in range(3):
            draw.rectangle([(i, i), (W-1-i, H-1-i)], outline=(*c, 180))

        def trebol(cx2, cy2, r=9):
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                ox2 = int(cx2 + r * math.cos(rad))
                oy2 = int(cy2 + r * math.sin(rad))
                draw.ellipse([(ox2-r, oy2-r), (ox2+r, oy2+r)], fill=(*c, 200))
            draw.rectangle([(cx2-2, cy2), (cx2+2, cy2+r+4)], fill=(*c, 200))

        trebol(20, 20)
        trebol(W-20, 20)
        trebol(20, H-20)
        trebol(W-20, H-20)
        for x in range(40, W-40, 12):
            draw.ellipse([(x, 4), (x+4, 8)], fill=(*c, 100))
            draw.ellipse([(x, H-8), (x+4, H-4)], fill=(*c, 100))

    elif estilo == "fuego":
        colores_fuego = [(255, 50, 0), (255, 140, 0), (255, 220, 0)]
        for i in range(3):
            draw.rectangle([(i, i), (W-1-i, H-1-i)], outline=colores_fuego[i])
        rng = random.Random(13)
        for fx in range(30, W-30, 18):
            altura = rng.randint(8, 22)
            grosor = rng.randint(3, 7)
            c_llama = colores_fuego[rng.randint(0, 2)]
            draw.polygon([
                (fx, H-1),
                (fx+grosor, H-1),
                (fx+grosor//2, H-1-altura)
            ], fill=(*c_llama, 180))
        for _ in range(20):
            sx = rng.randint(10, W-10)
            sy = rng.randint(H-40, H-5)
            draw.ellipse([(sx, sy), (sx+2, sy+2)], fill=(255, 255, 100, 200))

    elif estilo == "horror":
        c = (140, 0, 200)
        rng = random.Random(42)
        for side in range(4):
            if side == 0:
                pts = [(x, rng.randint(0, 7)) for x in range(0, W, 5)]
            elif side == 1:
                pts = [(W-1-rng.randint(0, 7), y) for y in range(0, H, 5)]
            elif side == 2:
                pts = [(x, H-1-rng.randint(0, 7)) for x in range(0, W, 5)]
            else:
                pts = [(rng.randint(0, 7), y) for y in range(0, H, 5)]
            for i in range(len(pts)-1):
                draw.line([pts[i], pts[i+1]], fill=(*c, 200), width=2)
        for ex, ey in [(12, 12), (W-32, 12), (12, H-30), (W-32, H-30)]:
            draw.ellipse([(ex, ey), (ex+20, ey+16)], outline=(*c, 200), width=1)
            draw.ellipse([(ex+5, ey+3), (ex+15, ey+13)], fill=(*c, 180))
            draw.ellipse([(ex+8, ey+5), (ex+12, ey+9)], fill=(0, 0, 0))

    elif estilo == "sangre":
        c = (190, 10, 30)
        for i in range(3):
            draw.rectangle([(i, i), (W-1-i, H-1-i)], outline=(*c, 200-i*30))
        rng = random.Random(7)
        for _ in range(10):
            gx = rng.randint(20, W-20)
            largo = rng.randint(12, 35)
            grosor = rng.randint(3, 7)
            draw.rectangle([(gx, 0), (gx+grosor, largo)], fill=(*c, 220))
            draw.ellipse([
                (gx - grosor//2, largo),
                (gx + grosor + grosor//2, largo + grosor*2)
            ], fill=(*c, 220))
        for _ in range(6):
            gx = rng.randint(20, W-20)
            largo = rng.randint(8, 20)
            grosor = rng.randint(2, 5)
            draw.rectangle([(gx, H-largo), (gx+grosor, H)], fill=(*c, 180))
            draw.ellipse([
                (gx - grosor//2, H-largo-grosor*2),
                (gx + grosor + grosor//2, H-largo)
            ], fill=(*c, 180))

    elif estilo == "dark":
        grises = [(60, 60, 60), (40, 40, 40), (25, 25, 25), (10, 10, 10), (0, 0, 0)]
        for i, g in enumerate(grises):
            draw.rectangle([(i, i), (W-1-i, H-1-i)], outline=g)
        sq = 14
        for cx2, cy2 in [(0, 0), (W-sq, 0), (0, H-sq), (W-sq, H-sq)]:
            draw.rectangle([(cx2, cy2), (cx2+sq, cy2+sq)], fill=(0, 0, 0))
        for length in range(5, 30, 5):
            draw.line([(0, length), (length, 0)], fill=(40, 40, 40), width=1)
            draw.line([(W-length, 0), (W, length)], fill=(40, 40, 40), width=1)
            draw.line([(0, H-length), (length, H)], fill=(40, 40, 40), width=1)
            draw.line([(W-length, H), (W, H-length)], fill=(40, 40, 40), width=1)

async def generar_tarjeta_perfil(
    usuario: discord.Member,
    perfil: dict,
    social: dict,
    es_preview: bool = False,
) -> discord.File:

    W, H = 780, 270
    cb = _hex_rgb(perfil.get("color_base", "c8a028"))
    cb2 = tuple(max(0, c - 40) for c in cb)
    est = perfil.get("estilo", "ninguno")

    img = _gradiente_v(W, H, (28, 20, 10), (18, 12, 6)).convert("RGBA")
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 8):
        for y in range(0, H, 8):
            draw.point((x, y), fill=(*cb, 14))

    draw.rectangle([(3, 3), (W-4, H-4)], outline=(*cb, 180), width=2)
    draw.rectangle([(7, 7), (W-8, H-8)], outline=(*cb2, 120), width=1)

    for ox, oy in [(10, 10), (W-30, 10), (10, H-30), (W-30, H-30)]:
        draw.ellipse([(ox, oy), (ox+18, oy+18)], outline=(*cb, 200), width=2)
        draw.ellipse([(ox+4, oy+4), (ox+14, oy+14)], fill=(*cb, 100))

    av_raw = None
    foto_url = perfil.get("foto_url", "").strip()
    if foto_url:
        try:
            av_raw = await descargar_imagen(foto_url)
        except:
            pass
    if av_raw is None:
        try:
            av_raw = await descargar_imagen(str(usuario.display_avatar.url))
        except Exception:
            pass
    if av_raw is None:
        av_raw = _avatar_gris(110)

    av = _avatar_cuadrado(av_raw, 110, cb, 8)
    img.paste(av, (26, (H - av.height) // 2), av)

    nombre = (perfil.get("nickname") or "").strip() or usuario.display_name
    draw.text((156, 22), nombre, font=fuente(22, True), fill=(*cb, 255))

    draw.line([(156, 50), (W-26, 50)], fill=(*cb, 160), width=1)
    draw.line([(156, 53), (W-26, 53)], fill=(*cb2, 100), width=1)

    draw.text((156, 60), f"✦  @{usuario.name}  ✦",
              font=fuente(12), fill=(*cb2, 200))

    stats = [
        ("SEGUIDORES", str(len(social.get("seguidores", [])))),
        ("LIKES", str(social.get("likes", 0))),
        ("DONACIONES", str(social.get("donaciones", 0))),
        ("COMENTARIOS", str(len(social.get("comentarios", [])))),
    ]
    col_w = (W - 156 - 26) // 4
    for i, (label, val) in enumerate(stats):
        x = 156 + i * col_w + col_w // 2
        bx = 156 + i * col_w + 8
        draw.rounded_rectangle(
            [(bx, 88), (bx + col_w - 16, 160)],
            radius=6, fill=(0, 0, 0, 60)
        )
        draw.rounded_rectangle(
            [(bx, 88), (bx + col_w - 16, 160)],
            radius=6, outline=(*cb, 120), width=1
        )
        draw.text((x, 96), val, font=fuente(26, True), fill=(*cb, 255), anchor="mt")
        draw.text((x, 130), label, font=fuente(10), fill=(*cb2, 200), anchor="mt")

    draw.line([(26, H-46), (W-26, H-46)], fill=(*cb, 120), width=1)
    draw.text((W//2, H-36), f"~ @{usuario.name} ~",
              font=fuente(12), fill=(*cb2, 160), anchor="mt")

    if es_preview:
        draw.text((W-14, H-14), "PREVIEW",
                  font=fuente(10, True), fill=(*cb, 130), anchor="rb")

    _dibujar_estilo(draw, img, est, cb, W, H)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="perfil.png")

# =========================================================
# IA — HELPERS
# =========================================================

async def generar_imagen_pillow(prompt: str) -> tuple:
    prompt_limpio = prompt.lower()
    for p in PALABRAS_IMAGEN:
        prompt_limpio = prompt_limpio.replace(p, "")
    prompt_limpio = re.sub(r'\s+', ' ', prompt_limpio).strip() or prompt

    W, H = 512, 512
    img = Image.new("RGB", (W, H), (20, 22, 30))
    draw = ImageDraw.Draw(img)

    for y in range(H):
        r = int(20 + (80 * (y / H)))
        g = int(22 + (40 * (y / H)))
        b = int(30 + (120 * (y / H)))
        draw.rectangle([(0, y), (W, y + 1)], fill=(r, g, b))

    for _ in range(5):
        x = random.randint(0, W)
        y = random.randint(0, H)
        radius = random.randint(30, 120)
        alpha = random.randint(20, 60)
        color = (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200),
            alpha
        )
        circle = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle)
        circle_draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], fill=color)
        img = Image.alpha_composite(img.convert("RGBA"), circle).convert("RGB")

    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)

    palabras = prompt_limpio[:200].split()
    lineas = []
    linea_actual = ""
    for palabra in palabras:
        if len(linea_actual + " " + palabra) < 20:
            linea_actual += " " + palabra if linea_actual else palabra
        else:
            if linea_actual:
                lineas.append(linea_actual)
            linea_actual = palabra
    if linea_actual:
        lineas.append(linea_actual)

    y_pos = 100
    for linea in lineas[:6]:
        try:
            font = fuente(28, bold=True)
            bbox = draw.textbbox((0, 0), linea, font=font)
            text_width = bbox[2] - bbox[0]
            x_pos = (W - text_width) // 2
            draw.text((x_pos, y_pos), linea, font=font, fill=(255, 255, 255))
            y_pos += 50
        except:
            draw.text((50, y_pos), linea, fill=(255, 255, 255))
            y_pos += 40

    seed = random.randint(1, 999999)
    draw.text((10, H - 30), f"Seed: {seed}", font=fuente(12), fill=(100, 100, 120))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return buf.read(), prompt_limpio, seed

async def generar_audio_pollinations(texto: str, voz: str = "nova") -> tuple:
    texto_limpio = urllib.parse.quote(texto[:500])
    url = f"https://gen.pollinations.ai/audio/{texto_limpio}?voice={voz}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    audio_data = await resp.read()
                    return audio_data, "mp3", None
                else:
                    return None, None, f"Error de la API: {resp.status}"
    except Exception as e:
        return None, None, str(e)

async def generar_imagen_ia(mensaje: str):
    prompt = mensaje.lower()
    for p in PALABRAS_IMAGEN:
        prompt = prompt.replace(p, "")
    prompt = re.sub(r'\s+', ' ', prompt).strip() or mensaje

    try:
        img_data, prompt_limpio, seed = await generar_imagen_pillow(prompt)
        if img_data:
            return img_data, prompt_limpio, seed
    except Exception as e:
        print(f"Error en Pillow: {e}")

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
            model="llama-3.3-70b-versatile", messages=mensajes_api,
            temperature=0.8, max_tokens=500)
        texto = respuesta.choices[0].message.content
        return texto[:500] + "..." if len(texto) > 500 else texto
    except Exception as e:
        print(f"Error Groq: {e}")
        return "Tuve un problema al procesar tu mensaje, intentalo de nuevo."

# =========================================================
# LAST.FM — HELPER
# =========================================================

async def buscar_cancion_exacta(artista: str, cancion: str) -> dict:
    if not LASTFM_API_KEY:
        return None
    url = (f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo"
           f"&api_key={LASTFM_API_KEY}&artist={urllib.parse.quote(artista.strip())}"
           f"&track={urllib.parse.quote(cancion.strip())}&format=json")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        if "error" in data:
            return None
        track = data.get("track")
        if not track:
            return None
        nombre = track.get("name", cancion)
        artista_nombre = track.get("artist", {}).get("name", artista)
        album = track.get("album", {}).get("title", "Sin álbum")
        duracion_seg = int(track.get("duration") or 0)
        duracion_texto = f"{duracion_seg//60}:{duracion_seg%60:02d}" if duracion_seg else "Desconocida"
        imagenes = track.get("album", {}).get("image", [])
        cover_url = next((img["#text"] for img in reversed(imagenes) if img.get("#text")), "")
        try:
            oyentes_num = int(track.get("listeners", 0))
            oyentes_texto = f"{oyentes_num/1_000_000:.1f}M" if oyentes_num >= 1_000_000 else f"{oyentes_num/1_000:.1f}K" if oyentes_num >= 1_000 else str(oyentes_num)
        except:
            oyentes_texto = "N/A"
        año = ""
        fecha_raw = track.get("album", {}).get("date", {})
        if isinstance(fecha_raw, dict):
            fecha_texto = fecha_raw.get("#text", "")
            if fecha_texto and len(fecha_texto) >= 4:
                año = fecha_texto[:4]
        return {"nombre": nombre, "artista": artista_nombre, "album": album,
                "duracion": duracion_texto, "cover": cover_url,
                "url": track.get("url", ""), "año": año, "oyentes": oyentes_texto}
    except Exception as e:
        print(f"Error buscar_cancion_exacta: {e}")
        return None

async def obtener_foto_artista(nombre_artista: str) -> str:
    if LASTFM_API_KEY:
        try:
            url = (f"http://ws.audioscrobbler.com/2.0/?method=artist.getInfo"
                   f"&api_key={LASTFM_API_KEY}&artist={urllib.parse.quote(nombre_artista.strip())}&format=json")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        imagenes = data.get("artist", {}).get("image", [])
                        PLACEHOLDER = "2a96cbd8b46e442fc41c2b86b821562f"
                        for img in reversed(imagenes):
                            texto = img.get("#text", "")
                            if texto and PLACEHOLDER not in texto:
                                return texto
        except:
            pass
    try:
        mb_url = (f"https://musicbrainz.org/ws/2/artist/?query=artist:{urllib.parse.quote(nombre_artista.strip())}&fmt=json&limit=1")
        headers = {"User-Agent": "MistiBot/1.0 (discord bot)"}
        async with aiohttp.ClientSession() as session:
            async with session.get(mb_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return ""
                mb_data = await resp.json()
                artistas = mb_data.get("artists", [])
                if not artistas:
                    return ""
                mbid = artistas[0].get("id", "")
            if not mbid:
                return ""
            rel_url = f"https://musicbrainz.org/ws/2/artist/{mbid}?inc=url-rels&fmt=json"
            async with session.get(rel_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return ""
                rel_data = await resp.json()
                relaciones = rel_data.get("relations", [])
            wikidata_id, wiki_title = "", ""
            for rel in relaciones:
                url_rel = rel.get("url", {}).get("resource", "")
                if "wikidata.org/wiki/" in url_rel:
                    wikidata_id = url_rel.split("/wiki/")[-1]
                if "wikipedia.org/wiki/" in url_rel and not wiki_title:
                    wiki_title = url_rel.split("/wiki/")[-1]
            if wikidata_id:
                wd_url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"
                async with session.get(wd_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        wd_data = await resp.json()
                        claims = wd_data.get("entities", {}).get(wikidata_id, {}).get("claims", {})
                        imagenes_wd = claims.get("P18", [])
                        if imagenes_wd:
                            nombre_archivo = imagenes_wd[0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
                            if nombre_archivo:
                                nombre_enc = nombre_archivo.replace(" ", "_")
                                md5 = hashlib.md5(nombre_enc.encode()).hexdigest()
                                return (f"https://upload.wikimedia.org/wikipedia/commons/"
                                        f"{md5[0]}/{md5[0:2]}/{urllib.parse.quote(nombre_enc)}")
            if wiki_title:
                wp_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
                async with session.get(wp_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        wp_data = await resp.json()
                        thumbnail = wp_data.get("thumbnail", {}).get("source", "")
                        if thumbnail:
                            return re.sub(r'/\d+px-', '/800px-', thumbnail)
    except Exception as e:
        print(f"[obtener_foto_artista] Error: {e}")
    return ""

# =========================================================
# GRUPOS DE COMANDOS HÍBRIDOS
# =========================================================

# =========================================================
# GRUPO 1: MODERACIÓN (/mod)
# =========================================================

@bot.hybrid_group(name="mod", description="Comandos de moderación", fallback="help")
async def mod_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="MODERACIÓN",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`ban` - Banea a un usuario\n"
                       "`kick` - Expulsa a un usuario\n"
                       "`warn` - Advierte a un usuario\n"
                       "`warn-list` - Ver warns de un usuario\n"
                       "`delete` - Elimina mensajes\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@mod_group.command(name="ban", description="Banea a un usuario")
@commands.has_permissions(ban_members=True)
async def mod_ban(ctx: commands.Context, usuario: discord.Member, *, razon: str = "Sin razon"):
    if ctx.interaction:
        await ctx.defer()
    if usuario == ctx.author:
        await ctx.send("> No puedes banearte a ti mismo", ephemeral=True)
        return
    try:
        await usuario.ban(reason=razon)
        await ctx.send(file=await generar_ban(usuario, razon, ctx.author))
    except Exception as e:
        await ctx.send(f"> Error:\n```{e}```")

@mod_group.command(name="kick", description="Expulsa a un usuario")
@commands.has_permissions(kick_members=True)
async def mod_kick(ctx: commands.Context, usuario: discord.Member, *, razon: str = "Sin razon"):
    if ctx.interaction:
        await ctx.defer()
    if usuario == ctx.author:
        await ctx.send("> No puedes expulsarte a ti mismo")
        return
    try:
        await usuario.kick(reason=razon)
        embed = discord.Embed(color=AZUL_IPOD_NUM)
        embed.description = f"> **{usuario.display_name}** fue expulsado\n> Razon: {razon}\n> Moderador: {ctx.author.mention}"
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error:\n```{e}```")

@mod_group.command(name="warn", description="Advierte a un usuario")
@commands.has_permissions(manage_messages=True)
async def mod_warn(ctx: commands.Context, usuario: discord.Member, *, razon: str = "Sin razon"):
    if ctx.interaction:
        await ctx.defer()
    guild_id = str(ctx.guild.id)
    user_id = str(usuario.id)
    if guild_id not in warnings_data:
        warnings_data[guild_id] = {}
    if user_id not in warnings_data[guild_id]:
        warnings_data[guild_id][user_id] = []
    warnings_data[guild_id][user_id].append({
        "razon": razon,
        "moderador": str(ctx.author),
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    })
    total = len(warnings_data[guild_id][user_id])
    embed = discord.Embed(
        title="WARN",
        description=(
            f"{sep()}\n\n"
            f"USUARIO: {usuario.mention}\n"
            f"RAZON: {razon}\n"
            f"TOTAL WARNS: {total}\n"
            f"MODERADOR: {ctx.author.mention}\n\n"
            f"{sep()}"
        ),
        color=AZUL_IPOD_NUM
    )
    embed.set_footer(text="Misti - Sistema de Warns")
    await ctx.send(embed=embed)

@mod_group.command(name="warn-list", description="Ver warns de un usuario")
@commands.has_permissions(manage_messages=True)
async def mod_warn_list(ctx: commands.Context, usuario: discord.Member):
    if ctx.interaction:
        await ctx.defer()
    guild_id = str(ctx.guild.id)
    user_id = str(usuario.id)
    if guild_id not in warnings_data or user_id not in warnings_data[guild_id]:
        embed = discord.Embed(
            title="WARNS",
            description=(
                f"{sep()}\n\n"
                f"{usuario.mention} no tiene warns\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        embed.set_footer(text="Misti - Lista de Warns")
        await ctx.send(embed=embed)
        return
    warns = warnings_data[guild_id][user_id]
    view = WarnListView(ctx.author.id, warns)
    await ctx.send(embed=view.get_embed(usuario), view=view)

@mod_group.command(name="delete", description="Elimina mensajes del canal")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def mod_delete(ctx: commands.Context, cantidad: int, usuario: discord.Member = None):
    is_slash = ctx.interaction is not None
    if is_slash:
        await ctx.defer(ephemeral=True)
    if cantidad < 1 or cantidad > 1000:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                "La cantidad debe ser entre 1 y 1000\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed, ephemeral=is_slash)
        return
    if not is_slash:
        await ctx.message.delete()
    if usuario:
        def check(m):
            return m.author == usuario
        eliminados = await ctx.channel.purge(limit=cantidad, check=check)
    else:
        eliminados = await ctx.channel.purge(limit=cantidad)
    embed = discord.Embed(
        title="✅ DELETE",
        description=(
            f"{sep()}\n\n"
            f"**MENSAJES ELIMINADOS:** {len(eliminados)}\n"
            f"**CANAL:** {ctx.channel.mention}\n"
            f"**USUARIO FILTRADO:** {usuario.mention if usuario else 'Ninguno'}\n\n"
            f"{sep()}"
        ),
        color=AZUL_IPOD_NUM
    )
    embed.set_footer(text="Misti - Delete")
    await ctx.send(embed=embed, ephemeral=is_slash)

# =========================================================
# GRUPO 2: ECONOMÍA (/eco)
# =========================================================

@bot.hybrid_group(name="eco", description="Comandos de economía", fallback="help")
async def eco_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="ECONOMÍA",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`balance` - Ver saldo\n"
                       "`daily` - Reclamar daily\n"
                       "`ranking` - Top usuarios\n"
                       "`canjear` - Canjear cupón\n\n"
                       "**Administración:**\n"
                       "`dar` - Agregar monedas\n"
                       "`quitar` - Quitar monedas\n"
                       "`cupon` - Crear cupón\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@eco_group.command(name="balance", description="Ve tu saldo actual")
async def eco_balance(ctx: commands.Context, usuario: discord.Member = None):
    if ctx.interaction:
        await ctx.defer()
    usuario = ctx.guild.get_member((usuario or ctx.author).id)
    data = get_user_eco(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@eco_group.command(name="daily", description="Reclama tus monedas diarias")
async def eco_daily(ctx: commands.Context):
    if ctx.interaction:
        await ctx.defer()
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
    guardar_economia()
    await ctx.send(content=f"> Recibiste **{recompensa}** monedas!",
                   file=await generar_balance(ctx.guild.get_member(ctx.author.id), data["coins"], data["last_daily"]))

@eco_group.command(name="ranking", description="Top usuarios con más monedas")
async def eco_ranking(ctx: commands.Context):
    if ctx.interaction:
        await ctx.defer()
    gid = str(ctx.guild.id)
    if gid not in economia_data or not economia_data[gid]:
        await ctx.send("> Nadie tiene monedas todavia.")
        return
    top = sorted(economia_data[gid].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
    await ctx.send(file=await generar_ranking(ctx.guild, top))

@eco_group.command(name="dar", description="(ADMIN) Agrega monedas a un usuario")
@commands.has_permissions(administrator=True)
async def eco_dar(ctx: commands.Context, usuario: discord.Member, cantidad: int):
    if ctx.interaction:
        await ctx.defer()
    data = get_user_eco(ctx.guild.id, usuario.id)
    data["coins"] += cantidad
    guardar_economia()
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Se agregaron **${cantidad:,}** a {usuario.mention}\n> Saldo: **${data['coins']:,}**"
    await ctx.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@eco_group.command(name="quitar", description="(ADMIN) Quita monedas a un usuario")
@commands.has_permissions(administrator=True)
async def eco_quitar(ctx: commands.Context, usuario: discord.Member, cantidad: int):
    if ctx.interaction:
        await ctx.defer()
    data = get_user_eco(ctx.guild.id, usuario.id)
    data["coins"] = max(0, data["coins"] - cantidad)
    guardar_economia()
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Se quitaron **${cantidad:,}** a {usuario.mention}\n> Saldo: **${data['coins']:,}**"
    await ctx.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@eco_group.command(name="cupon", description="(ADMIN) Crea un cupón de recompensa")
@commands.has_permissions(administrator=True)
async def eco_cupon(ctx: commands.Context, codigo: str, recompensa: int):
    gid = str(ctx.guild.id)
    if gid not in cupones_data:
        cupones_data[gid] = {}
    cupones_data[gid][codigo.upper()] = {"recompensa": recompensa, "usado_por": []}
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Cupon `{codigo.upper()}` creado\n> Recompensa: **${recompensa:,}**"
    await ctx.send(embed=embed)

@eco_group.command(name="canjear", description="Canjea un cupón de recompensa")
async def eco_canjear(ctx: commands.Context, codigo: str):
    gid = str(ctx.guild.id)
    if gid not in cupones_data or codigo.upper() not in cupones_data[gid]:
        await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> Cupon invalido"))
        return
    cupon = cupones_data[gid][codigo.upper()]
    if ctx.author.id in cupon["usado_por"]:
        await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> Ya usaste este cupon"))
        return
    cupon["usado_por"].append(ctx.author.id)
    eco = get_user_eco(ctx.guild.id, ctx.author.id)
    eco["coins"] += cupon["recompensa"]
    guardar_economia()
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> Canjeado! Ganaste: **${cupon['recompensa']:,}**"))

# =========================================================
# GRUPO 3: NIVELES (/nivel)
# =========================================================

@bot.hybrid_group(name="nivel", description="Comandos de niveles", fallback="help")
async def nivel_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="NIVELES",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`ver` - Ver tu nivel actual\n\n"
                       "**Administración:**\n"
                       "`canal` - Configurar canal de niveles\n"
                       "`agregar` - Agregar niveles\n"
                       "`quitar` - Quitar niveles\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@nivel_group.command(name="ver", description="Ve tu nivel actual")
async def nivel_ver(ctx: commands.Context, usuario: discord.Member = None):
    if ctx.interaction:
        await ctx.defer()
    usuario = ctx.guild.get_member((usuario or ctx.author).id)
    data = get_xp(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@nivel_group.command(name="canal", description="(ADMIN) Canal donde se anuncian los niveles")
@commands.has_permissions(administrator=True)
async def nivel_canal_cmd(ctx: commands.Context, canal: discord.TextChannel):
    nivel_canal[ctx.guild.id] = canal.id
    guardar_config()
    await ctx.send(f"> Canal de niveles seteado en {canal.mention}")

@nivel_group.command(name="agregar", description="(ADMIN) Agrega niveles a un usuario")
@commands.has_permissions(administrator=True)
async def nivel_agregar(ctx: commands.Context, usuario: discord.Member, cantidad: int):
    if ctx.interaction:
        await ctx.defer()
    data = get_xp(ctx.guild.id, usuario.id)
    data["level"] += cantidad
    guardar_xp()
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Se agregaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await ctx.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@nivel_group.command(name="quitar", description="(ADMIN) Quita niveles a un usuario")
@commands.has_permissions(administrator=True)
async def nivel_quitar(ctx: commands.Context, usuario: discord.Member, cantidad: int):
    if ctx.interaction:
        await ctx.defer()
    data = get_xp(ctx.guild.id, usuario.id)
    data["level"] = max(1, data["level"] - cantidad)
    guardar_xp()
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Se quitaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await ctx.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

# =========================================================
# GRUPO 4: UTILIDADES (/util)
# =========================================================

@bot.hybrid_group(name="util", description="Comandos de utilidad", fallback="help")
async def util_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="UTILIDADES",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`usuario` - Información de un usuario\n"
                       "`servidor` - Información del servidor\n"
                       "`avatar` - Ver avatar de un usuario\n"
                       "`ping` - Latencia del bot\n"
                       "`calcular` - Calcula una operación\n"
                       "`qr` - Genera un código QR\n"
                       "`color` - Muestra un color HEX\n"
                       "`afk` - Activa tu modo AFK\n"
                       "`doctor` - Diagnóstico de permisos\n"
                       "`say` - El bot repite lo que digas\n"
                       "`autosay` - Activa/desactiva modo espejo\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@util_group.command(name="usuario", description="Información de un usuario")
async def util_usuario(ctx: commands.Context, usuario: discord.Member = None):
    if ctx.interaction:
        await ctx.defer()
    usuario = ctx.guild.get_member((usuario or ctx.author).id)
    await ctx.send(file=await generar_userinfo(usuario))

@util_group.command(name="servidor", description="Información del servidor")
async def util_servidor(ctx: commands.Context):
    if ctx.interaction:
        await ctx.defer()
    await ctx.send(file=await generar_serverinfo(ctx.guild, ctx.author))

@util_group.command(name="avatar", description="Ver avatar de un usuario")
async def util_avatar(ctx: commands.Context, usuario: discord.Member = None):
    usuario = usuario or ctx.author
    embed = discord.Embed(title=f"Avatar de {usuario.name}", color=AZUL_IPOD_NUM)
    embed.set_image(url=usuario.display_avatar.url)
    await ctx.send(embed=embed)

@util_group.command(name="ping", description="Latencia del bot")
async def util_ping(ctx: commands.Context):
    ms = round(bot.latency * 1000)
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Pong! `{ms}ms`"
    await ctx.send(embed=embed)

@util_group.command(name="calcular", description="Calcula una operación matemática")
async def util_calcular(ctx: commands.Context, *, operacion: str):
    if not _CALC_ALLOWED.match(operacion):
        await ctx.send("> Solo se permiten operaciones básicas (+, -, *, /, **, %)")
        return
    try:
        resultado = eval(operacion, {"__builtins__": {}}, {})
        embed = discord.Embed(color=AZUL_IPOD_NUM)
        embed.description = f"> **Operación:** {operacion}\n> **Resultado:** {resultado}"
        await ctx.send(embed=embed)
    except ZeroDivisionError:
        await ctx.send("> División entre cero")
    except:
        await ctx.send("> Operación inválida")

@util_group.command(name="qr", description="Genera un código QR")
async def util_qr(ctx: commands.Context, *, texto: str):
    url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(texto)}"
    embed = discord.Embed(title="Código QR", description=f"**Contenido:** {texto[:100]}{'...' if len(texto)>100 else ''}", color=AZUL_IPOD_NUM)
    embed.set_image(url=url)
    await ctx.send(embed=embed)

@util_group.command(name="color", description="Muestra un color HEX o genera uno aleatorio")
async def util_color(ctx: commands.Context, hex_code: str = None):
    if not hex_code:
        hex_code = ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
        es_aleatorio = True
    else:
        hex_code = hex_code.strip().lstrip('#').upper()
        es_aleatorio = False
    if not re.match(r'^[0-9A-F]{6}$', hex_code):
        await ctx.send(f"> HEX inválido: `{hex_code}`")
        return
    r, g, b = int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)
    r_c, g_c, b_c = 255-r, 255-g, 255-b
    hex_comp = f"{r_c:02X}{g_c:02X}{b_c:02X}"
    img = Image.new("RGB", (400, 200), (r, g, b))
    draw = ImageDraw.Draw(img)
    draw.text((200, 80), f"#{hex_code}", font=fuente(24, bold=True), fill=(255, 255, 255), anchor="mm")
    draw.text((200, 120), f"RGB({r}, {g}, {b})", font=fuente(16), fill=(255, 255, 255), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    archivo = discord.File(buf, filename="color.png")
    embed = discord.Embed(title="Color Aleatorio" if es_aleatorio else "Color", color=int(hex_code, 16))
    embed.add_field(name="> Código HEX", value=f"`#{hex_code}`", inline=True)
    embed.add_field(name="> RGB", value=f"`({r}, {g}, {b})`", inline=True)
    embed.add_field(name="> Complementario", value=f"`#{hex_comp}`", inline=True)
    embed.set_image(url="attachment://color.png")
    await ctx.send(embed=embed, file=archivo)

@util_group.command(name="afk", description="Activa tu modo AFK")
async def util_afk(ctx: commands.Context, *, motivo: str = "Sin motivo"):
    if ctx.interaction:
        await ctx.defer()
    afk_data[ctx.author.id] = {"motivo": motivo, "tiempo": time.time()}
    usuario = ctx.guild.get_member(ctx.author.id)
    await ctx.send(file=await generar_afk(usuario, motivo))

@util_group.command(name="doctor", description="Diagnóstico de permisos del bot")
async def util_doctor(ctx: commands.Context):
    if ctx.interaction:
        await ctx.defer()
    me = ctx.guild.me
    cp = ctx.channel.permissions_for(me)
    gp = me.guild_permissions
    permisos_canal = {
        "Ver Canal": cp.view_channel, "Enviar Mensajes": cp.send_messages,
        "Crear Embeds": cp.embed_links, "Adjuntar Archivos": cp.attach_files,
        "Emojis Externos": cp.use_external_emojis, "Añadir Reacciones": cp.add_reactions,
        "Leer Historial": cp.read_message_history,
    }
    permisos_servidor = {
        "Administrador": gp.administrator, "Gestionar Mensajes": gp.manage_messages,
        "Gestionar Canales": gp.manage_channels, "Gestionar Roles": gp.manage_roles,
        "Expulsar Miembros": gp.kick_members, "Banear Miembros": gp.ban_members,
        "Silenciar Miembros": gp.mute_members,
    }
    def fmt(d):
        return "\n".join(f"{'✅' if v else '❌'} **{k}**" for k, v in d.items())
    embed = discord.Embed(title="Diagnóstico del Bot", description="Estado de permisos", color=AZUL_IPOD_NUM)
    embed.add_field(name="Canal", value=fmt(permisos_canal), inline=False)
    embed.add_field(name="Servidor", value=fmt(permisos_servidor), inline=False)
    errores = [k for k, v in permisos_canal.items() if not v]
    if gp.administrator:
        diagnostico = "> Tiene permiso de **Administrador**. Sin restricciones."
    elif not errores:
        diagnostico = "> ¡Excelente! Todos los permisos fundamentales activos."
    else:
        diagnostico = f"> Faltan permisos: **{', '.join(errores[:2])}**"
    embed.add_field(name="Conclusión", value=diagnostico, inline=False)
    embed.set_footer(text=f"Latencia: {round(bot.latency * 1000)}ms", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@util_group.command(name="say", description="El bot repite lo que digas")
async def util_say(ctx: commands.Context, *, mensaje: str):
    await ctx.send(mensaje)
    if ctx.message:
        await ctx.message.delete()

@util_group.command(name="autosay", description="Activa/desactiva el modo espejo")
async def util_autosay(ctx: commands.Context):
    user_id = ctx.author.id
    status = not autosay_users.get(user_id, False)
    autosay_users[user_id] = status
    await ctx.send(f"Auto-say: {'Activado' if status else 'Desactivado'}")

# =========================================================
# GRUPO 5: INFO Y BUSQUEDAS (/info)
# =========================================================

@bot.hybrid_group(name="info", description="Comandos de información y búsquedas", fallback="help")
async def info_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="INFO Y BUSQUEDAS",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`roblox` - Perfil de Roblox\n"
                       "`pokemon` - Información de Pokémon\n"
                       "`pais` - Información de un país\n"
                       "`pelicula` - Busca una película\n"
                       "`clima` - Clima actual\n"
                       "`google` - Busca en Google\n"
                       "`imagenes` - Busca imágenes\n"
                       "`lugares` - Busca lugares\n"
                       "`noticias` - Últimas noticias\n"
                       "`steam` - Busca un juego en Steam\n"
                       "`nasa` - Foto astronómica del día\n"
                       "`covid` - Datos de COVID-19\n"
                       "`traducir` - Traduce texto\n"
                       "`recetas` - Busca recetas\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@info_group.command(name="roblox", description="Perfil de Roblox de un usuario")
async def info_roblox(ctx: commands.Context, *, usuario: str):
    if ctx.interaction:
        await ctx.defer()
    try:
        async with aiohttp.ClientSession() as session:
            data_user = {"usernames": [usuario], "excludeBannedUsers": False}
            async with session.post("https://users.roblox.com/v1/usernames/users", json=data_user) as resp:
                if resp.status != 200:
                    await ctx.send("> Error conectando con Roblox")
                    return
                res_user = await resp.json()
                if not res_user["data"]:
                    await ctx.send(f"> El usuario **{usuario}** no existe")
                    return
                user_info = res_user["data"][0]
                user_id = user_info["id"]
                roblox_user = user_info["name"]
                display_name = user_info["displayName"]
            async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as resp:
                res_details = await resp.json()
                fecha_iso = res_details["created"].split("T")[0]
                cuenta_creada = datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
            async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count") as resp:
                cantidad_amigos = (await resp.json()).get("count", 0)
            estado_texto = "Desconectado"
            async with session.post("https://presence.roblox.com/v1/presence/users", json={"userIds": [user_id]}) as resp:
                presence_data = await resp.json()
                presence = presence_data["userPresences"][0]
                status_type = presence["userPresenceType"]
                if status_type == 0:
                    estado_texto = "Desconectado"
                elif status_type == 1:
                    estado_texto = "En línea"
                elif status_type == 2:
                    estado_texto = f"Jugando: {presence.get('lastLocation', 'Desconocido')}"
            avatar_url = "https://images.rbxcdn.com/default_avatar.png"
            async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false") as resp:
                if resp.status == 200:
                    res_thumb = await resp.json()
                    if res_thumb["data"]:
                        avatar_url = res_thumb["data"][0]["imageUrl"]
        embed = discord.Embed(color=AZUL_IPOD_NUM, title="Perfil de Roblox")
        embed.add_field(name="Usuario", value=roblox_user, inline=True)
        embed.add_field(name="ID", value=user_id, inline=True)
        embed.add_field(name="Apodo", value=display_name, inline=False)
        embed.add_field(name="Estado", value=estado_texto, inline=True)
        embed.add_field(name="Cuenta Creada", value=cuenta_creada, inline=True)
        embed.add_field(name="Amigos", value=cantidad_amigos, inline=True)
        embed.add_field(name="Perfil", value=f"[ver](https://www.roblox.com/users/{user_id}/profile)", inline=False)
        embed.set_thumbnail(url=avatar_url)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error: {str(e)[:100]}")

@info_group.command(name="pokemon", description="Información de un Pokémon")
async def info_pokemon(ctx: commands.Context, *, nombre: str):
    if ctx.interaction:
        await ctx.defer()
    url = f"https://pokeapi.co/api/v2/pokemon/{urllib.parse.quote(nombre.lower().strip())}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send(f"> No se encontró el Pokémon: **{nombre}**")
                return
            data = await resp.json()
    embed = discord.Embed(title=f"{data.get('name', nombre).capitalize()} #{data.get('id', 0)}", color=AZUL_IPOD_NUM)
    embed.add_field(name="> Altura", value=f"{data.get('height', 0)/10} m", inline=True)
    embed.add_field(name="> Peso", value=f"{data.get('weight', 0)/10} kg", inline=True)
    embed.add_field(name="> Tipo", value=", ".join([t['type']['name'].capitalize() for t in data.get('types', [])]), inline=True)
    embed.add_field(name="> Habilidades", value=", ".join([h['ability']['name'].capitalize() for h in data.get('abilities', [])[:3]]), inline=False)
    stats = {s['stat']['name']: s['base_stat'] for s in data.get('stats', [])}
    if stats:
        embed.add_field(name="> HP", value=stats.get('hp', 0), inline=True)
        embed.add_field(name="> Ataque", value=stats.get('attack', 0), inline=True)
        embed.add_field(name="> Defensa", value=stats.get('defense', 0), inline=True)
    sprite = data.get('sprites', {}).get('front_default', '')
    if sprite:
        embed.set_thumbnail(url=sprite)
    await ctx.send(embed=embed)

@info_group.command(name="pais", description="Informacion de un pais")
async def info_pais(ctx: commands.Context, *, nombre: str):
    if ctx.interaction:
        await ctx.defer()
    try:
        url = f"https://restcountries.com/v3.1/name/{urllib.parse.quote(nombre)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 404:
                    embed = discord.Embed(
                        title="ERROR",
                        description=(
                            f"{sep()}\n\n"
                            f"Pais no encontrado: {nombre}\n\n"
                            f"{sep()}"
                        ),
                        color=AZUL_IPOD_NUM
                    )
                    await ctx.send(embed=embed)
                    return
                if resp.status != 200:
                    embed = discord.Embed(
                        title="ERROR",
                        description=(
                            f"{sep()}\n\n"
                            f"Error al conectar con la API: {resp.status}\n\n"
                            f"{sep()}"
                        ),
                        color=AZUL_IPOD_NUM
                    )
                    await ctx.send(embed=embed)
                    return
                data = await resp.json()
        if not data:
            embed = discord.Embed(
                title="ERROR",
                description=(
                    f"{sep()}\n\n"
                    f"No se encontraron datos para: {nombre}\n\n"
                    f"{sep()}"
                ),
                color=AZUL_IPOD_NUM
            )
            await ctx.send(embed=embed)
            return
        d = data[0]
        nombre_oficial = d.get('name', {}).get('official', 'Desconocido')
        capital = ", ".join(d.get('capital', ['Desconocida']))
        poblacion = f"{d.get('population', 0):,}"
        area = f"{d.get('area', 0):,} km²"
        idiomas = ", ".join(d.get('languages', {}).values())[:50]
        moneda_data = d.get('currencies', {})
        if moneda_data:
            moneda = list(moneda_data.values())[0].get('name', 'Desconocida')
        else:
            moneda = 'Desconocida'
        mapa = d.get('maps', {}).get('googleMaps', '')
        bandera = d.get('flags', {}).get('png', '')
        embed = discord.Embed(
            title=f"{nombre_oficial}",
            description=f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        if bandera:
            embed.set_thumbnail(url=bandera)
        embed.add_field(
            name="INFORMACION",
            value=(
                f"> CAPITAL: {capital}\n"
                f"> POBLACION: {poblacion}\n"
                f"> AREA: {area}\n"
                f"> IDIOMAS: {idiomas}\n"
                f"> MONEDA: {moneda}"
            ),
            inline=False
        )
        if mapa:
            embed.add_field(
                name="GOOGLE MAPS",
                value=f"[Ver mapa en Google Maps]({mapa})",
                inline=False
            )
        embed.add_field(
            name="",
            value=f"\n{sep()}",
            inline=False
        )
        embed.set_footer(text="RestCountries API - Misti")
        await ctx.send(embed=embed)
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                "Tiempo de espera agotado\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                f"Error: {str(e)[:100]}\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@info_group.command(name="pelicula", description="Busca información de una película")
async def info_pelicula(ctx: commands.Context, *, nombre: str):
    if ctx.interaction:
        await ctx.defer()
    if not TMDB_API_KEY:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                "**TMDB_API_KEY no configurada**\n\n"
                "El administrador debe agregar `TMDB_API_KEY` en Render.\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={urllib.parse.quote(nombre)}&language=es"
        ) as resp:
            data = await resp.json()
            resultados = data.get('results', [])
            if not resultados:
                embed = discord.Embed(
                    title="ERROR",
                    description=(
                        f"{sep()}\n\n"
                        f"**No se encontró la película:** {nombre}\n\n"
                        f"{sep()}"
                    ),
                    color=AZUL_IPOD_NUM
                )
                await ctx.send(embed=embed)
                return
            peli = resultados[0]
        async with session.get(
            f"https://api.themoviedb.org/3/movie/{peli.get('id')}?api_key={TMDB_API_KEY}&language=es"
        ) as resp:
            detalles = await resp.json()
    titulo = detalles.get('title', 'Sin título')
    fecha = detalles.get('release_date', 'Desconocida')[:4]
    duracion = detalles.get('runtime', 0)
    generos = ", ".join([g.get('name', '') for g in detalles.get('genres', [])])
    descripcion = detalles.get('overview', 'Sin descripción')
    puntaje = detalles.get('vote_average', 0)
    poster = detalles.get('poster_path', '')
    embed = discord.Embed(
        title=f"{titulo} ({fecha})",
        description=(
            f"{sep()}\n\n"
            f"{descripcion[:300] + '...' if len(descripcion) > 300 else descripcion}\n\n"
            f"{sep()}"
        ),
        color=AZUL_IPOD_NUM
    )
    if poster:
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{poster}")
    embed.add_field(
        name="INFORMACIÓN",
        value=(
            f"**> PUNTUACIÓN:** {puntaje}/10\n"
            f"**> DURACIÓN:** {duracion} min\n"
            f"**> GÉNEROS:** {generos[:50]}"
        ),
        inline=False
    )
    embed.add_field(
        name="",
        value=f"\n{sep()}",
        inline=False
    )
    embed.set_footer(text="The Movie Database (TMDB) • Misti")
    await ctx.send(embed=embed)

@info_group.command(name="clima", description="Clima actual de una ciudad")
async def info_clima(ctx: commands.Context, *, ciudad: str):
    if ctx.interaction:
        await ctx.defer()
    if not WEATHER_API_KEY:
        await ctx.send("> `WEATHER_API_KEY` no configurada.")
        return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.openweathermap.org/data/2.5/weather?q={urllib.parse.quote(ciudad)}&appid={WEATHER_API_KEY}&units=metric&lang=es") as resp:
                if resp.status == 404:
                    await ctx.send(f"> Ciudad **{ciudad}** no encontrada.")
                    return
                if resp.status != 200:
                    await ctx.send(f"> Error ({resp.status})")
                    return
                datos = await resp.json()
    except Exception as e:
        await ctx.send(f"> Error de conexión: ```{str(e)}```")
        return
    embed = discord.Embed(title=f"Clima en {datos['name']}, {datos['sys']['country']}", color=AZUL_IPOD_NUM)
    embed.add_field(name="> Temperatura", value=f"{datos['main']['temp']}°C", inline=True)
    embed.add_field(name="> Sensación", value=f"{datos['main']['feels_like']}°C", inline=True)
    embed.add_field(name="> Humedad", value=f"{datos['main']['humidity']}%", inline=True)
    embed.add_field(name="> Viento", value=f"{datos['wind']['speed']} m/s", inline=True)
    embed.add_field(name="> Descripción", value=datos['weather'][0]['description'].capitalize(), inline=False)
    embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{datos['weather'][0]['icon']}@2x.png")
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@info_group.command(name="google", description="Busca en Google")
async def info_google(ctx: commands.Context, *, query: str):
    if ctx.interaction:
        await ctx.defer()
    if not SERPER_API_KEY:
        await ctx.send("> `SERPER_API_KEY` no configurada")
        return
    async with aiohttp.ClientSession() as session:
        async with session.post("https://google.serper.dev/search",
                                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                                json={"q": query, "num": 5, "gl": "es", "hl": "es"}) as resp:
            data = await resp.json()
    resultados = data.get("organic", [])
    if not resultados:
        await ctx.send(f"> Sin resultados para: **{query}**")
        return
    embed = discord.Embed(title=f"Google: {query[:50]}", color=AZUL_IPOD_NUM)
    for n, res in enumerate(resultados[:5]):
        embed.add_field(name=f"{n+1}. {res.get('title','')[:70]}",
                        value=f"> {res.get('snippet','')[:150]}\n[Leer más]({res.get('link','#')})",
                        inline=False)
    await ctx.send(embed=embed)

@info_group.command(name="imagenes", description="Busca imágenes en Google")
async def info_imagenes(ctx: commands.Context, *, query: str):
    if ctx.interaction:
        await ctx.defer()
    if not SERPER_API_KEY:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                "SERPER_API_KEY no configurada\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://google.serper.dev/images",
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": 5, "safe": "Off"}
        ) as resp:
            if resp.status != 200:
                embed = discord.Embed(
                    title="ERROR",
                    description=(
                        f"{sep()}\n\n"
                        f"Error en la API: {resp.status}\n\n"
                        f"{sep()}"
                    ),
                    color=AZUL_IPOD_NUM
                )
                await ctx.send(embed=embed)
                return
            data = await resp.json()
    imagenes = data.get("images", [])
    if not imagenes:
        embed = discord.Embed(
            title="SIN RESULTADOS",
            description=(
                f"{sep()}\n\n"
                f"No se encontraron imagenes para: {query}\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    embed = discord.Embed(
        title=f"IMAGENES: {query[:50]}",
        description=f"{sep()}",
        color=AZUL_IPOD_NUM
    )
    embed.set_image(url=imagenes[0].get('imageUrl', ''))
    for n, img in enumerate(imagenes[:3]):
        embed.add_field(
            name=f"IMAGEN {n+1}",
            value=f"[Ver imagen]({img.get('imageUrl', '#')})",
            inline=True
        )
    embed.set_footer(text="Google Images - Misti")
    await ctx.send(embed=embed)

@info_group.command(name="lugares", description="Busca lugares en Google Maps")
async def info_lugares(ctx: commands.Context, *, lugar: str):
    if ctx.interaction:
        await ctx.defer()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://nominatim.openstreetmap.org/search",
                                   params={"q": lugar, "format": "json", "limit": "5", "addressdetails": "1"},
                                   headers={"User-Agent": "MistiBot/1.0"}) as resp:
                if resp.status != 200:
                    await ctx.send(f"> Error ({resp.status})")
                    return
                data = await resp.json()
        if not data:
            await ctx.send(f"> Sin resultados para: **{lugar}**")
            return
        embed = discord.Embed(title=f"Lugares: {lugar}", color=AZUL_IPOD_NUM)
        for sitio in data[:5]:
            lat, lon = sitio.get("lat", ""), sitio.get("lon", "")
            nombre_corto = sitio.get("display_name", "Sin nombre")[:60] + "..." if len(sitio.get("display_name", "")) > 60 else sitio.get("display_name", "Sin nombre")
            embed.add_field(name=nombre_corto,
                            value=f"> **Tipo:** {sitio.get('type', 'lugar').replace('_', ' ').capitalize()}\n> **Coords:** `{float(lat):.4f}, {float(lon):.4f}`\n> [Google Maps](https://www.google.com/maps?q={lat},{lon})",
                            inline=False)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name} | OpenStreetMap")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error: `{str(e)[:100]}`")

@info_group.command(name="noticias", description="Últimas noticias de actualidad")
async def info_noticias(ctx: commands.Context, *, query: str = None):
    if ctx.interaction:
        await ctx.defer()
    feeds = ([f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=es&gl=ES&ceid=ES:es",
              "https://feeds.bbci.co.uk/mundo/rss.xml"] if query
             else ["https://news.google.com/rss?hl=es&gl=ES&ceid=ES:es",
                   "https://feeds.bbci.co.uk/mundo/rss.xml",
                   "https://www.infobae.com/feeds/rss/"])
    noticias_lista = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MistiBot/1.0)"}
    try:
        async with aiohttp.ClientSession() as session:
            for feed_url in feeds:
                if len(noticias_lista) >= 5:
                    break
                try:
                    async with session.get(feed_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status != 200:
                            continue
                        contenido = await resp.text()
                    root = ET.fromstring(contenido)
                    canal = root.find("channel")
                    if canal is None:
                        continue
                    for item in canal.findall("item"):
                        if len(noticias_lista) >= 5:
                            break
                        titulo = re.sub(r"<[^>]+>", "", item.findtext("title", "Sin título").strip())
                        enlace = item.findtext("link", "#").strip()
                        fecha = item.findtext("pubDate", "")
                        fuente_tag = item.find("{http://purl.org/dc/elements/1.1/}creator")
                        fuente = fuente_tag.text if fuente_tag is not None else feed_url.split("/")[2]
                        fecha_texto = ""
                        if fecha:
                            try:
                                fecha_texto = parsedate_to_datetime(fecha).strftime("%d/%m/%Y %H:%M")
                            except:
                                fecha_texto = fecha[:16]
                        noticias_lista.append({"titulo": titulo, "enlace": enlace, "fuente": fuente, "fecha": fecha_texto})
                except:
                    continue
        if not noticias_lista:
            await ctx.send(f"> Sin noticias para: **{query or 'hoy'}**")
            return
        embed = discord.Embed(title=f"Noticias: {query or 'Últimas'}", color=AZUL_IPOD_NUM)
        for n in noticias_lista[:5]:
            titulo_corto = (n["titulo"][:60] + "...") if len(n["titulo"]) > 60 else n["titulo"]
            embed.add_field(name=titulo_corto,
                            value=f"> **{n['fuente']}** | {n['fecha']}\n> [Leer más]({n['enlace']})",
                            inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"Error noticias: {e}")
        await ctx.send("> Error al procesar las noticias.")

@info_group.command(name="steam", description="Busca información de un juego en Steam")
async def info_steam(ctx: commands.Context, *, juego: str):
    if ctx.interaction:
        await ctx.defer()
    async with aiohttp.ClientSession() as session:
        async with session.get("https://steamcommunity.com/api/ISteamApps/GetAppList/v2/") as resp:
            if resp.status != 200:
                embed = discord.Embed(
                    title="ERROR",
                    description=(
                        f"{sep()}\n\n"
                        "**Error conectando con Steam**\n\n"
                        f"{sep()}"
                    ),
                    color=AZUL_IPOD_NUM
                )
                await ctx.send(embed=embed)
                return
            apps = (await resp.json()).get('applist', {}).get('apps', [])
    resultados = [app for app in apps if juego.lower() in app['name'].lower()]
    if not resultados:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                f"**No se encontró el juego:** {juego}\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    app_id = resultados[0]['appid']
    nombre = resultados[0]['name']
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://store.steampowered.com/api/appdetails?appids={app_id}") as resp:
            data = await resp.json()
    detalles = data.get(str(app_id), {})
    if not detalles.get('success'):
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                f"**Sin detalles para:** {nombre}\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    info = detalles.get('data', {})
    descripcion = info.get('short_description', 'Sin descripción')
    precio = info.get('price_overview', {})
    precio_final = precio.get('final_formatted', 'Gratis') if precio else 'No disponible'
    plataformas = []
    if info.get('platforms', {}).get('windows'):
        plataformas.append("🪟 Windows")
    if info.get('platforms', {}).get('mac'):
        plataformas.append("🍎 Mac")
    if info.get('platforms', {}).get('linux'):
        plataformas.append("🐧 Linux")
    generos_texto = ", ".join([g['description'] for g in info.get('genres', [])][:3]) or "N/A"
    puntaje = info.get('metacritic', {}).get('score', 'N/A')
    url_imagen = info.get('header_image', '')
    embed = discord.Embed(
        title=f"{nombre}",
        description=(
            f"{sep()}\n\n"
            f"{descripcion[:200] + '...' if len(descripcion) > 200 else descripcion}\n\n"
            f"{sep()}"
        ),
        color=AZUL_IPOD_NUM,
        url=f"https://store.steampowered.com/app/{app_id}"
    )
    if url_imagen:
        embed.set_thumbnail(url=url_imagen)
    embed.add_field(
        name="INFORMACIÓN",
        value=(
            f"**> PRECIO:** {precio_final}\n"
            f"**> METACRITIC:** {f'{puntaje}/100' if puntaje != 'N/A' else puntaje}\n"
            f"**> GÉNEROS:** {generos_texto}\n"
            f"**> PLATAFORMAS:** {', '.join(plataformas) or 'N/A'}"
        ),
        inline=False
    )
    embed.add_field(
        name="",
        value=f"\n{sep()}",
        inline=False
    )
    embed.set_footer(text=f"ID: {app_id} • Steam Store • Misti")
    await ctx.send(embed=embed)

@info_group.command(name="nasa", description="Foto astronómica del día (NASA APOD)")
async def info_nasa(ctx: commands.Context):
    if ctx.interaction:
        await ctx.defer()
    años = list(range(1995, 2025))
    fecha_aleatoria = f"{random.choice(años)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    usar_actual = random.choice([True, False])
    fecha = fecha_actual if usar_actual else fecha_aleatoria
    tipo = "Imagen del Día" if usar_actual else "Imagen Aleatoria (Archivo NASA)"
    url = f"https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&date={fecha}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                embed = discord.Embed(
                    title="ERROR",
                    description=(
                        f"{sep()}\n\n"
                        "**No se pudo obtener la imagen de la NASA.**\n\n"
                        f"{sep()}"
                    ),
                    color=AZUL_IPOD_NUM
                )
                await ctx.send(embed=embed)
                return
            data = await resp.json()
    if 'error' in data:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                f"**{data.get('error', {}).get('message', 'Error desconocido')}**\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    titulo = data.get('title', 'Imagen del día')
    explicacion = data.get('explanation', 'Sin explicación')
    if len(explicacion) > 500:
        explicacion = explicacion[:500] + "..."
    imagen = data.get('url', '')
    fecha_nasa = data.get('date', fecha)
    copyright_nt = data.get('copyright', 'NASA')
    if imagen.endswith('.mp4') or 'youtube' in imagen or 'vimeo' in imagen:
        embed = discord.Embed(
            title=f"{titulo}",
            description=(
                f"{sep()}\n\n"
                f"**Video del día**\n\n"
                f"{explicacion}\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        embed.add_field(
            name="**VER VIDEO**",
            value=f"[Haz clic aquí para ver el video]({imagen})",
            inline=False
        )
    else:
        embed = discord.Embed(
            title=f"{titulo}",
            description=(
                f"{sep()}\n\n"
                f"{explicacion}\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM,
            url=imagen
        )
        embed.set_image(url=imagen)
    embed.add_field(
        name="INFORMACIÓN",
        value=(
            f"**> FECHA:** {fecha_nasa}\n"
            f"**> CRÉDITO:** {copyright_nt}\n"
            f"**> TIPO:** {tipo}"
        ),
        inline=False
    )
    embed.add_field(
        name="",
        value=f"\n{sep()}",
        inline=False
    )
    embed.set_footer(text=f"NASA APOD • Misti")
    await ctx.send(embed=embed)

@info_group.command(name="covid", description="🦠 Datos actualizados de COVID-19")
async def info_covid(ctx: commands.Context, *, pais: str = "mexico"):
    if ctx.interaction:
        await ctx.defer()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://disease.sh/v3/covid-19/countries/{urllib.parse.quote(pais)}") as resp:
            if resp.status != 200:
                embed = discord.Embed(
                    title="ERROR",
                    description=(
                        f"{sep()}\n\n"
                        f"**No se encontraron datos para:** {pais}\n\n"
                        f"{sep()}"
                    ),
                    color=AZUL_IPOD_NUM
                )
                await ctx.send(embed=embed)
                return
            data = await resp.json()
    nombre = data.get('country', pais.capitalize())
    casos = data.get('cases', 0)
    muertes = data.get('deaths', 0)
    casos_hoy = data.get('todayCases', 0)
    muertes_hoy = data.get('todayDeaths', 0)
    recuperados = data.get('recovered', 0)
    activos = data.get('active', 0)
    criticos = data.get('critical', 0)
    pruebas = data.get('tests', 0)
    bandera = data.get('countryInfo', {}).get('flag', '')
    tm = (muertes / casos * 100) if casos > 0 else 0
    tr = (recuperados / casos * 100) if casos > 0 else 0
    embed = discord.Embed(
        title=f"COVID-19: {nombre.upper()}",
        description=f"{sep()}",
        color=AZUL_IPOD_NUM
    )
    if bandera:
        embed.set_thumbnail(url=bandera)
    embed.add_field(
        name="DATOS GENERALES",
        value=(
            f"**CASOS TOTALES:** {casos:,}\n"
            f"**CASOS HOY:** +{casos_hoy:,}\n"
            f"**MUERTES:** {muertes:,}\n"
            f"**MUERTES HOY:** +{muertes_hoy:,}\n"
            f"**RECUPERADOS:** {recuperados:,}\n"
            f"**ACTIVOS:** {activos:,}\n"
            f"**CRÍTICOS:** {criticos:,}\n"
            f"**PRUEBAS:** {pruebas:,}\n\n"
            f"**TASA MORTALIDAD:** {tm:.2f}%\n"
            f"**TASA RECUPERACIÓN:** {tr:.2f}%"
        ),
        inline=False
    )
    embed.add_field(
        name="",
        value=f"\n{sep()}",
        inline=False
    )
    embed.set_footer(text="Datos actualizados • disease.sh API • Misti")
    await ctx.send(embed=embed)

@info_group.command(name="traducir", description="Traduce texto a cualquier idioma")
async def info_traducir(ctx: commands.Context, idioma: str, *, texto: str):
    if ctx.interaction:
        await ctx.defer()
    idiomas_nombres = {
        "es": "Español", "en": "Inglés", "fr": "Francés", "de": "Alemán", "it": "Italiano",
        "pt": "Portugués", "ja": "Japonés", "ko": "Coreano", "zh": "Chino", "ru": "Ruso",
        "ar": "Árabe", "hi": "Hindi", "nl": "Holandés", "pl": "Polaco", "tr": "Turco",
        "vi": "Vietnamita", "th": "Tailandés", "el": "Griego", "he": "Hebreo", "sv": "Sueco",
        "no": "Noruego", "da": "Danés", "fi": "Finlandés",
    }
    idioma = idioma.lower()
    if idioma not in idiomas_nombres:
        codigos = ", ".join(list(idiomas_nombres.keys())[:15])
        await ctx.send(f"> Idioma **{idioma}** no válido. Disponibles: {codigos}...")
        return
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&dj=1&q={urllib.parse.quote(texto)}&sl=auto&tl={idioma}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("> Error con el traductor.")
                    return
                data = await resp.json()
        traduccion = "".join(s.get('trans', '') for s in data.get('sentences', []) if 'trans' in s)
        if not traduccion:
            await ctx.send("> No se pudo traducir.")
            return
        idioma_origen_nombre = idiomas_nombres.get(data.get('src', ''), data.get('src', '').upper())
        idioma_destino_nombre = idiomas_nombres.get(idioma, idioma.upper())
        embed = discord.Embed(title="Traductor", color=AZUL_IPOD_NUM)
        embed.add_field(name=f"> Original ({idioma_origen_nombre})", value=f"```{texto[:500]}```", inline=False)
        embed.add_field(name=f"> Traducción ({idioma_destino_nombre})", value=f"```{traduccion[:500]}```", inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error al traducir: ```{str(e)[:100]}```")

@info_group.command(name="recetas", description="Busca recetas de cocina")
async def info_recetas(ctx: commands.Context, *, plato: str):
    if ctx.interaction:
        await ctx.defer()
    if not SERPER_API_KEY:
        await ctx.send("> `SERPER_API_KEY` no configurada")
        return
    async with aiohttp.ClientSession() as session:
        async with session.post("https://google.serper.dev/search",
                                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                                json={"q": f"{plato} receta", "num": 5}) as resp:
            data = await resp.json()
    resultados = data.get("organic", [])
    if not resultados:
        await ctx.send(f"> Sin recetas para: **{plato}**")
        return
    embed = discord.Embed(title=f"Recetas de: {plato}", color=AZUL_IPOD_NUM)
    for r in resultados[:5]:
        embed.add_field(name=f"> {r.get('title','')[:60]}",
                        value=f"{r.get('snippet','')[:120]}\n[Ver receta]({r.get('link','#')})",
                        inline=False)
    await ctx.send(embed=embed)

# =========================================================
# GRUPO 6: MÚSICA (/musica)
# =========================================================

@bot.hybrid_group(name="musica", description="Comandos de música", fallback="help")
async def musica_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="MÚSICA",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`spotify` - Muestra lo que escucha un usuario\n"
                       "`cancion` - Busca una canción en Last.fm\n"
                       "`artista` - Busca un artista en Last.fm\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@musica_group.command(name="spotify", description="Muestra la música que escucha un usuario")
async def musica_spotify(ctx: commands.Context, usuario: discord.Member = None):
    if ctx.interaction:
        await ctx.defer()
    usuario = ctx.guild.get_member((usuario or ctx.author).id)
    actividad = discord.utils.find(lambda a: isinstance(a, discord.Spotify), usuario.activities)
    if not actividad:
        await ctx.send(f"> **{usuario.name} no esta escuchando Spotify**")
        return
    await ctx.send(file=await generar_spotify_card(usuario, actividad))

@musica_group.command(name="cancion", description="Busca una canción exacta en Last.fm")
async def musica_cancion(ctx: commands.Context, artista: str, *, cancion: str):
    if ctx.interaction:
        await ctx.defer()
    if not LASTFM_API_KEY:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                "**LASTFM_API_KEY no configurada**\n\n"
                "El administrador debe agregar `LASTFM_API_KEY` en Render.\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    if len(artista.strip()) < 2 or len(cancion.strip()) < 2:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                "**Artista y canción deben tener al menos 2 caracteres.**\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    try:
        track = await buscar_cancion_exacta(artista, cancion)
        if not track:
            embed = discord.Embed(
                title="ERROR",
                description=(
                    f"{sep()}\n\n"
                    f"**No se encontró la canción:**\n"
                    f" {cancion}\n"
                    f" {artista}\n\n"
                    f"{sep()}"
                ),
                color=AZUL_IPOD_NUM
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(
            title=f" {track['nombre']}",
            description=(
                f"{sep()}\n\n"
                f"** {track['artista']}**\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM,
            url=track["url"] or None
        )
        if track["cover"]:
            embed.set_thumbnail(url=track["cover"])
        embed.add_field(
            name="INFORMACIÓN",
            value=(
                f"**> ÁLBUM:** {track['album']}\n"
                f"**> DURACIÓN:** {track['duracion']}\n"
                f"**> AÑO:** {track.get('año', 'N/A')}\n"
                f"**> OYENTES:** {track.get('oyentes', 'N/A')}"
            ),
            inline=False
        )
        embed.add_field(
            name="",
            value=f"\n{sep()}",
            inline=False
        )
        embed.set_footer(text=f"Last.fm • {artista} - {cancion} • Misti")
        embed.set_author(name="Misti Music")
        view = discord.ui.View()
        if track["url"]:
            view.add_item(discord.ui.Button(
                label="Escuchar en Last.fm",
                url=track["url"],
                style=discord.ButtonStyle.link
            ))
        await ctx.send(embed=embed, view=view)
    except Exception as e:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                f"**Error:** {str(e)[:100]}\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@musica_group.command(name="artista", description="Busca información de un artista en Last.fm")
async def musica_artista(ctx: commands.Context, *, artista: str):
    if ctx.interaction:
        await ctx.defer()
    if not LASTFM_API_KEY:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                "**LASTFM_API_KEY no configurada**\n\n"
                "El administrador debe agregar `LASTFM_API_KEY` en Render.\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    if len(artista.strip()) < 2:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                "**Mínimo 2 caracteres para la búsqueda.**\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
        return
    try:
        url = (f"http://ws.audioscrobbler.com/2.0/?method=artist.getInfo"
               f"&api_key={LASTFM_API_KEY}&artist={urllib.parse.quote(artista.strip())}&format=json")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    embed = discord.Embed(
                        title="ERROR",
                        description=(
                            f"{sep()}\n\n"
                            f"**Error Last.fm:** {resp.status}\n\n"
                            f"{sep()}"
                        ),
                        color=AZUL_IPOD_NUM
                    )
                    await ctx.send(embed=embed)
                    return
                data = await resp.json()
        if "error" in data:
            embed = discord.Embed(
                title="ERROR",
                description=(
                    f"{sep()}\n\n"
                    f"**Artista no encontrado:** {artista}\n\n"
                    f"{sep()}"
                ),
                color=AZUL_IPOD_NUM
            )
            await ctx.send(embed=embed)
            return
        info = data.get("artist")
        if not info:
            embed = discord.Embed(
                title="ERROR",
                description=(
                    f"{sep()}\n\n"
                    "**Sin información del artista.**\n\n"
                    f"{sep()}"
                ),
                color=AZUL_IPOD_NUM
            )
            await ctx.send(embed=embed)
            return
        nombre = info.get("name", artista)
        url_lastfm = info.get("url", "")
        stats = info.get("stats", {})
        try:
            oyentes = f"{int(stats.get('listeners', 0)):,}".replace(",", ".")
        except:
            oyentes = "N/A"
        try:
            reproducciones = f"{int(stats.get('playcount', 0)):,}".replace(",", ".")
        except:
            reproducciones = "N/A"
        bio_raw = info.get("bio", {}).get("summary", "")
        bio = re.sub(r'<a href="[^"]*">[^<]*</a>', '', bio_raw)
        bio = re.sub(r'<[^>]+>', '', bio).strip()
        bio = (bio[:500] + "...") if len(bio) > 500 else bio or "Sin biografía."
        tags_raw = info.get("tags", {}).get("tag", [])
        if isinstance(tags_raw, dict):
            tags_raw = [tags_raw]
        generos = ", ".join([t.get("name", "") for t in tags_raw[:5]]) or "Sin géneros"
        similares_raw = info.get("similar", {}).get("artist", [])
        if isinstance(similares_raw, dict):
            similares_raw = [similares_raw]
        similares = ", ".join([a.get("name", "") for a in similares_raw[:4]]) or "N/A"
        imagen_url = await obtener_foto_artista(nombre)
        embed = discord.Embed(
            title=f"{nombre}",
            description=(
                f"{sep()}\n\n"
                f"{bio}\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM,
            url=url_lastfm or None
        )
        if imagen_url:
            embed.set_thumbnail(url=imagen_url)
        embed.add_field(
            name="INFORMACIÓN",
            value=(
                f"**> OYENTES:** {oyentes}\n"
                f"**> REPRODUCCIONES:** {reproducciones}\n"
                f"**> GÉNEROS:** {generos}"
            ),
            inline=False
        )
        if similares != "N/A":
            embed.add_field(
                name="ARTISTAS SIMILARES",
                value=similares,
                inline=False
            )
        embed.add_field(
            name="",
            value=f"\n{sep()}",
            inline=False
        )
        embed.set_footer(text="Last.fm • Misti")
        embed.set_author(name="Misti Music")
        view = discord.ui.View()
        if url_lastfm:
            view.add_item(discord.ui.Button(
                label=" Ver en Last.fm",
                url=url_lastfm,
                style=discord.ButtonStyle.link
            ))
        await ctx.send(embed=embed, view=view)
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                "**Tiempo de espera agotado.**\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="ERROR",
            description=(
                f"{sep()}\n\n"
                f"**Error:** {str(e)[:100]}\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

# =========================================================
# GRUPO 7: IA (/ia)
# =========================================================

@bot.hybrid_group(name="ia", description="Comandos de inteligencia artificial", fallback="help")
async def ia_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="INTELIGENCIA ARTIFICIAL",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`ask` - Habla con Misti\n"
                       "`forget` - Borra tu historial\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

class RegenerarButton(discord.ui.View):
    def __init__(self, user_id: int, mensaje_original: str):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.mensaje_original = mensaje_original

    @discord.ui.button(label="Regenerar", style=discord.ButtonStyle.primary, emoji="🔄")
    async def regenerar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("> Solo quien hizo la pregunta puede regenerar.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            nombre_servidor = interaction.guild.name if interaction.guild else "DM"
            respuesta = await generar_respuesta_groq(interaction.user.id, self.mensaje_original, interaction.user.display_name, nombre_servidor)
            agregar_memoria(interaction.user.id, "assistant", respuesta)
            embed = discord.Embed(color=AZUL_IPOD_NUM)
            user_text = self.mensaje_original[:500] + "..." if len(self.mensaje_original) > 500 else self.mensaje_original
            embed.add_field(name=f"**{interaction.user.display_name}**", value=f"> {user_text}", inline=False)
            bot_text = respuesta[:500] + "..." if len(respuesta) > 500 else respuesta
            embed.add_field(name="**Misti**", value=f"> {bot_text}", inline=False)
            await interaction.edit_original_response(embed=embed, view=RegenerarButton(interaction.user.id, self.mensaje_original))
        except Exception as e:
            await interaction.edit_original_response(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> Error: `{str(e)[:100]}`"), view=None)

async def responder_ask(destino, autor, mensaje: str, es_reply: bool = False):
    nombre_servidor = autor.guild.name if hasattr(autor, 'guild') and autor.guild else "DM"
    if any(p in mensaje.lower() for p in PALABRAS_AUDIO):
        prompt_audio = mensaje
        for p in PALABRAS_AUDIO:
            prompt_audio = prompt_audio.lower().replace(p, "").strip()
        if not prompt_audio or len(prompt_audio) < 3:
            prompt_audio = "Hola, soy Misti, tu asistente."
        audio_data, formato, error = await generar_audio_pollinations(prompt_audio)
        if audio_data:
            archivo_audio = discord.File(io.BytesIO(audio_data), filename=f"misti_audio.{formato}")
            embed = discord.Embed(
                title="Audio generado",
                description=f"> **Texto:** {prompt_audio[:200]}",
                color=AZUL_IPOD_NUM
            )
            embed.set_footer(text=f"Voz: nova • Misti")
            if es_reply:
                await destino.reply(embed=embed, file=archivo_audio, mention_author=False)
            else:
                await destino.send(embed=embed, file=archivo_audio)
        else:
            embed = discord.Embed(color=AZUL_IPOD_NUM, description=f"> No pude generar el audio: {error}")
            if es_reply:
                await destino.reply(embed=embed, mention_author=False)
            else:
                await destino.send(embed=embed)
        return
    if any(p in mensaje.lower() for p in PALABRAS_IMAGEN):
        img_data, prompt, seed = await generar_imagen_ia(mensaje)
        if img_data:
            archivo = discord.File(io.BytesIO(img_data), filename="misti_art.png")
            embed = discord.Embed(title="Imagen generada", description=f"> **Prompt:** {prompt[:200]}", color=AZUL_IPOD_NUM)
            embed.set_image(url="attachment://misti_art.png")
            if seed:
                embed.set_footer(text=f"Seed: {seed}")
            if es_reply:
                await destino.reply(embed=embed, file=archivo, mention_author=False)
            else:
                await destino.send(embed=embed, file=archivo)
        else:
            embed = discord.Embed(color=AZUL_IPOD_NUM, description="> No pude generar la imagen, intenta con otro prompt.")
            if es_reply:
                await destino.reply(embed=embed, mention_author=False)
            else:
                await destino.send(embed=embed)
        return
    agregar_memoria(autor.id, "user", mensaje)
    respuesta = await generar_respuesta_groq(autor.id, mensaje, autor.display_name, nombre_servidor)
    agregar_memoria(autor.id, "assistant", respuesta)
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    user_text = mensaje[:500] + "..." if len(mensaje) > 500 else mensaje
    embed.add_field(name=f"**{autor.display_name}**", value=f"> {user_text}", inline=False)
    bot_text = respuesta[:500] + "..." if len(respuesta) > 500 else respuesta
    embed.add_field(name="**Misti**", value=f"> {bot_text}", inline=False)
    view = RegenerarButton(autor.id, mensaje)
    if es_reply:
        await destino.reply(embed=embed, view=view, mention_author=False)
    else:
        await destino.send(embed=embed, view=view)

@ia_group.command(name="ask", description="Habla con Misti")
async def ia_ask(ctx: commands.Context, *, texto: str):
    if ctx.interaction:
        await ctx.defer()
    nombre_servidor = ctx.guild.name if ctx.guild else "DM"
    if any(p in texto.lower() for p in PALABRAS_AUDIO):
        prompt_audio = texto
        for p in PALABRAS_AUDIO:
            prompt_audio = prompt_audio.lower().replace(p, "").strip()
        if not prompt_audio or len(prompt_audio) < 3:
            prompt_audio = "Hola, soy Misti, tu asistente."
        audio_data, formato, error = await generar_audio_pollinations(prompt_audio)
        if audio_data:
            archivo_audio = discord.File(io.BytesIO(audio_data), filename=f"misti_audio.{formato}")
            embed = discord.Embed(
                title="Audio generado",
                description=f"> **Texto:** {prompt_audio[:200]}",
                color=AZUL_IPOD_NUM
            )
            embed.set_footer(text=f"Voz: nova • Misti")
            await ctx.send(embed=embed, file=archivo_audio)
        else:
            embed = discord.Embed(color=AZUL_IPOD_NUM, description=f"> No pude generar el audio: {error}")
            await ctx.send(embed=embed)
        return
    if any(p in texto.lower() for p in PALABRAS_IMAGEN):
        img_data, prompt, seed = await generar_imagen_ia(texto)
        if img_data:
            archivo = discord.File(io.BytesIO(img_data), filename="misti_art.png")
            embed = discord.Embed(title="Imagen generada", description=f"> **Prompt:** {prompt[:200]}", color=AZUL_IPOD_NUM)
            embed.set_image(url="attachment://misti_art.png")
            if seed:
                embed.set_footer(text=f"Seed: {seed}")
            await ctx.send(embed=embed, file=archivo)
        else:
            embed = discord.Embed(color=AZUL_IPOD_NUM, description="> No pude generar la imagen, intenta con otro prompt.")
            await ctx.send(embed=embed)
        return
    agregar_memoria(ctx.author.id, "user", texto)
    respuesta = await generar_respuesta_groq(ctx.author.id, texto, ctx.author.display_name, nombre_servidor)
    agregar_memoria(ctx.author.id, "assistant", respuesta)
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    user_text = texto[:500] + "..." if len(texto) > 500 else texto
    embed.add_field(name=f"**{ctx.author.display_name}**", value=f"> {user_text}", inline=False)
    bot_text = respuesta[:500] + "..." if len(respuesta) > 500 else respuesta
    embed.add_field(name="**Misti**", value=f"> {bot_text}", inline=False)
    await ctx.send(embed=embed, view=RegenerarButton(ctx.author.id, texto))

@ia_group.command(name="forget", description="Borra tu historial de conversación con Misti")
async def ia_forget(ctx: commands.Context):
    limpiar_memoria(ctx.author.id)
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> Misti ya no recuerda nada de ti."))

# =========================================================
# GRUPO 8: EMBEDS (/embed)
# =========================================================

@bot.hybrid_group(name="embed", description="Comandos de embeds", fallback="help")
async def embed_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="EMBEDS",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`crear` - Crea un embed con variables\n"
                       "`config` - Configura un embed personalizado (ADMIN)\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@embed_group.command(name="crear", description="Crea un embed personalizado con variables")
async def embed_crear(
    ctx: commands.Context,
    titulo: str = None,
    descripcion: str = None,
    color: str = None,
    autor: str = None,
    autor_imagen: str = None,
    footer: str = None,
    footer_imagen: str = None,
    imagen: str = None,
    thumbnail: str = None,
    canal: discord.TextChannel = None
):
    if ctx.interaction:
        await ctx.defer()
    if not canal:
        canal = ctx.channel
    def reemplazar(texto):
        if not texto:
            return texto
        return texto.replace("{user_name}", ctx.author.display_name) \
            .replace("{user_avatar}", str(ctx.author.display_avatar.url)) \
            .replace("{user_id}", str(ctx.author.id)) \
            .replace("{server_name}", ctx.guild.name) \
            .replace("{server_avatar}", str(ctx.guild.icon.url) if ctx.guild.icon else "") \
            .replace("{server_id}", str(ctx.guild.id)) \
            .replace("{user_count}", str(ctx.guild.member_count)) \
            .replace("{date}", datetime.now().strftime("%d/%m/%Y %H:%M"))
    embed = discord.Embed(
        title=reemplazar(titulo) or None,
        description=reemplazar(descripcion) or None,
        color=int(color.lstrip("#"), 16) if color else AZUL_IPOD_NUM
    )
    if autor:
        embed.set_author(
            name=reemplazar(autor),
            icon_url=reemplazar(autor_imagen) or None
        )
    if footer:
        embed.set_footer(
            text=reemplazar(footer),
            icon_url=reemplazar(footer_imagen) or None
        )
    if imagen:
        embed.set_image(url=reemplazar(imagen))
    if thumbnail:
        embed.set_thumbnail(url=reemplazar(thumbnail))
    await canal.send(embed=embed)

class EmbedBuilder(discord.ui.View):
    def __init__(self, user_id: int, guild_id: int, guild: discord.Guild, config_id: str = None):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = str(guild_id)
        self.guild = guild
        if self.guild_id not in configs:
            configs[self.guild_id] = {}
            guardar_configs()
        if config_id is None:
            import time
            self.config_id = f"embed_{int(time.time())}_{user_id}"
        else:
            self.config_id = config_id
        if self.config_id not in configs[self.guild_id]:
            configs[self.guild_id][self.config_id] = {
                "id": self.config_id,
                "titulo": "",
                "descripcion": "",
                "color": 0x2B55B5,
                "autor": "",
                "autor_imagen": "",
                "footer": "",
                "footer_imagen": "",
                "imagen": "",
                "thumbnail": "",
                "tipo": "normal",
                "canal": None,
                "ignorar_bots": False,
                "permanente": False
            }
            guardar_configs()
        self.config = configs[self.guild_id][self.config_id]
        self.embed_actual = None
        self.member = guild.get_member(user_id)

    def crear_embed_vista_previa(self) -> discord.Embed:
        member = self.member
        titulo = reemplazar_variables(self.config.get("titulo", "Titulo del embed"), member, self.guild)
        desc = reemplazar_variables(self.config.get("descripcion", "Descripcion del embed"), member, self.guild)
        embed = discord.Embed(
            title=titulo,
            description=desc,
            color=self.config.get("color", 0x2B55B5)
        )
        if self.config.get("autor"):
            autor_nombre = reemplazar_variables(self.config["autor"], member, self.guild)
            autor_img = reemplazar_variables(self.config.get("autor_imagen", ""), member, self.guild)
            if autor_img and not autor_img.startswith(("http://", "https://")):
                autor_img = None
            embed.set_author(name=autor_nombre, icon_url=autor_img or None)
        if self.config.get("footer"):
            footer_texto = reemplazar_variables(self.config["footer"], member, self.guild)
            footer_img = reemplazar_variables(self.config.get("footer_imagen", ""), member, self.guild)
            if footer_img and not footer_img.startswith(("http://", "https://")):
                footer_img = None
            embed.set_footer(text=footer_texto, icon_url=footer_img or None)
        else:
            footer_texto = reemplazar_variables("Vista previa - Configuracion en vivo", member, self.guild)
            embed.set_footer(text=footer_texto)
        if self.config.get("imagen"):
            img_url = reemplazar_variables(self.config["imagen"], member, self.guild)
            if img_url and img_url.startswith(("http://", "https://")):
                embed.set_image(url=img_url)
        if self.config.get("thumbnail"):
            thumb_url = reemplazar_variables(self.config["thumbnail"], member, self.guild)
            if thumb_url and thumb_url.startswith(("http://", "https://")):
                embed.set_thumbnail(url=thumb_url)
        return embed

    def get_embed_final(self, member: discord.Member = None) -> discord.Embed:
        if member is None:
            member = self.member
        titulo = reemplazar_variables(self.config.get("titulo", ""), member, self.guild)
        desc = reemplazar_variables(self.config.get("descripcion", ""), member, self.guild)
        embed = discord.Embed(
            title=titulo or "Titulo del embed",
            description=desc or "Descripcion del embed",
            color=self.config.get("color", 0x2B55B5)
        )
        if self.config.get("autor"):
            autor_nombre = reemplazar_variables(self.config["autor"], member, self.guild)
            autor_img = reemplazar_variables(self.config.get("autor_imagen", ""), member, self.guild)
            if autor_img and not autor_img.startswith(("http://", "https://")):
                autor_img = None
            embed.set_author(name=autor_nombre, icon_url=autor_img or None)
        if self.config.get("footer"):
            footer_texto = reemplazar_variables(self.config["footer"], member, self.guild)
            footer_img = reemplazar_variables(self.config.get("footer_imagen", ""), member, self.guild)
            if footer_img and not footer_img.startswith(("http://", "https://")):
                footer_img = None
            embed.set_footer(text=footer_texto, icon_url=footer_img or None)
        if self.config.get("imagen"):
            img_url = reemplazar_variables(self.config["imagen"], member, self.guild)
            if img_url and img_url.startswith(("http://", "https://")):
                embed.set_image(url=img_url)
        if self.config.get("thumbnail"):
            thumb_url = reemplazar_variables(self.config["thumbnail"], member, self.guild)
            if thumb_url and thumb_url.startswith(("http://", "https://")):
                embed.set_thumbnail(url=thumb_url)
        return embed

    def crear_embed_info(self) -> discord.Embed:
        config = self.config
        embed = discord.Embed(
            title="Informacion de la Configuracion",
            color=self.config.get("color", 0x2B55B5)
        )
        embed.add_field(name="Titulo", value=config.get("titulo") or "No configurado", inline=False)
        embed.add_field(name="Descripcion", value=config.get("descripcion") or "No configurado", inline=False)
        embed.add_field(name="Color", value=f"#{format(config.get('color', 0x2B55B5), '06X')}", inline=True)
        embed.add_field(name="Tipo", value=config.get("tipo", "normal").capitalize(), inline=True)
        embed.add_field(name="Canal", value=f"<#{config.get('canal')}>" if config.get('canal') else "No configurado", inline=True)
        autor_texto = f"Nombre: {config.get('autor') or 'No configurado'}"
        if config.get('autor_imagen'):
            autor_texto += f"\nImagen: [URL]({config['autor_imagen']})"
        embed.add_field(name="Autor", value=autor_texto, inline=False)
        footer_texto = f"Texto: {config.get('footer') or 'No configurado'}"
        if config.get('footer_imagen'):
            footer_texto += f"\nImagen: [URL]({config['footer_imagen']})"
        embed.add_field(name="Footer", value=footer_texto, inline=False)
        embed.add_field(name="Imagen", value=config.get('imagen') or "No configurado", inline=False)
        embed.add_field(name="Thumbnail", value=config.get('thumbnail') or "No configurado", inline=False)
        if config.get("tipo") in ["bienvenida", "despedida"]:
            embed.add_field(name="Ignorar bots", value="Si" if config.get('ignorar_bots') else "No", inline=True)
            embed.add_field(name="Permanente", value="Si" if config.get('permanente') else "No", inline=True)
        embed.set_footer(text=f"ID: {self.config_id}")
        return embed

    async def actualizar_vista(self, interaction: discord.Interaction):
        embed = self.crear_embed_vista_previa()
        self.embed_actual = embed
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Editar (Titulo/Desc/Color)", style=discord.ButtonStyle.primary, row=0)
    async def editar_principal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("> Solo quien ejecuto el comando puede editar.", ephemeral=True)
            return
        modal = EditarPrincipalModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Editar Autor", style=discord.ButtonStyle.primary, row=0)
    async def editar_autor(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("> Solo quien ejecuto el comando puede editar.", ephemeral=True)
            return
        modal = EditarAutorModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Editar Footer", style=discord.ButtonStyle.primary, row=0)
    async def editar_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("> Solo quien ejecuto el comando puede editar.", ephemeral=True)
            return
        modal = EditarFooterModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Editar Imagen", style=discord.ButtonStyle.primary, row=1)
    async def editar_imagen(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("> Solo quien ejecuto el comando puede editar.", ephemeral=True)
            return
        modal = EditarImagenModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Configuracion", style=discord.ButtonStyle.primary, row=1)
    async def configuracion(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("> Solo quien ejecuto el comando puede configurar.", ephemeral=True)
            return
        modal = ConfiguracionModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Info", style=discord.ButtonStyle.secondary, row=1)
    async def info(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("> Solo quien ejecuto el comando puede ver la informacion.", ephemeral=True)
            return
        embed_info = self.crear_embed_info()
        await interaction.response.send_message(embed=embed_info, ephemeral=True)

    @discord.ui.button(label="Guardar/Activar", style=discord.ButtonStyle.success, row=2)
    async def guardar_activar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("> Solo quien ejecuto el comando puede guardar.", ephemeral=True)
            return
        tipo = self.config.get("tipo", "normal")
        canal_id = self.config.get("canal")
        if not canal_id:
            await interaction.response.send_message("> No se ha configurado un canal. Usa el boton Configuracion.", ephemeral=True)
            return
        canal = interaction.guild.get_channel(canal_id)
        if not canal:
            await interaction.response.send_message("> El canal configurado no existe.", ephemeral=True)
            return
        if tipo == "normal":
            embed = self.get_embed_final(self.member)
            await canal.send(embed=embed)
            await interaction.response.send_message(f"> Embed enviado al canal {canal.mention}", ephemeral=True)
        elif tipo == "bienvenida":
            guardar_configs()
            await interaction.response.send_message("> Configuracion de bienvenida guardada.", ephemeral=True)
        elif tipo == "despedida":
            guardar_configs()
            await interaction.response.send_message("> Configuracion de despedida guardada.", ephemeral=True)

class EditarPrincipalModal(discord.ui.Modal, title="Editar Titulo, Descripcion y Color"):
    def __init__(self, view: EmbedBuilder):
        super().__init__(timeout=120)
        self.view = view
        self.titulo = discord.ui.TextInput(
            label="Titulo",
            placeholder="Titulo del embed. Usa variables: {user_name}, {server_name}, {date}",
            default=self.view.config.get("titulo", ""),
            required=False,
            max_length=256
        )
        self.add_item(self.titulo)
        self.descripcion = discord.ui.TextInput(
            label="Descripcion",
            placeholder="Descripcion del embed. Usa variables: {user_name}, {server_name}, {date}",
            default=self.view.config.get("descripcion", ""),
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=4000
        )
        self.add_item(self.descripcion)
        self.color = discord.ui.TextInput(
            label="Color (codigo HEX)",
            placeholder="Ejemplo: 2B55B5 o #2B55B5",
            default=format(self.view.config.get("color", 0x2B55B5), '06X'),
            required=False,
            max_length=7
        )
        self.add_item(self.color)

    async def on_submit(self, interaction: discord.Interaction):
        config = self.view.config
        if self.titulo.value is not None:
            config["titulo"] = self.titulo.value
        if self.descripcion.value is not None:
            config["descripcion"] = self.descripcion.value
        if self.color.value:
            try:
                color_limpio = self.color.value.lstrip('#')
                if len(color_limpio) == 6:
                    config["color"] = int(color_limpio, 16)
                else:
                    await interaction.response.send_message("> Color invalido. Usa formato HEX (ej: 2B55B5)", ephemeral=True)
                    return
            except:
                await interaction.response.send_message("> Color invalido. Usa formato HEX (ej: 2B55B5)", ephemeral=True)
                return
        configs[self.view.guild_id][self.view.config_id] = config
        guardar_configs()
        await self.view.actualizar_vista(interaction)

class EditarAutorModal(discord.ui.Modal, title="Editar Autor"):
    def __init__(self, view: EmbedBuilder):
        super().__init__(timeout=120)
        self.view = view
        self.autor = discord.ui.TextInput(
            label="Nombre del autor",
            placeholder="Nombre que aparecera en el autor. Usa variables: {user_name}, {server_name}",
            default=self.view.config.get("autor", ""),
            required=False,
            max_length=256
        )
        self.add_item(self.autor)
        self.autor_imagen = discord.ui.TextInput(
            label="Imagen del autor (URL)",
            placeholder="URL de la imagen. Usa variables: {user_avatar}, {server_avatar}",
            default=self.view.config.get("autor_imagen", ""),
            required=False,
            max_length=500
        )
        self.add_item(self.autor_imagen)

    async def on_submit(self, interaction: discord.Interaction):
        config = self.view.config
        if self.autor.value is not None:
            config["autor"] = self.autor.value
        elif self.autor.value == "":
            config["autor"] = ""
        if self.autor_imagen.value is not None:
            config["autor_imagen"] = self.autor_imagen.value
        elif self.autor_imagen.value == "":
            config["autor_imagen"] = ""
        configs[self.view.guild_id][self.view.config_id] = config
        guardar_configs()
        await self.view.actualizar_vista(interaction)

class EditarFooterModal(discord.ui.Modal, title="Editar Footer"):
    def __init__(self, view: EmbedBuilder):
        super().__init__(timeout=120)
        self.view = view
        self.footer = discord.ui.TextInput(
            label="Texto del footer",
            placeholder="Texto que aparecera en el footer. Usa variables: {user_name}, {server_name}, {date}",
            default=self.view.config.get("footer", ""),
            required=False,
            max_length=2048
        )
        self.add_item(self.footer)
        self.footer_imagen = discord.ui.TextInput(
            label="Imagen del footer (URL)",
            placeholder="URL de la imagen. Usa variables: {user_avatar}, {server_avatar}",
            default=self.view.config.get("footer_imagen", ""),
            required=False,
            max_length=500
        )
        self.add_item(self.footer_imagen)

    async def on_submit(self, interaction: discord.Interaction):
        config = self.view.config
        if self.footer.value is not None:
            config["footer"] = self.footer.value
        elif self.footer.value == "":
            config["footer"] = ""
        if self.footer_imagen.value is not None:
            config["footer_imagen"] = self.footer_imagen.value
        elif self.footer_imagen.value == "":
            config["footer_imagen"] = ""
        configs[self.view.guild_id][self.view.config_id] = config
        guardar_configs()
        await self.view.actualizar_vista(interaction)

class EditarImagenModal(discord.ui.Modal, title="Editar Imagen y Thumbnail"):
    def __init__(self, view: EmbedBuilder):
        super().__init__(timeout=120)
        self.view = view
        self.imagen = discord.ui.TextInput(
            label="Imagen principal (URL)",
            placeholder="URL de la imagen. Usa variables: {user_avatar}, {server_avatar}",
            default=self.view.config.get("imagen", ""),
            required=False,
            max_length=500
        )
        self.add_item(self.imagen)
        self.thumbnail = discord.ui.TextInput(
            label="Thumbnail (URL)",
            placeholder="URL del thumbnail. Usa variables: {user_avatar}, {server_avatar}",
            default=self.view.config.get("thumbnail", ""),
            required=False,
            max_length=500
        )
        self.add_item(self.thumbnail)

    async def on_submit(self, interaction: discord.Interaction):
        config = self.view.config
        if self.imagen.value is not None:
            config["imagen"] = self.imagen.value
        elif self.imagen.value == "":
            config["imagen"] = ""
        if self.thumbnail.value is not None:
            config["thumbnail"] = self.thumbnail.value
        elif self.thumbnail.value == "":
            config["thumbnail"] = ""
        configs[self.view.guild_id][self.view.config_id] = config
        guardar_configs()
        await self.view.actualizar_vista(interaction)

class ConfiguracionModal(discord.ui.Modal, title="Configuracion del Embed"):
    def __init__(self, view: EmbedBuilder):
        super().__init__(timeout=300)
        self.view = view
        self.tipo = discord.ui.TextInput(
            label="Tipo de embed",
            placeholder="normal / bienvenida / despedida",
            default=self.view.config.get("tipo", "normal"),
            required=False,
            max_length=20
        )
        self.add_item(self.tipo)
        self.ignorar_bots = discord.ui.TextInput(
            label="Ignorar bots (solo bienvenida/despedida)",
            placeholder="si / no",
            default="si" if self.view.config.get("ignorar_bots", False) else "no",
            required=False,
            max_length=2
        )
        self.add_item(self.ignorar_bots)
        self.permanente = discord.ui.TextInput(
            label="Hacer permanente (reenvio automatico)",
            placeholder="si / no",
            default="si" if self.view.config.get("permanente", False) else "no",
            required=False,
            max_length=2
        )
        self.add_item(self.permanente)
        self.canal = discord.ui.TextInput(
            label="ID del canal",
            placeholder="Ejemplo: 123456789012345678",
            default=str(self.view.config.get("canal", "")) if self.view.config.get("canal") else "",
            required=False,
            max_length=20
        )
        self.add_item(self.canal)

    async def on_submit(self, interaction: discord.Interaction):
        config = self.view.config
        errores = []
        if self.tipo.value:
            tipo = self.tipo.value.lower().strip()
            if tipo in ["normal", "bienvenida", "despedida"]:
                config["tipo"] = tipo
            else:
                errores.append("Tipo invalido. Usa: normal, bienvenida o despedida")
        if self.ignorar_bots.value:
            valor = self.ignorar_bots.value.lower().strip()
            if valor in ["si", "sí"]:
                config["ignorar_bots"] = True
            elif valor in ["no", "n"]:
                config["ignorar_bots"] = False
            else:
                errores.append("Ignorar bots debe ser 'si' o 'no'")
        if self.permanente.value:
            valor = self.permanente.value.lower().strip()
            if valor in ["si", "sí"]:
                config["permanente"] = True
            elif valor in ["no", "n"]:
                config["permanente"] = False
            else:
                errores.append("Permanente debe ser 'si' o 'no'")
        if self.canal.value:
            try:
                canal_id = int(self.canal.value.strip())
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    config["canal"] = canal_id
                else:
                    errores.append("El canal no existe en este servidor")
            except ValueError:
                errores.append("El ID del canal debe ser un numero")
        else:
            config["canal"] = None
        if errores:
            await interaction.response.send_message(
                f"> Errores en la configuracion:\n" + "\n".join(f"• {e}" for e in errores),
                ephemeral=True
            )
            return
        configs[self.view.guild_id][self.view.config_id] = config
        guardar_configs()
        await self.view.actualizar_vista(interaction)

@embed_group.command(name="config", description="(ADMIN) Configura un embed personalizado")
@commands.has_permissions(administrator=True)
async def embed_config(ctx: commands.Context):
    view = EmbedBuilder(ctx.author.id, ctx.guild.id, ctx.guild)
    embed_vista = view.crear_embed_vista_previa()
    await ctx.send(
        content="# Panel de configuracion de embeds\n> Usa los botones para personalizar tu embed. La vista previa se actualiza en vivo.",
        embed=embed_vista,
        view=view,
        ephemeral=True
    )

# =========================================================
# GRUPO 9: ANÓNIMOS (/anon)
# =========================================================

@bot.hybrid_group(name="anon", description="Comandos de mensajes anónimos", fallback="help")
async def anon_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="ANÓNIMOS",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`enviar` - Envía un mensaje anónimo\n\n"
                       "**Administración:**\n"
                       "`set` - Configura el canal de anónimos\n"
                       "`panel` - Reenvía el panel\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

class ModalAnonimo(discord.ui.Modal, title="Mensaje Anónimo"):
    contenido = discord.ui.TextInput(label="Tu mensaje", style=discord.TextStyle.long,
                                     placeholder="Escribe aquí tu mensaje anónimo...", min_length=1, max_length=1000)

    def __init__(self, canal_destino: discord.TextChannel):
        super().__init__()
        self.canal_destino = canal_destino

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid not in anon_data:
            anon_data[gid] = []
        if gid not in anon_count:
            anon_count[gid] = 0
        anon_count[gid] += 1
        numero = anon_count[gid]
        anon_data[gid].append({"numero": numero, "user_id": interaction.user.id,
                               "username": str(interaction.user), "contenido": str(self.contenido)})
        guardar_anonimos()
        embed = discord.Embed(description=str(self.contenido), color=AZUL_IPOD_NUM)
        embed.set_footer(text=f"#{numero:03d}")
        await self.canal_destino.send(embed=embed)
        await interaction.response.send_message("> Tu mensaje anónimo fue enviado.", ephemeral=True)

class VistaPanelAnonimo(discord.ui.View):
    def __init__(self, canal_destino: discord.TextChannel):
        super().__init__(timeout=None)
        self.canal_destino = canal_destino

    @discord.ui.button(label="Enviar mensaje anónimo", style=discord.ButtonStyle.primary,
                       custom_id="btn_panel_anonimo", emoji="📨")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        gid = str(interaction.guild.id)
        if gid not in anon_config:
            await interaction.response.send_message("> El canal de anónimos no está configurado.", ephemeral=True)
            return
        canal = interaction.guild.get_channel(anon_config[gid]["canal_id"])
        if not canal:
            await interaction.response.send_message("> El canal configurado no existe.", ephemeral=True)
            return
        await interaction.response.send_modal(ModalAnonimo(canal))

@anon_group.command(name="set", description="(ADMIN) Configura el canal de mensajes anónimos")
@commands.has_permissions(administrator=True)
async def anon_set(ctx: commands.Context, canal: discord.TextChannel):
    if ctx.interaction:
        await ctx.defer(ephemeral=True)
    gid = str(ctx.guild.id)
    anon_config[gid] = {"canal_id": canal.id}
    anon_count[gid] = 0
    anon_data[gid] = []
    guardar_anonimos()
    guardar_config()
    embed_panel = discord.Embed(title="Mensajes Anónimos",
                                description="Estos son los mensajes anónimos.\n\n> Usa el botón de abajo para enviar tu mensaje anónimo.",
                                color=AZUL_IPOD_NUM)
    await canal.send(embed=embed_panel, view=VistaPanelAnonimo(canal))
    await ctx.send(f"> Panel configurado en {canal.mention}.", ephemeral=True)

@anon_group.command(name="panel", description="(ADMIN) Reenvía el panel de mensajes anónimos")
@commands.has_permissions(administrator=True)
async def anon_panel(ctx: commands.Context):
    if ctx.interaction:
        await ctx.defer(ephemeral=True)
    gid = str(ctx.guild.id)
    if gid not in anon_config:
        await ctx.send("> Primero configura con `/anon set`.")
        return
    canal = ctx.guild.get_channel(anon_config[gid]["canal_id"])
    if not canal:
        await ctx.send("> Canal no encontrado.")
        return
    total = anon_count.get(gid, 0)
    embed_panel = discord.Embed(title="Mensajes Anónimos",
                                description="Estos son los mensajes anónimos.\n\n> Usa el botón de abajo para enviar tu mensaje anónimo.",
                                color=AZUL_IPOD_NUM)
    embed_panel.set_footer(text=f"Mensajes enviados hasta ahora: {total}")
    await canal.send(embed=embed_panel, view=VistaPanelAnonimo(canal))
    await ctx.send(f"> Panel reenviado en {canal.mention}.", ephemeral=True)

@anon_group.command(name="enviar", description="Envía un mensaje anónimo")
async def anon_enviar(ctx: commands.Context):
    gid = str(ctx.guild.id)
    if gid not in anon_config:
        await ctx.send("> Los mensajes anónimos no están configurados en este servidor.")
        return
    canal = ctx.guild.get_channel(anon_config[gid]["canal_id"])
    if not canal:
        await ctx.send("> El canal configurado no existe.")
        return
    if ctx.interaction:
        await ctx.interaction.response.send_modal(ModalAnonimo(canal))
    else:
        await ctx.send("> Este comando solo funciona como slash command `/anon enviar`.")

# =========================================================
# GRUPO 10: JUEGOS (/juego)
# =========================================================

@bot.hybrid_group(name="juego", description="Comandos de juegos", fallback="help")
async def juego_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="JUEGOS",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`ship` - Compatibilidad entre dos usuarios\n"
                       "`logro` - Genera una tarjeta de logro\n"
                       "`ipod` - Genera un reproductor iPod\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

@juego_group.command(name="ship", description="Compatibilidad entre dos usuarios")
async def juego_ship(ctx: commands.Context, usuario1: discord.Member, usuario2: discord.Member):
    if ctx.interaction:
        await ctx.defer()
    seed = (usuario1.id + usuario2.id) % 101
    random.seed(seed)
    pct = random.randint(0, 100)
    random.seed()
    await ctx.send(file=await generar_ship(usuario1, usuario2, pct))

@juego_group.command(name="logro", description="Genera una tarjeta de logro para un usuario")
async def juego_logro(ctx: commands.Context, usuario: discord.Member, titulo: str, *, descripcion: str = "Ha completado un gran desafío"):
    if ctx.interaction:
        await ctx.defer()
    await ctx.send(file=await generar_logro(usuario, titulo, descripcion))

@juego_group.command(name="ipod", description="Genera un reproductor iPod Classic")
async def juego_ipod(ctx: commands.Context, cancion: str, artista: str, duracion: str = "3:45", progreso: int = 45):
    if ctx.interaction:
        await ctx.defer()
    W, H = 340, 500
    PANTALLA_FONDO = (173, 232, 244)
    PANTALLA_TEXTO = (3, 4, 94)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(10, 10), (W-10, H-10)], radius=30, fill=AZUL_IPOD)
    draw.rounded_rectangle([(10, 10), (W-10, H-10)], radius=30, outline=BLANCO, width=2)
    draw.rounded_rectangle([(30, 30), (W-30, 210)], radius=10, fill=PANTALLA_FONDO)
    draw.rounded_rectangle([(30, 30), (W-30, 210)], radius=10, outline=(100, 200, 255), width=2)
    draw.text((45, 45), "Ahora Sonando", font=fuente(12, bold=True), fill=(10, 50, 120))
    draw.text((45, 75), (cancion[:20] + "..." if len(cancion) > 20 else cancion), font=fuente(18, bold=True), fill=PANTALLA_TEXTO)
    draw.text((45, 105), (artista[:24] + "..." if len(artista) > 24 else artista), font=fuente(13), fill=PANTALLA_TEXTO)
    draw.rounded_rectangle([(45, 140), (W-45, 148)], radius=4, fill=(210, 210, 210))
    progreso_px = 45 + int((W-90) * (max(0, min(progreso, 100)) / 100))
    draw.rounded_rectangle([(45, 140), (progreso_px, 148)], radius=4, fill=AZUL_IPOD)
    draw.text((45, 160), "0:00", font=fuente(11), fill=PANTALLA_TEXTO)
    draw.text((W-45, 160), duracion, font=fuente(11), fill=PANTALLA_TEXTO, anchor="ra")
    cx, cy, r_rueda = W//2, 350, 90
    draw.ellipse([(cx-r_rueda, cy-r_rueda), (cx+r_rueda, cy+r_rueda)], fill=(240, 240, 240))
    draw.ellipse([(cx-r_rueda, cy-r_rueda), (cx+r_rueda, cy+r_rueda)], outline=(200, 200, 200), width=3)
    draw.ellipse([(cx-30, cy-30), (cx+30, cy+30)], fill=(210, 210, 210))
    draw.text((cx, cy-75), "MENU", font=fuente(12, bold=True), fill=(120, 120, 120), anchor="mm")
    draw.text((cx, cy+70), "▶||", font=fuente(12, bold=True), fill=(120, 120, 120), anchor="mm")
    draw.text((cx-65, cy), "|◀◀", font=fuente(11, bold=True), fill=(120, 120, 120), anchor="mm")
    draw.text((cx+65, cy), "▶▶|", font=fuente(11, bold=True), fill=(120, 120, 120), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    await ctx.send(file=discord.File(buf, filename="ipod.png"))

# =========================================================
# GRUPO 11: PERFILES (/perfil)
# =========================================================

@bot.hybrid_group(name="perfil", description="Comandos de perfiles", fallback="help")
async def perfil_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="PERFILES",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`ver` - Muestra un perfil\n"
                       "`config` - Configura tu perfil\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

class PerfilView(discord.ui.View):
    def __init__(self, viewer: discord.Member, target: discord.Member):
        super().__init__(timeout=120)
        self.viewer = viewer
        self.target = target
        self._rebuild()

    def _sigue(self) -> bool:
        return self.viewer.id in get_social(
            self.target.guild.id, self.target.id
        ).get("seguidores", [])

    def _rebuild(self):
        self.clear_items()
        sigue = self._sigue()
        btn_seg = discord.ui.Button(
            label="Dejar de seguir" if sigue else "Seguir",
            style=discord.ButtonStyle.secondary if sigue else discord.ButtonStyle.primary,
            custom_id="btn_seguir",
            row=0,
        )
        btn_seg.callback = self._cb_seguir
        self.add_item(btn_seg)
        btn_like = discord.ui.Button(
            label="❤️ Like",
            style=discord.ButtonStyle.primary,
            custom_id="btn_like",
            row=0,
        )
        btn_like.callback = self._cb_like
        self.add_item(btn_like)
        btn_don = discord.ui.Button(
            label="💰 Donar",
            style=discord.ButtonStyle.primary,
            custom_id="btn_donar",
            row=0,
        )
        btn_don.callback = self._cb_donar
        self.add_item(btn_don)
        btn_com = discord.ui.Button(
            label="💬 Comentar",
            style=discord.ButtonStyle.primary,
            custom_id="btn_comentar",
            row=0,
        )
        btn_com.callback = self._cb_comentar
        self.add_item(btn_com)
        soc = get_social(self.target.guild.id, self.target.id)
        coments = soc.get("comentarios", [])
        options = []
        if coments:
            for i, c in enumerate(reversed(coments[-20:])):
                preview = c["texto"][:50] + ("..." if len(c["texto"]) > 50 else "")
                options.append(discord.SelectOption(
                    label=f"@{c['autor_name'][:20]}",
                    value=str(i),
                    description=preview,
                ))
        else:
            options.append(discord.SelectOption(
                label="Sin comentarios aún",
                value="none",
                description="Sé el primero en comentar",
            ))
        sel = discord.ui.Select(
            placeholder="💬 Ver comentarios...",
            options=options,
            custom_id="sel_comentarios",
            row=1,
        )
        sel.callback = self._cb_ver_comentario
        self.add_item(sel)

    async def _cb_seguir(self, interaction: discord.Interaction):
        if interaction.user.id != self.viewer.id:
            await interaction.response.send_message(
                "> Solo el dueño de esta vista puede interactuar.", ephemeral=True)
            return
        if interaction.user.id == self.target.id:
            await interaction.response.send_message(
                "> No puedes seguirte a ti mismo.", ephemeral=True)
            return
        soc = get_social(self.target.guild.id, self.target.id)
        segs = soc.setdefault("seguidores", [])
        if self.viewer.id in segs:
            segs.remove(self.viewer.id)
        else:
            segs.append(self.viewer.id)
        guardar_social()
        self._rebuild()
        await interaction.response.defer()
        await self.refrescar(interaction)

    async def _cb_like(self, interaction: discord.Interaction):
        if interaction.user.id != self.viewer.id:
            await interaction.response.send_message(
                "> Solo el dueño de esta vista puede interactuar.", ephemeral=True)
            return
        soc = get_social(self.target.guild.id, self.target.id)
        soc["likes"] = soc.get("likes", 0) + 1
        guardar_social()
        await interaction.response.defer()
        await self.refrescar(interaction)

    async def _cb_donar(self, interaction: discord.Interaction):
        if interaction.user.id != self.viewer.id:
            await interaction.response.send_message(
                "> Solo el dueño de esta vista puede interactuar.", ephemeral=True)
            return
        if interaction.user.id == self.target.id:
            await interaction.response.send_message(
                "> No puedes donarte a ti mismo.", ephemeral=True)
            return
        modal = ModalDonacion(self.viewer, self.target, self)
        await interaction.response.send_modal(modal)

    async def _cb_comentar(self, interaction: discord.Interaction):
        if interaction.user.id != self.viewer.id:
            await interaction.response.send_message(
                "> Solo el dueño de esta vista puede interactuar.", ephemeral=True)
            return
        modal = ModalComentario(self.viewer, self.target, self)
        await interaction.response.send_modal(modal)

    async def _cb_ver_comentario(self, interaction: discord.Interaction):
        if interaction.user.id != self.viewer.id:
            await interaction.response.send_message(
                "> Solo el dueño de esta vista puede interactuar.", ephemeral=True)
            return
        val = interaction.data["values"][0]
        if val == "none":
            await interaction.response.send_message(
                "> Aún no hay comentarios.", ephemeral=True)
            return
        soc = get_social(self.target.guild.id, self.target.id)
        coments = list(reversed(soc.get("comentarios", [])[-20:]))
        idx = int(val)
        if idx >= len(coments):
            await interaction.response.send_message(
                "> Comentario no encontrado.", ephemeral=True)
            return
        c = coments[idx]
        color_int = int(
            get_perfil(self.target.guild.id, self.target.id)
            .get("color_base", "c8a028"), 16
        )
        embed = discord.Embed(description=f"> {c['texto']}", color=color_int)
        embed.set_author(name=f"@{c['autor_name']}  ·  {c['fecha']}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def refrescar(self, interaction: discord.Interaction):
        perfil = get_perfil(self.target.guild.id, self.target.id)
        social = get_social(self.target.guild.id, self.target.id)
        self._rebuild()
        archivo = await generar_tarjeta_perfil(self.target, perfil, social)
        await interaction.edit_original_response(attachments=[archivo], view=self)

class ModalDonacion(discord.ui.Modal, title="Donar monedas"):
    cantidad = discord.ui.TextInput(
        label="Cantidad a donar",
        placeholder="Ej: 500",
        required=True,
        max_length=10,
    )

    def __init__(self, donante: discord.Member, receptor: discord.Member, view_ref):
        super().__init__()
        self.donante = donante
        self.receptor = receptor
        self.vref = view_ref

    async def on_submit(self, interaction: discord.Interaction):
        try:
            cant = int(str(self.cantidad).strip())
            if cant <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "> Ingresa una cantidad válida mayor a 0.", ephemeral=True)
            return
        eco_d = get_user_eco(interaction.guild.id, self.donante.id)
        if eco_d["coins"] < cant:
            await interaction.response.send_message(
                f"> No tienes suficientes monedas. Tienes **${eco_d['coins']:,}**.",
                ephemeral=True)
            return
        eco_r = get_user_eco(interaction.guild.id, self.receptor.id)
        eco_d["coins"] -= cant
        eco_r["coins"] += cant
        guardar_economia()
        soc = get_social(interaction.guild.id, self.receptor.id)
        soc["donaciones"] = soc.get("donaciones", 0) + 1
        guardar_social()
        await interaction.response.defer()
        await self.vref.refrescar(interaction)

class ModalComentario(discord.ui.Modal, title="Dejar un comentario"):
    mensaje = discord.ui.TextInput(
        label="Tu comentario",
        style=discord.TextStyle.long,
        placeholder="Escribe aquí...",
        required=True,
        min_length=1,
        max_length=200,
    )

    def __init__(self, autor: discord.Member, receptor: discord.Member, view_ref):
        super().__init__()
        self.autor = autor
        self.receptor = receptor
        self.vref = view_ref

    async def on_submit(self, interaction: discord.Interaction):
        soc = get_social(interaction.guild.id, self.receptor.id)
        soc.setdefault("comentarios", []).append({
            "autor_id": self.autor.id,
            "autor_name": self.autor.display_name,
            "texto": str(self.mensaje),
            "fecha": time.strftime("%d/%m/%Y"),
        })
        soc["comentarios"] = soc["comentarios"][-50:]
        guardar_social()
        await interaction.response.defer()
        await self.vref.refrescar(interaction)

class PerfilConfigView(discord.ui.View):
    def __init__(self, usuario: discord.Member):
        super().__init__(timeout=300)
        self.usuario = usuario
        self.tmp = copy.deepcopy(get_perfil(usuario.guild.id, usuario.id))

    async def refrescar(self, interaction: discord.Interaction):
        social = get_social(self.usuario.guild.id, self.usuario.id)
        archivo = await generar_tarjeta_perfil(
            self.usuario, self.tmp, social, es_preview=True)
        await interaction.edit_original_response(attachments=[archivo], view=self)

    @discord.ui.button(label="✏️ Editar (Nickname / Foto)", style=discord.ButtonStyle.primary, row=0)
    async def btn_editar(self, interaction: discord.Interaction, btn):
        if interaction.user.id != self.usuario.id:
            await interaction.response.send_message("> Solo el dueño puede editar.", ephemeral=True)
            return
        modal = ModalEditarPerfil(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🎨 Decoración", style=discord.ButtonStyle.primary, row=0)
    async def btn_decoracion(self, interaction: discord.Interaction, btn):
        if interaction.user.id != self.usuario.id:
            await interaction.response.send_message("> Solo el dueño puede editar.", ephemeral=True)
            return
        modal = ModalDecoracion(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔄 Restaurar", style=discord.ButtonStyle.primary, row=1)
    async def btn_restaurar(self, interaction: discord.Interaction, btn):
        if interaction.user.id != self.usuario.id:
            await interaction.response.send_message("> Solo el dueño puede restaurar.", ephemeral=True)
            return
        self.tmp = copy.deepcopy(_PERFIL_DEFAULT)
        await interaction.response.defer()
        await self.refrescar(interaction)

    @discord.ui.button(label="💾 Guardar", style=discord.ButtonStyle.primary, row=1)
    async def btn_guardar(self, interaction: discord.Interaction, btn):
        if interaction.user.id != self.usuario.id:
            await interaction.response.send_message("> Solo el dueño puede guardar.", ephemeral=True)
            return
        gid = str(self.usuario.guild.id)
        uid = str(self.usuario.id)
        perfiles_data.setdefault(gid, {})[uid] = copy.deepcopy(self.tmp)
        guardar_perfiles()
        await interaction.response.send_message("> ¡Perfil guardado correctamente!", ephemeral=True)

class ModalEditarPerfil(discord.ui.Modal, title="Editar perfil"):
    nickname = discord.ui.TextInput(
        label="Nickname",
        placeholder="Tu nombre visible (vacío = usar nombre de Discord)",
        required=False,
        max_length=32,
    )
    foto_url = discord.ui.TextInput(
        label="URL de foto de perfil",
        placeholder="https://... (vacío = usar avatar de Discord)",
        required=False,
        max_length=500,
    )

    def __init__(self, config_view):
        super().__init__()
        self.cv = config_view
        self.nickname.default = config_view.tmp.get("nickname", "")
        self.foto_url.default = config_view.tmp.get("foto_url", "")

    async def on_submit(self, interaction: discord.Interaction):
        self.cv.tmp["nickname"] = str(self.nickname).strip()
        self.cv.tmp["foto_url"] = str(self.foto_url).strip()
        await interaction.response.defer()
        await self.cv.refrescar(interaction)

class ModalDecoracion(discord.ui.Modal, title="Decoración del perfil"):
    color_base = discord.ui.TextInput(
        label="Color base (HEX) — bordes, letras, ornamentos",
        placeholder="Ej: c8a028   (dorado por defecto)",
        required=False,
        max_length=7,
    )
    estilo = discord.ui.TextInput(
        label="Estilo",
        placeholder="ninguno / basic / futurista / amor / san patricio / fuego / horror / sangre / dark",
        required=False,
        max_length=20,
    )

    def __init__(self, config_view):
        super().__init__()
        self.cv = config_view
        self.color_base.default = config_view.tmp.get("color_base", "c8a028")
        self.estilo.default = config_view.tmp.get("estilo", "ninguno")

    async def on_submit(self, interaction: discord.Interaction):
        errores = []
        cb_val = str(self.color_base).strip().lstrip("#")
        if cb_val:
            if len(cb_val) == 6:
                try:
                    int(cb_val, 16)
                    self.cv.tmp["color_base"] = cb_val
                except Exception:
                    errores.append("Color base inválido (usa 6 caracteres HEX, ej: c8a028).")
            else:
                errores.append("El color base debe tener exactamente 6 caracteres HEX.")
        est_val = str(self.estilo).strip().lower()
        if est_val:
            if est_val in ESTILOS_VALIDOS:
                self.cv.tmp["estilo"] = est_val
            else:
                errores.append(
                    f"Estilo inválido. Opciones: {', '.join(ESTILOS_VALIDOS)}"
                )
        if errores:
            await interaction.response.send_message(
                "> Errores:\n" + "\n".join(f"• {e}" for e in errores),
                ephemeral=True,
            )
            return
        await interaction.response.defer()
        await self.cv.refrescar(interaction)

@perfil_group.command(name="ver", description="Muestra el perfil de un usuario")
async def perfil_ver(ctx: commands.Context, usuario: discord.Member = None):
    if ctx.interaction:
        await ctx.defer()
    usuario = usuario or ctx.author
    view = PerfilView(ctx.author, usuario)
    perfil = get_perfil(ctx.guild.id, usuario.id)
    social = get_social(ctx.guild.id, usuario.id)
    archivo = await generar_tarjeta_perfil(usuario, perfil, social)
    await ctx.send(file=archivo, view=view)

@perfil_group.command(name="config", description="Configura tu perfil")
async def perfil_config(ctx: commands.Context):
    if ctx.interaction:
        await ctx.defer()
    view = PerfilConfigView(ctx.author)
    perfil = get_perfil(ctx.guild.id, ctx.author.id)
    social = get_social(ctx.guild.id, ctx.author.id)
    archivo = await generar_tarjeta_perfil(ctx.author, perfil, social, es_preview=True)
    await ctx.send("## Configuración de perfil\n> Usa los botones para personalizar tu perfil.",
                   file=archivo, view=view, ephemeral=True)

# =========================================================
# GRUPO 12: GIVEAWAY (/giveaway)
# =========================================================

@bot.hybrid_group(name="giveaway", description="Comandos de sorteos", fallback="help")
async def giveaway_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="GIVEAWAY",
            description=f"{sep()}\n\n"
                       "**Administración:**\n"
                       "`crear` - Crea un nuevo giveaway\n"
                       "`finish` - Finaliza un giveaway\n"
                       "`list` - Lista giveaways activos\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

class GiveawayView(discord.ui.View):
    def __init__(self, premio, segundos, duracion_texto, organizador_id, mensaje_id, canal_id, guild_id):
        super().__init__(timeout=segundos)
        self.premio = premio
        self.duracion_texto = duracion_texto
        self.organizador_id = organizador_id
        self.mensaje_id = mensaje_id
        self.canal_id = canal_id
        self.guild_id = guild_id
        self.participantes = []
        self.finalizado = False

    @discord.ui.button(label="PARTICIPAR", style=discord.ButtonStyle.primary)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            await interaction.response.send_message("Este giveaway ya finalizo.", ephemeral=True)
            return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message("Ya estas participando.", ephemeral=True)
            return
        self.participantes.append(interaction.user.id)
        await interaction.response.send_message(f"**{interaction.user.display_name}** participo!", ephemeral=True)
        try:
            canal = interaction.guild.get_channel(self.canal_id)
            if canal:
                msg = await canal.fetch_message(self.mensaje_id)
                old_e = msg.embeds[0]
                new_e = discord.Embed(title=old_e.title, description=old_e.description, color=old_e.color)
                for field in old_e.fields:
                    if field.name == "PARTICIPANTES":
                        new_e.add_field(name=field.name, value=f"```{len(self.participantes)} personas```", inline=field.inline)
                    else:
                        new_e.add_field(name=field.name, value=field.value, inline=field.inline)
                if old_e.footer:
                    new_e.set_footer(text=old_e.footer.text)
                await msg.edit(embed=new_e, view=self)
        except:
            pass

async def _finalizar_giveaway(mensaje_id, segundos, view, canal_id, guild_id):
    await asyncio.sleep(segundos)
    if mensaje_id not in giveaways_activos:
        return
    view.finalizado = True
    if view.participantes:
        ganador_id = random.choice(view.participantes)
        data = get_user_eco(guild_id, ganador_id)
        data["coins"] += view.premio
        embed_final = discord.Embed(
            title="GIVEAWAY FINALIZADO",
            description=(
                f"{sep()}\n\n"
                f"**GANADOR:** <@{ganador_id}>\n"
                f"**PREMIO:** ${view.premio:,}\n\n"
                f"{sep()}\n\n"
                f"**Felicitaciones!**"
            ),
            color=AZUL_IPOD_NUM
        )
        embed_final.set_footer(text="Sistema de Giveaway - Misti")
        for guild in bot.guilds:
            if guild.id == guild_id:
                canal = guild.get_channel(canal_id)
                if canal:
                    try:
                        msg = await canal.fetch_message(mensaje_id)
                        await msg.edit(embed=embed_final, view=None)
                        await canal.send(f"Felicidades <@{ganador_id}>! Ganaste **${view.premio:,}**!")
                    except:
                        pass
                break
    else:
        embed_final = discord.Embed(
            title="GIVEAWAY FINALIZADO",
            description=(
                f"{sep()}\n\n"
                f"**SIN PARTICIPANTES**\n\n"
                f"El giveaway ha terminado sin participantes.\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        embed_final.set_footer(text="Sistema de Giveaway - Misti")
        for guild in bot.guilds:
            if guild.id == guild_id:
                canal = guild.get_channel(canal_id)
                if canal:
                    try:
                        msg = await canal.fetch_message(mensaje_id)
                        await msg.edit(embed=embed_final, view=None)
                    except:
                        pass
                break
    giveaways_activos.pop(mensaje_id, None)

class GiveawayModal(discord.ui.Modal, title="CREAR GIVEAWAY"):
    def __init__(self, canal_id, guild_id):
        super().__init__(timeout=300)
        self.canal_id = canal_id
        self.guild_id = guild_id
        self.premio = discord.ui.TextInput(
            label="CANTIDAD DEL PREMIO",
            placeholder="Ej: 1000",
            min_length=1,
            max_length=10,
            required=True
        )
        self.add_item(self.premio)
        self.cantidad = discord.ui.TextInput(
            label="CANTIDAD DE TIEMPO",
            placeholder="Ej: 10",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.cantidad)
        self.unidad = discord.ui.TextInput(
            label="UNIDAD (m/h/d)",
            placeholder="m = minutos, h = horas, d = dias",
            min_length=1,
            max_length=1,
            required=True
        )
        self.add_item(self.unidad)
        self.motivo = discord.ui.TextInput(
            label="MOTIVO",
            placeholder="Ej: Por llegar a 100 miembros",
            required=False,
            max_length=100
        )
        self.add_item(self.motivo)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            premio = int(self.premio.value)
            cantidad = int(self.cantidad.value)
        except ValueError:
            await interaction.response.send_message("Premio y tiempo deben ser numeros.", ephemeral=True)
            return
        if premio <= 0 or cantidad <= 0:
            await interaction.response.send_message("Los valores deben ser mayores a 0.", ephemeral=True)
            return
        unidad = self.unidad.value.lower()
        if unidad == 'm':
            segundos = cantidad * 60
            duracion_texto = f"{cantidad} minuto{'s' if cantidad != 1 else ''}"
        elif unidad == 'h':
            segundos = cantidad * 3600
            duracion_texto = f"{cantidad} hora{'s' if cantidad != 1 else ''}"
        elif unidad == 'd':
            segundos = cantidad * 86400
            duracion_texto = f"{cantidad} dia{'s' if cantidad != 1 else ''}"
        else:
            await interaction.response.send_message("Unidad invalida. Usa m, h o d.", ephemeral=True)
            return
        if segundos < 60:
            await interaction.response.send_message("Minimo 1 minuto.", ephemeral=True)
            return
        if segundos > 604800:
            await interaction.response.send_message("Maximo 7 dias.", ephemeral=True)
            return
        motivo = self.motivo.value or "Sorteo especial"
        fecha_fin = datetime.now() + dt.timedelta(seconds=segundos)
        timestamp_fin = int(fecha_fin.timestamp())
        embed = discord.Embed(
            title="NUEVO GIVEAWAY",
            description=(
                f"{sep()}\n\n"
                f"**PREMIO:** ${premio:,} monedas\n"
                f"**MOTIVO:** {motivo}\n\n"
                f"{sep()}\n\n"
                f"**Haz clic en el boton para participar!**"
            ),
            color=AZUL_IPOD_NUM
        )
        embed.add_field(name="TERMINA", value=f"<t:{timestamp_fin}:R>", inline=True)
        embed.add_field(name="PARTICIPANTES", value=f"```0 personas```", inline=False)
        embed.add_field(name="ORGANIZADO POR", value=interaction.user.mention, inline=False)
        embed.set_footer(text="Sistema de Giveaway - Misti")
        await interaction.response.defer()
        view = GiveawayView(premio, segundos, duracion_texto, interaction.user.id, None, interaction.channel_id, interaction.guild_id)
        mensaje = await interaction.followup.send(embed=embed, view=view, wait=True)
        view.mensaje_id = mensaje.id
        giveaways_activos[mensaje.id] = view
        asyncio.create_task(_finalizar_giveaway(mensaje.id, segundos, view, interaction.channel_id, interaction.guild_id))

@giveaway_group.command(name="crear", description="(ADMIN) Crea un nuevo giveaway")
@commands.has_permissions(administrator=True)
async def giveaway_crear(ctx: commands.Context):
    embed = discord.Embed(
        title="CREAR GIVEAWAY",
        description=(
            f"{sep()}\n\n"
            "**INSTRUCCIONES:**\n"
            "Completa el formulario para crear un giveaway.\n\n"
            f"{sep()}\n\n"
            "**CAMPOS:**\n"
            "• Premio: Cantidad de monedas\n"
            "• Tiempo: Numero y unidad (m/h/d)\n"
            "• Motivo: Opcional\n\n"
            f"{sep()}"
        ),
        color=AZUL_IPOD_NUM
    )
    embed.set_footer(text="Sistema de Giveaway - Misti")
    view = discord.ui.View()
    async def btn_callback(interaction: discord.Interaction):
        modal = GiveawayModal(ctx.channel.id, ctx.guild.id)
        await interaction.response.send_modal(modal)
    view.add_item(discord.ui.Button(
        label="CREAR GIVEAWAY",
        style=discord.ButtonStyle.primary,
        custom_id="btn_crear",
    ))
    for child in view.children:
        child.callback = btn_callback
    await ctx.send(embed=embed, view=view)

@giveaway_group.command(name="finish", description="(ADMIN) Finaliza un giveaway anticipadamente")
@commands.has_permissions(administrator=True)
async def giveaway_finish(ctx: commands.Context, mensaje_id: str):
    try:
        msg_id = int(mensaje_id)
    except ValueError:
        embed = discord.Embed(
            title="ERROR",
            description="ID de mensaje invalido.",
            color=AZUL_IPOD_NUM
        )
        return await ctx.send(embed=embed)
    if msg_id not in giveaways_activos:
        embed = discord.Embed(
            title="ERROR",
            description="No se encontro un giveaway activo con ese ID.",
            color=AZUL_IPOD_NUM
        )
        return await ctx.send(embed=embed)
    view = giveaways_activos[msg_id]
    view.finalizado = True
    if view.participantes:
        ganador_id = random.choice(view.participantes)
        data = get_user_eco(ctx.guild.id, ganador_id)
        data["coins"] += view.premio
        embed_final = discord.Embed(
            title="GIVEAWAY FINALIZADO (ANTICIPADO)",
            description=(
                f"{sep()}\n\n"
                f"**GANADOR:** <@{ganador_id}>\n"
                f"**PREMIO:** ${view.premio:,}\n\n"
                f"{sep()}\n\n"
                f"**Felicitaciones!**"
            ),
            color=AZUL_IPOD_NUM
        )
        embed_final.set_footer(text="Sistema de Giveaway - Misti")
        try:
            canal = ctx.channel
            msg = await canal.fetch_message(msg_id)
            await msg.edit(embed=embed_final, view=None)
            await ctx.send(f"Giveaway finalizado! Ganador: <@{ganador_id}>")
        except:
            pass
    else:
        embed_final = discord.Embed(
            title="GIVEAWAY FINALIZADO (ANTICIPADO)",
            description=(
                f"{sep()}\n\n"
                f"**SIN PARTICIPANTES**\n\n"
                f"No hubo participantes en este giveaway.\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        embed_final.set_footer(text="Sistema de Giveaway - Misti")
        try:
            canal = ctx.channel
            msg = await canal.fetch_message(msg_id)
            await msg.edit(embed=embed_final, view=None)
        except:
            pass
    giveaways_activos.pop(msg_id, None)

@giveaway_group.command(name="list", description="(ADMIN) Lista los giveaways activos")
@commands.has_permissions(administrator=True)
async def giveaway_list(ctx: commands.Context):
    if not giveaways_activos:
        embed = discord.Embed(
            title="GIVEAWAYS ACTIVOS",
            description=(
                f"{sep()}\n\n"
                "**No hay giveaways activos**\n\n"
                f"{sep()}"
            ),
            color=AZUL_IPOD_NUM
        )
        embed.set_footer(text="Sistema de Giveaway - Misti")
        return await ctx.send(embed=embed)
    embed = discord.Embed(
        title="GIVEAWAYS ACTIVOS",
        description=f"{sep()}\n\n**Giveaways en curso:** {len(giveaways_activos)}",
        color=AZUL_IPOD_NUM
    )
    for msg_id, view in list(giveaways_activos.items())[:10]:
        embed.add_field(
            name=f"┌─ GIVEAWAY #{msg_id}",
            value=(
                f"│ **PREMIO:** ${view.premio:,}\n"
                f"│ **PARTICIPANTES:** {len(view.participantes)}\n"
                f"│ **DURACION:** {view.duracion_texto}\n"
                f"└─{''.join(['─' for _ in range(42)])}"
            ),
            inline=False
        )
    embed.set_footer(text="Sistema de Giveaway - Misti")
    await ctx.send(embed=embed)

# =========================================================
# GRUPO 13: BUZÓN (/buzon)
# =========================================================

@bot.hybrid_group(name="buzon", description="Comandos del buzón", fallback="help")
async def buzon_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="BUZÓN",
            description=f"{sep()}\n\n"
                       "**Subcomandos disponibles:**\n"
                       "`ver` - Ver tus correos\n\n"
                       "**Administración:**\n"
                       "`panel` - Crea el panel de buzón\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

class CorreoTextoModal(discord.ui.Modal, title="NUEVO CORREO DE TEXTO"):
    def __init__(self):
        super().__init__(timeout=300)
        self.titulo = discord.ui.TextInput(
            label="TÍTULO DEL CORREO",
            placeholder="Ej: ¡Hola!",
            required=False,
            max_length=100
        )
        self.add_item(self.titulo)
        self.descripcion = discord.ui.TextInput(
            label="CONTENIDO DEL CORREO",
            placeholder="Escribe tu mensaje...",
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=4000
        )
        self.add_item(self.descripcion)
        self.atte = discord.ui.TextInput(
            label="ATTE. (PIE DE PÁGINA)",
            placeholder="Ej: Tu amigo",
            required=False,
            max_length=100
        )
        self.add_item(self.atte)
        self.color = discord.ui.TextInput(
            label="COLOR (HEX)",
            placeholder="Ej: 2B55B5",
            required=False,
            max_length=7
        )
        self.add_item(self.color)
        self.destinatario = discord.ui.TextInput(
            label="ID DEL DESTINATARIO",
            placeholder="123456789012345678",
            required=True,
            max_length=20
        )
        self.add_item(self.destinatario)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            destinatario_id = int(self.destinatario.value)
            destinatario = interaction.guild.get_member(destinatario_id)
            if not destinatario:
                await interaction.response.send_message("> Usuario no encontrado en el servidor.", ephemeral=True)
                return
            if destinatario.bot:
                await interaction.response.send_message("> No puedes enviar correos a un bot.", ephemeral=True)
                return
            if destinatario.id == interaction.user.id:
                await interaction.response.send_message("> No puedes enviarte un correo a ti mismo.", ephemeral=True)
                return
            correo_id = f"correo_{int(datetime.now().timestamp())}_{interaction.user.id}"
            correo = {
                "id": correo_id,
                "tipo": "texto",
                "remitente": interaction.user.id,
                "destinatario": destinatario_id,
                "titulo": self.titulo.value or "Correo",
                "descripcion": self.descripcion.value or "Sin contenido",
                "atte": self.atte.value or "",
                "color": self.color.value or "2B55B5",
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "leido": False,
                "reclamado": False
            }
            guild_id = str(interaction.guild.id)
            if guild_id not in buzon_data:
                buzon_data[guild_id] = []
            buzon_data[guild_id].append(correo)
            guardar_buzon()
            embed = discord.Embed(
                title="CORREO ENVIADO",
                description=f"Correo enviado a {destinatario.mention}",
                color=AZUL_IPOD_NUM
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("> ID de usuario inválido.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"> Error: {str(e)[:100]}", ephemeral=True)

class CorreoDonacionModal(discord.ui.Modal, title="NUEVA DONACIÓN"):
    def __init__(self):
        super().__init__(timeout=300)
        self.descripcion = discord.ui.TextInput(
            label="MOTIVO DE LA DONACIÓN",
            placeholder="¿Para qué es la donación?",
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=4000
        )
        self.add_item(self.descripcion)
        self.cantidad = discord.ui.TextInput(
            label="CANTIDAD DE MONEDAS",
            placeholder="Ej: 1000",
            required=True,
            max_length=10
        )
        self.add_item(self.cantidad)
        self.atte = discord.ui.TextInput(
            label="ATTE. (PIE DE PÁGINA)",
            placeholder="Ej: Tu amigo",
            required=False,
            max_length=100
        )
        self.add_item(self.atte)
        self.color = discord.ui.TextInput(
            label="COLOR (HEX)",
            placeholder="Ej: 2B55B5",
            required=False,
            max_length=7
        )
        self.add_item(self.color)
        self.destinatario = discord.ui.TextInput(
            label="ID DEL DESTINATARIO",
            placeholder="123456789012345678",
            required=True,
            max_length=20
        )
        self.add_item(self.destinatario)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            destinatario_id = int(self.destinatario.value)
            destinatario = interaction.guild.get_member(destinatario_id)
            if not destinatario:
                await interaction.response.send_message("> Usuario no encontrado en el servidor.", ephemeral=True)
                return
            if destinatario.bot:
                await interaction.response.send_message("> No puedes enviar donaciones a un bot.", ephemeral=True)
                return
            if destinatario.id == interaction.user.id:
                await interaction.response.send_message("> No puedes donarte a ti mismo.", ephemeral=True)
                return
            cantidad = int(self.cantidad.value)
            if cantidad <= 0:
                await interaction.response.send_message("> La cantidad debe ser mayor a 0.", ephemeral=True)
                return
            data_remitente = get_user_eco(interaction.guild.id, interaction.user.id)
            if data_remitente["coins"] < cantidad:
                await interaction.response.send_message(f"> No tienes suficientes monedas. Tienes ${data_remitente['coins']}", ephemeral=True)
                return
            correo_id = f"correo_{int(datetime.now().timestamp())}_{interaction.user.id}"
            correo = {
                "id": correo_id,
                "tipo": "donacion",
                "remitente": interaction.user.id,
                "destinatario": destinatario_id,
                "titulo": "Donación",
                "descripcion": self.descripcion.value or "¡Te han donado monedas!",
                "cantidad": cantidad,
                "atte": self.atte.value or "",
                "color": self.color.value or "2B55B5",
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "leido": False,
                "reclamado": False
            }
            guild_id = str(interaction.guild.id)
            if guild_id not in buzon_data:
                buzon_data[guild_id] = []
            buzon_data[guild_id].append(correo)
            guardar_buzon()
            embed = discord.Embed(
                title="DONACIÓN ENVIADA",
                description=f"Donación de **${cantidad}** enviada a {destinatario.mention}",
                color=AZUL_IPOD_NUM
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("> La cantidad debe ser un número.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"> Error: {str(e)[:100]}", ephemeral=True)

class BuzonPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="TEXTO/ANUNCIO", style=discord.ButtonStyle.primary, row=0, custom_id="btn_texto")
    async def texto_anuncio(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CorreoTextoModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="DONACIÓN", style=discord.ButtonStyle.primary, row=0, custom_id="btn_donacion")
    async def donacion(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CorreoDonacionModal()
        await interaction.response.send_modal(modal)

@buzon_group.command(name="panel", description="(ADMIN) Crea el panel de buzón")
@commands.has_permissions(administrator=True)
async def buzon_panel(ctx: commands.Context):
    embed = discord.Embed(
        title="# PANEL DE BUZÓN",
        description=(
            "Elige qué tipo de correo quieres enviar:\n\n"
            f"{sep()}\n\n"
            "**TEXTO/ANUNCIO**\n"
            "Envía un mensaje a otro usuario.\n\n"
            "**DONACIÓN**\n"
            "Envía monedas a otro usuario.\n\n"
            f"{sep()}\n\n"
            "**INSTRUCCIONES:**\n"
            "1. Selecciona el tipo de correo\n"
            "2. Completa el formulario\n"
            "3. ¡Listo!"
        ),
        color=AZUL_IPOD_NUM
    )
    embed.set_footer(text="Sistema de Buzón • Misti")
    view = BuzonPanelView()
    await ctx.send(embed=embed, view=view)

class BuzonView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.pagina = 0
        self.correos = []
        self.total_paginas = 1
        self.guild_id = None

    def cargar_correos(self, guild_id: str):
        self.guild_id = guild_id
        self.correos = []
        if guild_id in buzon_data:
            for correo in buzon_data[guild_id]:
                if correo["destinatario"] == self.user_id:
                    remitente = None
                    for guild in bot.guilds:
                        if str(guild.id) == guild_id:
                            remitente = guild.get_member(correo["remitente"])
                            break
                    if remitente:
                        self.correos.append(correo)
        self.correos.reverse()
        self.total_paginas = (len(self.correos) + 4) // 5
        if self.total_paginas == 0:
            self.total_paginas = 1

    def _get_remitente_nombre(self, remitente_id: int) -> str:
        for guild in bot.guilds:
            member = guild.get_member(remitente_id)
            if member:
                return member.display_name
        return f"Usuario {remitente_id}"

    def get_embed(self, guild_id: str) -> discord.Embed:
        self.cargar_correos(guild_id)
        embed = discord.Embed(
            title="BUZÓN",
            description="Aquí puedes ver todos los correos que has recibido.",
            color=AZUL_IPOD_NUM
        )
        embed.add_field(name="", value=crear_separador(), inline=False)
        inicio = self.pagina * 4
        fin = min(inicio + 4, len(self.correos))
        correos_pagina = self.correos[inicio:fin]
        if not self.correos:
            embed.add_field(
                name="NO TIENES CORREOS",
                value="Cuando alguien te envíe un correo, aparecerá aquí.",
                inline=False
            )
        else:
            for i, correo in enumerate(correos_pagina, start=inicio + 1):
                estado = "NO LEÍDO" if not correo.get("leido", False) else "LEÍDO"
                tipo = "TEXTO" if correo.get("tipo") == "texto" else "DONACIÓN"
                remitente_id = correo.get('remitente', 0)
                nombre = self._get_remitente_nombre(remitente_id)
                fecha = correo.get('fecha', '')
                embed.add_field(
                    name=f"┌─   CORREO #{i}",
                    value=f"│ **TIPO:** {tipo}\n│ **DE:** {nombre}\n│ **ESTADO:** {estado}\n│ **FECHA:** {fecha}\n└─" + "─" * 42,
                    inline=False
                )
        embed.add_field(name="", value=crear_separador(), inline=False)
        nav_info = f"PÁGINA {self.pagina + 1} DE {self.total_paginas}"
        embed.add_field(
            name="NAVEGACIÓN",
            value=f"**{nav_info}**\n**TOTAL DE CORREOS:** {len(self.correos)}",
            inline=False
        )
        embed.add_field(name="", value=crear_separador(), inline=False)
        embed.add_field(
            name="SELECCIONA UN CORREO",
            value="Usa el menú desplegable para abrir un correo.\nUsa los botones de navegación para cambiar de página.",
            inline=False
        )
        embed.set_footer(text="Sistema de Buzón • Misti")
        return embed

    def get_menu_view(self, guild_id: str) -> discord.ui.View:
        self.cargar_correos(guild_id)
        view = discord.ui.View(timeout=None)
        options = []
        inicio = self.pagina * 4
        fin = min(inicio + 4, len(self.correos))
        if not self.correos:
            options.append(
                discord.SelectOption(
                    label="📭 No hay correos",
                    value="none",
                    description="No tienes correos para abrir"
                )
            )
        else:
            for i in range(inicio, fin):
                correo = self.correos[i]
                tipo = "💬" if correo.get("tipo") == "texto" else "💰"
                estado = "📨" if not correo.get("leido", False) else "📖"
                titulo = correo.get('titulo', 'Correo')[:20]
                nombre = self._get_remitente_nombre(correo['remitente'])
                options.append(
                    discord.SelectOption(
                        label=f"#{i+1} - {tipo} {titulo}",
                        description=f"{estado} De: {nombre[:20]}",
                        value=str(i),
                        emoji="📬"
                    )
                )
        select = discord.ui.Select(
            placeholder="📨 SELECCIONA UN CORREO",
            min_values=1,
            max_values=1,
            options=options
        )
        async def select_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("> Solo el dueño del buzón puede abrir correos.", ephemeral=True)
                return
            if select.values[0] == "none":
                await interaction.response.send_message("> No hay correos para abrir.", ephemeral=True)
                return
            try:
                index = int(select.values[0])
                correo = self.correos[index]
                await self.abrir_correo(interaction, correo)
            except Exception as e:
                await interaction.response.send_message(f"> Error: {str(e)[:100]}", ephemeral=True)
        select.callback = select_callback
        view.add_item(select)
        view.add_item(discord.ui.Button(
            label="ANTERIOR",
            style=discord.ButtonStyle.primary,
            custom_id="nav_anterior", emoji="◀️"
        ))
        view.add_item(discord.ui.Button(
            label="SIGUIENTE",
            style=discord.ButtonStyle.primary,
            custom_id="nav_siguiente", emoji="▶️"
        ))
        async def anterior_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("> Solo el dueño del buzón puede navegar.", ephemeral=True)
                return
            if self.pagina > 0:
                self.pagina -= 1
                nueva_vista = self.get_menu_view(guild_id)
                await interaction.response.edit_message(embed=self.get_embed(guild_id), view=nueva_vista)
            else:
                await interaction.response.send_message("> Ya estás en la primera página.", ephemeral=True)
        async def siguiente_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("> Solo el dueño del buzón puede navegar.", ephemeral=True)
                return
            if self.pagina < self.total_paginas - 1:
                self.pagina += 1
                nueva_vista = self.get_menu_view(guild_id)
                await interaction.response.edit_message(embed=self.get_embed(guild_id), view=nueva_vista)
            else:
                await interaction.response.send_message("> Ya estás en la última página.", ephemeral=True)
        for child in view.children:
            if child.custom_id == "nav_anterior":
                child.callback = anterior_callback
            elif child.custom_id == "nav_siguiente":
                child.callback = siguiente_callback
        return view

    async def abrir_correo(self, interaction: discord.Interaction, correo: dict):
        correo["leido"] = True
        guild_id = str(interaction.guild.id)
        if guild_id in buzon_data:
            for c in buzon_data[guild_id]:
                if c["id"] == correo["id"]:
                    c["leido"] = True
                    break
            guardar_buzon()
        color = int(correo.get('color', '2B55B5'), 16) if correo.get('color') else AZUL_IPOD_NUM
        embed = discord.Embed(
            title="CORREO",
            description=f"**{correo.get('titulo', 'Correo')}**",
            color=color
        )
        embed.add_field(name="", value=crear_separador(), inline=False)
        embed.add_field(
            name="CONTENIDO",
            value=correo.get('descripcion', 'Sin contenido'),
            inline=False
        )
        embed.add_field(name="", value=crear_separador(), inline=False)
        nombre_remitente = self._get_remitente_nombre(correo['remitente'])
        embed.add_field(
            name="INFORMACIÓN",
            value=f"**DE:** {nombre_remitente} (<@{correo['remitente']}>)\n"
                  f"**FECHA:** {correo.get('fecha', '')}\n"
                  f"**TIPO:** {'TEXTO' if correo.get('tipo') == 'texto' else '💰 DONACIÓN'}",
            inline=False
        )
        if correo.get('atte'):
            embed.set_footer(text=f"Atte. {correo['atte']}")
        if correo.get("tipo") == "donacion" and not correo.get("reclamado", False):
            view = ReclamarView(correo["id"], interaction.user.id)
            view.add_item(discord.ui.Button(
                label="VOLVER AL BUZÓN",
                style=discord.ButtonStyle.secondary,
                custom_id="volver_buzon"
            ))
        elif correo.get("tipo") == "donacion" and correo.get("reclamado", False):
            embed.add_field(name="ESTADO", value="YA RECLAMADO", inline=False)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="VOLVER AL BUZÓN",
                style=discord.ButtonStyle.secondary,
                custom_id="volver_buzon"
            ))
        else:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="VOLVER AL BUZÓN",
                style=discord.ButtonStyle.secondary,
                custom_id="volver_buzon"
            ))
        async def volver_callback(interaction2: discord.Interaction):
            if interaction2.user.id != self.user_id:
                await interaction2.response.send_message("> No puedes hacer esto.", ephemeral=True)
                return
            await self.mostrar_buzon(interaction2)
        for child in view.children:
            if child.custom_id == "volver_buzon":
                child.callback = volver_callback
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def mostrar_buzon(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        embed = self.get_embed(guild_id)
        view = self.get_menu_view(guild_id)
        await interaction.response.edit_message(embed=embed, view=view)

class ReclamarView(discord.ui.View):
    def __init__(self, correo_id: str, receptor_id: int):
        super().__init__(timeout=300)
        self.correo_id = correo_id
        self.receptor_id = receptor_id
        self.reclamado = False

    @discord.ui.button(label="RECLAMAR DONACIÓN", style=discord.ButtonStyle.success, emoji="💰")
    async def reclamar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.receptor_id:
            await interaction.response.send_message("> Este correo no es para ti.", ephemeral=True)
            return
        if self.reclamado:
            await interaction.response.send_message("> Esta donación ya fue reclamada.", ephemeral=True)
            return
        guild_id = str(interaction.guild.id)
        if guild_id not in buzon_data:
            await interaction.response.send_message("> Error: No se encontró el correo.", ephemeral=True)
            return
        correo_encontrado = None
        for c in buzon_data[guild_id]:
            if c["id"] == self.correo_id:
                correo_encontrado = c
                break
        if not correo_encontrado:
            await interaction.response.send_message("> Error: No se encontró el correo.", ephemeral=True)
            return
        if correo_encontrado.get("reclamado", False):
            await interaction.response.send_message("> Esta donación ya fue reclamada.", ephemeral=True)
            return
        cantidad = correo_encontrado.get("cantidad", 0)
        remitente_id = correo_encontrado["remitente"]
        receptor_id = interaction.user.id
        data_remitente = get_user_eco(interaction.guild.id, remitente_id)
        if data_remitente["coins"] < cantidad:
            await interaction.response.send_message(f"> El remitente no tiene suficientes monedas. Tiene ${data_remitente['coins']}", ephemeral=True)
            return
        data_receptor = get_user_eco(interaction.guild.id, receptor_id)
        data_remitente["coins"] -= cantidad
        data_receptor["coins"] += cantidad
        correo_encontrado["reclamado"] = True
        guardar_buzon()
        self.reclamado = True
        embed = discord.Embed(
            title="DONACIÓN RECLAMADA",
            description=f"¡Has reclamado **${cantidad}** monedas!\n\n**REMITE:** <@{remitente_id}>\n**NUEVO SALDO:** ${data_receptor['coins']}",
            color=discord.Color.green()
        )
        button.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

@buzon_group.command(name="ver", description="Ver los correos que has recibido")
async def buzon_ver(ctx: commands.Context):
    guild_id = str(ctx.guild.id)
    view = BuzonView(ctx.author.id)
    if guild_id not in buzon_data:
        embed = discord.Embed(
            title="📬 BUZÓN",
            description=f"{sep()}\n\n📭 **NO TIENES CORREOS**\n\nCuando alguien te envíe un correo,\naparecerá aquí.\n\n{sep()}",
            color=AZUL_IPOD_NUM
        )
        embed.set_footer(text="Sistema de Buzón • Misti")
        return await ctx.send(embed=embed, ephemeral=True)
    embed = view.get_embed(guild_id)
    vista = view.get_menu_view(guild_id)
    await ctx.send(embed=embed, view=vista, ephemeral=True)

# =========================================================
# GRUPO 14: PENSAMIENTO (/pensamiento)
# =========================================================

@bot.hybrid_group(name="pensamiento", description="Comandos de estado del bot", fallback="help")
async def pensamiento_group(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="PENSAMIENTO",
            description=f"{sep()}\n\n"
                       "**Administración:**\n"
                       "`set` - Cambia el estado del bot\n"
                       "`reset` - Elimina el estado del bot\n\n"
                       f"{sep()}",
            color=AZUL_IPOD_NUM
        )
        await ctx.send(embed=embed)

class PensamientoView(discord.ui.View):
    def __init__(self, autor_id: int, texto: str):
        super().__init__(timeout=60)
        self.autor_id = autor_id
        self.texto = texto

    @discord.ui.select(placeholder="Selecciona la duración", options=[
        discord.SelectOption(label="1 hora", value="1h", emoji="🕐"),
        discord.SelectOption(label="5 horas", value="5h", emoji="🕔"),
        discord.SelectOption(label="1 día", value="1d", emoji="📅"),
        discord.SelectOption(label="1 semana", value="1w", emoji="📆"),
        discord.SelectOption(label="1 mes", value="1m", emoji="🗓️"),
        discord.SelectOption(label="Para siempre", value="forever", emoji="♾️"),
    ])
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("> Solo quien ejecutó el comando puede seleccionar.", ephemeral=True)
            return
        dur = select.values[0]
        mapa = {"1h": (3600, "1 hora"), "5h": (18000, "5 horas"), "1d": (86400, "1 día"),
                "1w": (604800, "1 semana"), "1m": (2592000, "1 mes"), "forever": (None, "para siempre")}
        segundos, texto_dur = mapa[dur]
        texto_pens = self.texto[:120] + "..." if len(self.texto) > 120 else self.texto
        try:
            await interaction.client.change_presence(activity=discord.CustomActivity(name=texto_pens))
            embed = discord.Embed(title="Pensamiento actualizado",
                                  description=f"> **Pensamiento:** {texto_pens}\n> **Duración:** {texto_dur}",
                                  color=AZUL_IPOD_NUM)
            await interaction.response.edit_message(embed=embed, view=None)
            if segundos:
                await asyncio.sleep(segundos)
                actividad = interaction.client.activity
                if actividad and isinstance(actividad, discord.CustomActivity) and actividad.name == texto_pens:
                    await interaction.client.change_presence(activity=None)
                    try:
                        await interaction.channel.send(embed=discord.Embed(color=AZUL_IPOD_NUM,
                            description=f"> El pensamiento **{texto_pens}** ha expirado después de {texto_dur}"))
                    except:
                        pass
        except Exception as e:
            await interaction.response.edit_message(content=f"> Error: `{str(e)[:100]}`", view=None)

@pensamiento_group.command(name="set", description="(ADMIN) Cambia el estado del bot")
@commands.has_permissions(administrator=True)
async def pensamiento_set(ctx: commands.Context, *, texto: str):
    if len(texto) > 120:
        await ctx.send("> Máximo 120 caracteres.")
        return
    embed = discord.Embed(title="Establecer pensamiento",
                          description=f"> **Pensamiento:** {texto}\n\nSelecciona la duración:",
                          color=AZUL_IPOD_NUM)
    await ctx.send(embed=embed, view=PensamientoView(ctx.author.id, texto))

@pensamiento_group.command(name="reset", description="(ADMIN) Elimina el estado del bot")
@commands.has_permissions(administrator=True)
async def pensamiento_reset(ctx: commands.Context):
    await bot.change_presence(activity=None)
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> Pensamiento eliminado."))

# =========================================================
# EVENTOS
# =========================================================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Error sincronizando comandos: {e}")

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
        guardar_xp()
        canal_id = nivel_canal.get(message.guild.id)
        canal = message.guild.get_channel(canal_id) if canal_id else message.channel
        try:
            await canal.send(content=message.author.mention,
                             file=await generar_nivel(message.author, data["level"], data["xp"], xp_para_nivel(data["level"])))
        except Exception as e:
            print(f"Error nivel: {e}")

@bot.event
async def on_member_join(member):
    if member.bot:
        return
    # Verificar configuración de bienvenida del sistema de embeds
    try:
        guild_id = str(member.guild.id)
        if guild_id in configs:
            guild_configs = configs[guild_id]
            if isinstance(guild_configs, dict):
                for config_id, config in guild_configs.items():
                    if isinstance(config, dict) and config.get("tipo") == "bienvenida":
                        if config.get("ignorar_bots") and member.bot:
                            continue
                        canal_id = config.get("canal")
                        if canal_id:
                            canal = member.guild.get_channel(canal_id)
                            if canal:
                                titulo = reemplazar_variables(config.get("titulo", "Bienvenido al servidor"), member, member.guild)
                                desc = reemplazar_variables(config.get("descripcion", ""), member, member.guild)
                                embed = discord.Embed(
                                    title=titulo,
                                    description=desc or f"{member.mention} se unio al servidor",
                                    color=config.get("color", 0x2B55B5)
                                )
                                if config.get("autor"):
                                    autor_nombre = reemplazar_variables(config["autor"], member, member.guild)
                                    autor_img = reemplazar_variables(config.get("autor_imagen", ""), member, member.guild)
                                    if autor_img and not autor_img.startswith(("http://", "https://")):
                                        autor_img = None
                                    embed.set_author(name=autor_nombre, icon_url=autor_img or None)
                                if config.get("footer"):
                                    footer_texto = reemplazar_variables(config["footer"], member, member.guild)
                                    footer_img = reemplazar_variables(config.get("footer_imagen", ""), member, member.guild)
                                    if footer_img and not footer_img.startswith(("http://", "https://")):
                                        footer_img = None
                                    embed.set_footer(text=footer_texto, icon_url=footer_img or None)
                                if config.get("imagen"):
                                    img_url = reemplazar_variables(config["imagen"], member, member.guild)
                                    if img_url and img_url.startswith(("http://", "https://")):
                                        embed.set_image(url=img_url)
                                if config.get("thumbnail"):
                                    thumb_url = reemplazar_variables(config["thumbnail"], member, member.guild)
                                    if thumb_url and thumb_url.startswith(("http://", "https://")):
                                        embed.set_thumbnail(url=thumb_url)
                                await canal.send(embed=embed)
                                break
    except Exception as e:
        print(f"Error en bienvenida embeds: {e}")
    # Sistema de bienvenida antiguo
    cfg = welc_config.get(member.guild.id)
    if not cfg:
        return
    canal = member.guild.get_channel(cfg["canal"])
    if not canal:
        return
    embed = discord.Embed(
        title=parse_text(cfg.get("titulo") or f"Bienvenido {member.name}", member),
        description=parse_text(cfg.get("desc") or "", member),
        color=cfg.get("color", AZUL_IPOD_NUM))
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
    # Verificar configuración de despedida del sistema de embeds
    try:
        guild_id = str(member.guild.id)
        if guild_id in configs:
            guild_configs = configs[guild_id]
            if isinstance(guild_configs, dict):
                for config_id, config in guild_configs.items():
                    if isinstance(config, dict) and config.get("tipo") == "despedida":
                        if config.get("ignorar_bots") and member.bot:
                            continue
                        canal_id = config.get("canal")
                        if canal_id:
                            canal = member.guild.get_channel(canal_id)
                            if canal:
                                titulo = reemplazar_variables(config.get("titulo", "Hasta luego"), member, member.guild)
                                desc = reemplazar_variables(config.get("descripcion", ""), member, member.guild)
                                embed = discord.Embed(
                                    title=titulo,
                                    description=desc or f"{member.display_name} abandono el servidor",
                                    color=config.get("color", 0x2B55B5)
                                )
                                if config.get("autor"):
                                    autor_nombre = reemplazar_variables(config["autor"], member, member.guild)
                                    autor_img = reemplazar_variables(config.get("autor_imagen", ""), member, member.guild)
                                    if autor_img and not autor_img.startswith(("http://", "https://")):
                                        autor_img = None
                                    embed.set_author(name=autor_nombre, icon_url=autor_img or None)
                                if config.get("footer"):
                                    footer_texto = reemplazar_variables(config["footer"], member, member.guild)
                                    footer_img = reemplazar_variables(config.get("footer_imagen", ""), member, member.guild)
                                    if footer_img and not footer_img.startswith(("http://", "https://")):
                                        footer_img = None
                                    embed.set_footer(text=footer_texto, icon_url=footer_img or None)
                                if config.get("imagen"):
                                    img_url = reemplazar_variables(config["imagen"], member, member.guild)
                                    if img_url and img_url.startswith(("http://", "https://")):
                                        embed.set_image(url=img_url)
                                if config.get("thumbnail"):
                                    thumb_url = reemplazar_variables(config["thumbnail"], member, member.guild)
                                    if thumb_url and thumb_url.startswith(("http://", "https://")):
                                        embed.set_thumbnail(url=thumb_url)
                                await canal.send(embed=embed)
                                break
    except Exception as e:
        print(f"Error en despedida embeds: {e}")
    cfg = bye_config.get(member.guild.id)
    if not cfg:
        return
    canal = member.guild.get_channel(cfg["canal"])
    if not canal:
        return
    embed = discord.Embed(
        title=parse_text(cfg.get("titulo") or f"Adios {member.name}", member),
        description=parse_text(cfg.get("desc") or "", member),
        color=cfg.get("color", AZUL_IPOD_NUM))
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
async def on_message(message):
    if message.author.bot:
        return
    # AFK System
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
    # Claves system
    if message.guild:
        gid = str(message.guild.id)
        uid = str(message.author.id)
        if gid in claves_data and uid in claves_data[gid]:
            mensaje_lower = message.content.lower()
            for clave, respuesta in claves_data[gid][uid].items():
                if mensaje_lower == clave:
                    await message.reply(respuesta, mention_author=False)
                    break
    # Economy per message
    if message.guild:
        uid = str(message.author.id)
        if uid not in mensaje_count:
            mensaje_count[uid] = 0
        mensaje_count[uid] += 1
        if mensaje_count[uid] >= 5:
            mensaje_count[uid] = 0
            data = get_user_eco(str(message.guild.id), message.author.id)
            data["coins"] += random.randint(2, 4)
    # Auto-say
    if message.content == ">mt sayoff":
        autosay_users[message.author.id] = False
        await message.channel.send("Auto-say desactivado.", delete_after=5)
        try:
            await message.delete()
        except:
            pass
        return
    if autosay_users.get(message.author.id, False):
        if not message.content.startswith(">"):
            try:
                await message.delete()
            except discord.Forbidden:
                print("Error: El bot no tiene permiso para borrar mensajes.")
            await message.channel.send(message.content)
    # IA Responses
    if bot.user in message.mentions:
        mensaje_limpio = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if not mensaje_limpio:
            await message.reply("> Mencioname con un mensaje para que te responda.", mention_author=False)
        else:
            await responder_ask(message, message.author, mensaje_limpio, es_reply=True)
        await bot.process_commands(message)
        return
    if message.reference:
        try:
            replied = await message.channel.fetch_message(message.reference.message_id)
            if replied.author.id == bot.user.id:
                await responder_ask(message, message.author, message.content, es_reply=True)
                await bot.process_commands(message)
                return
        except:
            pass
    await bot.process_commands(message)

# =========================================================
# FLASK WEB
# =========================================================

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot activo"

def run_web():
    flask_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web, daemon=True).start()

# =========================================================
# RUN
# =========================================================

bot.run(TOKEN)
