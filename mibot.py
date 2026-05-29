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
from PIL import Image, ImageDraw, ImageFont
from groq import AsyncGroq
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading

# =========================================================
# ARCHIVOS DE DATOS
# =========================================================

DB_WARNINGS = "data_warnings.json"
DB_XP       = "data_xp.json"
DB_ECONOMIA = "data_economia.json"
DB_CLAVES   = "data_claves.json"
DB_ANONIMOS = "data_anonimos.json"
DB_CONFIG   = "data_config.json"
PLAYLIST_FILE = "playlists.json"

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

# =========================================================
# CARGA INICIAL
# =========================================================

warnings_data = _cargar(DB_WARNINGS)
xp_data       = _cargar(DB_XP)
economia_data = _cargar(DB_ECONOMIA)
claves_data   = _cargar(DB_CLAVES)

_anon_raw  = _cargar(DB_ANONIMOS, {"data": {}, "count": {}})
anon_data  = _anon_raw.get("data",  {})
anon_count = {k: int(v) for k, v in _anon_raw.get("count", {}).items()}

_cfg         = _cargar(DB_CONFIG, {"nivel_canal": {}, "welc": {}, "bye": {}, "anon_config": {}})
nivel_canal  = {int(k): v for k, v in _cfg.get("nivel_canal", {}).items()}
welc_config  = {int(k): v for k, v in _cfg.get("welc", {}).items()}
bye_config   = {int(k): v for k, v in _cfg.get("bye",  {}).items()}
anon_config  = _cfg.get("anon_config", {})

afk_data      = {}
mensaje_count = {}
xp_cooldown   = {}
cupones_data  = {}
giveaways_activos = {}
puntuaciones_trivia = {}
memoria_usuarios = {}

# =========================================================
# FUNCIONES DE GUARDADO
# =========================================================

def guardar_warnings():  _guardar(DB_WARNINGS, warnings_data)
def guardar_xp():        _guardar(DB_XP, xp_data)
def guardar_economia():  _guardar(DB_ECONOMIA, economia_data)
def guardar_claves():    _guardar(DB_CLAVES, claves_data)

def guardar_anonimos():
    _guardar(DB_ANONIMOS, {"data": anon_data, "count": anon_count})

def guardar_config():
    _guardar(DB_CONFIG, {
        "nivel_canal": {str(k): v for k, v in nivel_canal.items()},
        "welc":        {str(k): v for k, v in welc_config.items()},
        "bye":         {str(k): v for k, v in bye_config.items()},
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
# AUTOGUARDADO CADA 5 MINUTOS
# =========================================================

async def tarea_autoguardado():
    await bot.wait_until_ready()
    while not bot.is_closed():
        guardar_warnings(); guardar_xp(); guardar_economia()
        guardar_claves();   guardar_anonimos(); guardar_config()
        await asyncio.sleep(300)

# =========================================================
# CONFIGURACION
# =========================================================

groq_client   = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
TOKEN         = os.getenv("TOKEN")
RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

AZUL_OSCURO   = (35, 63, 98)
AZUL_IPOD     = (35, 63, 98)
AZUL_IPOD_NUM = 0x233f62
BLANCO        = (255, 255, 255)
FONDO_G       = (10, 10, 10)
GRIS_G        = (42, 42, 42)
TEXTO_G       = (255, 255, 255)
SUB_G         = (136, 136, 136)
OSCU_G        = (15, 15, 15)

_CALC_ALLOWED = re.compile(r'^[\d\s\+\-\*\/\(\)\.\%\*\*]+$')

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

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")

# =========================================================
# UTILIDADES DE IMAGEN
# =========================================================

async def descargar_imagen(url: str) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.read()
    return Image.open(io.BytesIO(data)).convert("RGBA")

def avatar_circular(img: Image.Image, size: int) -> Image.Image:
    img  = img.resize((size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    resultado = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    resultado.paste(img, (0, 0), mask)
    return resultado

def fuente(size: int, bold: bool = False):
    opciones = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"    if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"  if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in opciones:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

# =========================================================
# HELPERS DE DATOS
# =========================================================

def get_xp(guild_id, user_id):
    gid, uid = str(guild_id), str(user_id)
    if gid not in xp_data:      xp_data[gid] = {}
    if uid not in xp_data[gid]: xp_data[gid][uid] = {"xp": 0, "level": 1}
    return xp_data[gid][uid]

def xp_para_nivel(nivel): return nivel * 100

def get_user_eco(guild_id, user_id):
    gid, uid = str(guild_id), str(user_id)
    if gid not in economia_data:      economia_data[gid] = {}
    if uid not in economia_data[gid]: economia_data[gid][uid] = {"coins": 0, "last_daily": 0}
    return economia_data[gid][uid]

def get_user_claves(guild_id, user_id):
    gid, uid = str(guild_id), str(user_id)
    if gid not in claves_data:      claves_data[gid] = {}
    if uid not in claves_data[gid]: claves_data[gid][uid] = {}
    return claves_data[gid][uid]

def parse_text(texto, member):
    if not texto: return ""
    return texto.replace("{user_name}", member.name) \
                .replace("{user_mention}", member.mention) \
                .replace("{user_id}", str(member.id)) \
                .replace("{server_name}", member.guild.name) \
                .replace("{user_avatar}", str(member.display_avatar.url))

async def get_member_from_ctx(ctx, usuario=None):
    if usuario: return usuario
    if ctx.message.reference:
        try:
            replied = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member  = ctx.guild.get_member(replied.author.id)
            if member: return member
        except: pass
    return ctx.author

def get_memoria(user_id: int) -> list:
    if user_id not in memoria_usuarios: memoria_usuarios[user_id] = []
    return memoria_usuarios[user_id]

def agregar_memoria(user_id: int, role: str, content: str):
    memoria = get_memoria(user_id)
    memoria.append({"role": role, "content": content})
    if len(memoria) > 30: memoria.pop(0)

def limpiar_memoria(user_id: int):
    memoria_usuarios.pop(user_id, None)

# =========================================================
# GENERADORES DE IMAGEN
# =========================================================

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
    draw.text((128, 56), f"@{usuario.name}",   font=fuente(16),            fill=SUBTEXTO_USER)
    draw.rectangle([(24, 126), (W - 24, 128)], fill=(60, 63, 70))
    col1_x, col2_x, y = 24, 370, 148
    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, fill=CAMPO_FONDO)
        draw.text((x + 12, y + 8),  titulo, font=fuente(13),            fill=SUBTEXTO_USER)
        draw.text((x + 12, y + 30), valor,  font=fuente(17, bold=True), fill=TEXTO_USER)
    campo(col1_x, y, "USUARIO", f"@{usuario.display_name}")
    campo(col2_x, y, "ID",      str(usuario.id))
    y2 = y + 80
    campo(col1_x, y2, "CUENTA CREADA",   usuario.created_at.strftime("%d/%m/%Y"))
    campo(col2_x, y2, "ENTRO AL SERVER", usuario.joined_at.strftime("%d/%m/%Y") if usuario.joined_at else "?")
    draw.text((24, H - 22), f"Solicitado por {usuario.display_name}", font=fuente(12), fill=SUBTEXTO_USER)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="userinfo.png")

async def generar_serverinfo(guild: discord.Guild, solicitante: discord.Member) -> discord.File:
    W, H        = 700, 400
    CAMPO_FONDO = (20, 20, 20)
    CAMPO_BORDE = (50, 50, 60)
    img  = Image.new("RGBA", (W, H), FONDO_G)
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
    draw.text((nombre_x, 22), guild.name,        font=fuente(26, bold=True), fill=TEXTO_G)
    draw.text((nombre_x, 56), f"ID: {guild.id}", font=fuente(14),            fill=SUB_G)
    draw.rectangle([(24, 126), (W - 24, 127)], fill=AZUL_OSCURO)
    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, fill=CAMPO_FONDO)
        draw.rounded_rectangle([(x, y), (x + ancho, y + 64)], radius=8, outline=CAMPO_BORDE, width=1)
        draw.text((x + 12, y + 8),  titulo,     font=fuente(13),            fill=SUB_G)
        draw.text((x + 12, y + 30), str(valor),  font=fuente(17, bold=True), fill=TEXTO_G)
    y = 148
    campo(24,  y, "OWNER",  guild.owner.display_name if guild.owner else "?")
    campo(370, y, "CREADO", guild.created_at.strftime("%d/%m/%Y"))
    y2, a3 = y + 80, 204
    campo(24,       y2, "MIEMBROS", str(guild.member_count), ancho=a3)
    campo(24+224,   y2, "ROLES",    str(len(guild.roles)),   ancho=a3)
    campo(24+448,   y2, "EMOJIS",   str(len(guild.emojis)),  ancho=a3)
    y3 = y2 + 80
    campo(24,       y3, "TEXTO",  str(len(guild.text_channels)),  ancho=a3)
    campo(24+224,   y3, "VOZ",    str(len(guild.voice_channels)), ancho=a3)
    campo(24+448,   y3, "BOOSTS", f"{guild.premium_subscription_count} (nv {guild.premium_tier})", ancho=a3)
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
    progreso = min(xp / xp_needed, 1.0) if xp_needed > 0 else 0
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
    draw.text((34, 30), "Ranking",                      font=fuente(18, bold=True), fill=TEXTO_G)
    draw.text((34, 58), "Top usuarios con mas monedas", font=fuente(11),            fill=SUB_G)
    draw.rectangle([(34, 72), (646, 73)], fill=GRIS_G)
    for n, (uid, data) in enumerate(top):
        member = guild.get_member(int(uid))
        nombre = member.display_name if member else f"Usuario {uid}"
        nombre = nombre[:20] + "..." if len(nombre) > 20 else nombre
        y      = 82 + (n * 46)
        draw.rounded_rectangle([(34, y), (646, y + 36)], radius=8, fill=(26, 26, 26) if n == 0 else OSCU_G)
        draw.text((54,  y + 10), f"#{n+1}", font=fuente(14, bold=True), fill=AZUL_OSCURO if n == 0 else SUB_G)
        draw.text((90,  y + 10), nombre,    font=fuente(13, bold=n == 0), fill=TEXTO_G)
        draw.text((620, y + 10), f"$ {data['coins']:,}", font=fuente(13), fill=AZUL_OSCURO if n == 0 else SUB_G, anchor="ra")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ranking.png")

async def generar_ban(usuario: discord.Member, razon: str, moderador: discord.Member) -> discord.File:
    W, H = 680, 190
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
    draw.text((98, 72),  "z", font=fuente(17, bold=True), fill=BLANCO)
    draw.text((110, 58), "z", font=fuente(14, bold=True), fill=BLANCO)
    draw.text((120, 46), "z", font=fuente(11),            fill=BLANCO)
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
    draw.text((162, 122), (razon[:50] + "..." if len(razon) > 50 else razon), font=fuente(15, bold=True), fill=TEXTO_G)
    draw.text((162, 154), f"Total de warns: {total}", font=fuente(12), fill=AZUL_OSCURO)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="warn.png")

async def generar_warnings_img(usuario: discord.Member, warns: list) -> discord.File:
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
        draw.text((54, y + 8),  f"#{n+1}", font=fuente(13, bold=True), fill=AZUL_OSCURO)
        razon = w["razon"][:40] + "..." if len(w["razon"]) > 40 else w["razon"]
        draw.text((88,  y + 10), razon, font=fuente(13), fill=TEXTO_G)
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
    if bloqueado: draw.arc([(56, 42), (104, 98)],  start=180, end=0,   fill=AZUL_OSCURO, width=10)
    else:         draw.arc([(68, 30), (116, 86)],  start=180, end=360, fill=AZUL_OSCURO, width=10)
    draw.ellipse([(71, 103), (89, 121)], fill=FONDO_G)
    draw.rounded_rectangle([(76, 112), (84, 126)], radius=3, fill=FONDO_G)
    draw.text((144, 32), "Canal Bloqueado" if bloqueado else "Canal Desbloqueado", font=fuente(22, bold=True), fill=TEXTO_G)
    draw.rectangle([(144, 62), (654, 63)], fill=GRIS_G)
    draw.text((144, 76), "CANAL",           font=fuente(12),            fill=SUB_G)
    draw.text((144, 96), f"# {canal.name}", font=fuente(15, bold=True), fill=TEXTO_G)
    draw.text((144, 136), "Nadie puede enviar mensajes." if bloqueado else "Ya pueden enviar mensajes.", font=fuente(13), fill=AZUL_OSCURO)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="lock.png")

async def generar_ship(u1: discord.Member, u2: discord.Member, pct: int) -> discord.File:
    W, H = 680, 200
    img  = Image.new("RGBA", (W, H), FONDO_G)
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
    draw.text((85,  162), n1, font=fuente(13, bold=True), fill=TEXTO_G, anchor="mt")
    draw.text((595, 162), n2, font=fuente(13, bold=True), fill=TEXTO_G, anchor="mt")
    draw.rounded_rectangle([(160, 82), (520, 118)], radius=18, fill=GRIS_G)
    fill_w = int(160 + (360 * pct / 100))
    if fill_w > 160: draw.rounded_rectangle([(160, 82), (fill_w, 118)], radius=18, fill=AZUL_OSCURO)
    draw.text((340, 100), f"{pct}%", font=fuente(20, bold=True), fill=TEXTO_G, anchor="mm")
    if pct >= 90:   frase = "Almas gemelas de otra dimension"
    elif pct >= 75: frase = "El amor es inevitable entre estos dos"
    elif pct >= 60: frase = "Hay chispa, pero falta avivarlo"
    elif pct >= 40: frase = "Podria funcionar... o no"
    elif pct >= 20: frase = "Mejor como amigos"
    else:           frase = "Incompatibles al maximo nivel"
    draw.text((340, 140), frase, font=fuente(12), fill=SUB_G, anchor="mt")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ship.png")

async def generar_logro(usuario: discord.Member, titulo: str, descripcion: str) -> discord.File:
    W, H = 680, 160
    img  = Image.new("RGBA", (W, H), (10, 10, 10))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    cx, cy, radio = 80, 76, 48
    draw.ellipse([(cx-radio, cy-radio), (cx+radio, cy+radio)], fill=(25,25,25), outline=AZUL_OSCURO, width=2)
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, radio * 2)
        img.paste(av, (cx-radio, cy-radio), av)
        draw.ellipse([(cx-radio, cy-radio), (cx+radio, cy+radio)], outline=AZUL_OSCURO, width=2)
    except:
        draw.ellipse([(cx-14, cy-28), (cx+14, cy)],    fill=GRIS_G)
        draw.ellipse([(cx-26, cy+2),  (cx+26, cy+46)], fill=GRIS_G)
    tx = 155
    draw.text((tx, 18), "LOGRO DESBLOQUEADO", font=fuente(12, bold=True), fill=AZUL_OSCURO)
    draw.rectangle([(tx, 38), (W-24, 39)], fill=GRIS_G)
    draw.text((tx, 48), (titulo[:38]+"..." if len(titulo)>38 else titulo), font=fuente(20, bold=True), fill=TEXTO_G)
    draw.text((tx, 80), (descripcion[:60]+"..." if len(descripcion)>60 else descripcion), font=fuente(13), fill=(160,163,172))
    nombre = usuario.display_name[:22]+"..." if len(usuario.display_name)>22 else usuario.display_name
    draw.text((tx, 114), f"Logrado por {nombre}", font=fuente(12), fill=(160,163,172))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="logro.png")

async def generar_spotify_card(usuario: discord.Member, actividad: discord.Spotify) -> discord.File:
    W, H = 680, 180
    img  = Image.new("RGBA", (W, H), FONDO_G)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=AZUL_OSCURO)
    try:
        portada = await descargar_imagen(actividad.album_cover_url)
        portada = portada.resize((130, 130)).convert("RGBA")
        mask    = Image.new("L", (130, 130), 0)
        ImageDraw.Draw(mask).rounded_rectangle([(0,0),(130,130)], radius=10, fill=255)
        portada_r = Image.new("RGBA", (130, 130), (0,0,0,0))
        portada_r.paste(portada, (0,0), mask)
        img.paste(portada_r, (30, 25), portada_r)
    except:
        draw.rounded_rectangle([(30,25),(160,155)], radius=10, fill=GRIS_G)
    draw.rounded_rectangle([(29,24),(161,156)], radius=10, outline=AZUL_OSCURO, width=2)
    draw.text((182, 28), f"{usuario.display_name} esta escuchando", font=fuente(13), fill=SUB_G)
    cancion = actividad.title[:30]+"..." if len(actividad.title)>30 else actividad.title
    draw.text((182, 50), cancion,          font=fuente(20, bold=True), fill=TEXTO_G)
    draw.text((182, 78), actividad.artist, font=fuente(14),            fill=AZUL_OSCURO)
    album = actividad.album[:35]+"..." if len(actividad.album)>35 else actividad.album
    draw.text((182, 100), album, font=fuente(12), fill=SUB_G)
    draw.rectangle([(182,118),(645,119)], fill=GRIS_G)
    ahora        = discord.utils.utcnow()
    duracion     = actividad.duration.total_seconds()
    transcurrido = (ahora - actividad.start).total_seconds()
    progreso     = min(transcurrido / duracion, 1.0) if duracion > 0 else 0
    draw.rounded_rectangle([(182,128),(645,136)], radius=4, fill=GRIS_G)
    fill_w = int(182 + (463 * progreso))
    if fill_w > 182: draw.rounded_rectangle([(182,128),(fill_w,136)], radius=4, fill=BLANCO)
    fmt = lambda s: f"{int(s)//60}:{int(s)%60:02}"
    draw.text((182, 148), fmt(max(transcurrido, 0)), font=fuente(11), fill=SUB_G)
    draw.text((645, 148), fmt(duracion),              font=fuente(11), fill=SUB_G, anchor="ra")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="spotify.png")

# =========================================================
# IA — HELPERS
# =========================================================

PALABRAS_IMAGEN = ["imagen","foto","dibujo","genera","wallpaper","crea","hazme",
                   "dibujame","pintame","ilustra","generame","muestrame"]

async def generar_imagen_ia(mensaje: str):
    prompt = mensaje.lower()
    for p in PALABRAS_IMAGEN: prompt = prompt.replace(p, "")
    prompt = re.sub(r'\s+', ' ', prompt).strip() or mensaje
    seed   = random.randint(1, 999999)
    url    = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt[:500])}?w=512&h=512&seed={seed}&nologo=true"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    return await resp.read(), prompt, seed
    except: pass
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
        return texto[:500]+"..." if len(texto)>500 else texto
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
            embed = discord.Embed(color=AZUL_IPOD_NUM)
            user_text = self.mensaje_original[:500]+"..." if len(self.mensaje_original)>500 else self.mensaje_original
            embed.add_field(name=f"**{interaction.user.display_name}**", value=f"> {user_text}", inline=False)
            bot_text = respuesta[:500]+"..." if len(respuesta)>500 else respuesta
            embed.add_field(name="**Misti**", value=f"> {bot_text}", inline=False)
            await interaction.edit_original_response(embed=embed, view=RegenerarButton(interaction.user.id, self.mensaje_original))
        except Exception as e:
            await interaction.edit_original_response(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> Error: `{str(e)[:100]}`"), view=None)

async def responder_ask(destino, autor, mensaje: str, es_reply: bool = False):
    nombre_servidor = autor.guild.name if hasattr(autor, 'guild') and autor.guild else "DM"
    if any(p in mensaje.lower() for p in PALABRAS_IMAGEN):
        img_data, prompt, seed = await generar_imagen_ia(mensaje)
        if img_data:
            archivo = discord.File(io.BytesIO(img_data), filename="misti_art.png")
            embed   = discord.Embed(title="Imagen generada", description=f"> **Prompt:** {prompt[:200]}", color=AZUL_IPOD_NUM)
            embed.set_image(url="attachment://misti_art.png")
            if seed: embed.set_footer(text=f"Seed: {seed}")
            if es_reply: await destino.reply(embed=embed, file=archivo, mention_author=False)
            else:        await destino.send(embed=embed, file=archivo)
        else:
            embed = discord.Embed(color=AZUL_IPOD_NUM, description="> No pude generar la imagen, intenta con otro prompt.")
            if es_reply: await destino.reply(embed=embed, mention_author=False)
            else:        await destino.send(embed=embed)
        return
    agregar_memoria(autor.id, "user", mensaje)
    respuesta = await generar_respuesta_groq(autor.id, mensaje, autor.display_name, nombre_servidor)
    agregar_memoria(autor.id, "assistant", respuesta)
    embed     = discord.Embed(color=AZUL_IPOD_NUM)
    user_text = mensaje[:500]+"..." if len(mensaje)>500 else mensaje
    embed.add_field(name=f"**{autor.display_name}**", value=f"> {user_text}", inline=False)
    bot_text  = respuesta[:500]+"..." if len(respuesta)>500 else respuesta
    embed.add_field(name="**Misti**", value=f"> {bot_text}", inline=False)
    view = RegenerarButton(autor.id, mensaje)
    if es_reply: await destino.reply(embed=embed, view=view, mention_author=False)
    else:        await destino.send(embed=embed, view=view)

# =========================================================
# LAST.FM — HELPER
# =========================================================

async def buscar_cancion_exacta(artista: str, cancion: str) -> dict:
    if not LASTFM_API_KEY: return None
    url = (f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo"
           f"&api_key={LASTFM_API_KEY}&artist={urllib.parse.quote(artista.strip())}"
           f"&track={urllib.parse.quote(cancion.strip())}&format=json")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200: return None
                data = await resp.json()
        if "error" in data: return None
        track = data.get("track")
        if not track: return None
        nombre         = track.get("name", cancion)
        artista_nombre = track.get("artist", {}).get("name", artista)
        album          = track.get("album", {}).get("title", "Sin álbum")
        duracion_seg   = int(track.get("duration") or 0)
        duracion_texto = f"{duracion_seg//60}:{duracion_seg%60:02d}" if duracion_seg else "Desconocida"
        imagenes       = track.get("album", {}).get("image", [])
        cover_url      = next((img["#text"] for img in reversed(imagenes) if img.get("#text")), "")
        try:
            oyentes_num = int(track.get("listeners", 0))
            oyentes_texto = f"{oyentes_num/1_000_000:.1f}M" if oyentes_num>=1_000_000 else f"{oyentes_num/1_000:.1f}K" if oyentes_num>=1_000 else str(oyentes_num)
        except: oyentes_texto = "N/A"
        año = ""
        fecha_raw = track.get("album", {}).get("date", {})
        if isinstance(fecha_raw, dict):
            fecha_texto = fecha_raw.get("#text", "")
            if fecha_texto and len(fecha_texto) >= 4: año = fecha_texto[:4]
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
                        data     = await resp.json()
                        imagenes = data.get("artist", {}).get("image", [])
                        PLACEHOLDER = "2a96cbd8b46e442fc41c2b86b821562f"
                        for img in reversed(imagenes):
                            texto = img.get("#text", "")
                            if texto and PLACEHOLDER not in texto: return texto
        except: pass
    try:
        mb_url  = (f"https://musicbrainz.org/ws/2/artist/?query=artist:{urllib.parse.quote(nombre_artista.strip())}&fmt=json&limit=1")
        headers = {"User-Agent": "MistiBot/1.0 (discord bot)"}
        async with aiohttp.ClientSession() as session:
            async with session.get(mb_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200: return ""
                mb_data  = await resp.json()
                artistas = mb_data.get("artists", [])
                if not artistas: return ""
                mbid = artistas[0].get("id", "")
            if not mbid: return ""
            rel_url = f"https://musicbrainz.org/ws/2/artist/{mbid}?inc=url-rels&fmt=json"
            async with session.get(rel_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200: return ""
                rel_data   = await resp.json()
                relaciones = rel_data.get("relations", [])
            wikidata_id, wiki_title = "", ""
            for rel in relaciones:
                url_rel = rel.get("url", {}).get("resource", "")
                if "wikidata.org/wiki/" in url_rel:   wikidata_id = url_rel.split("/wiki/")[-1]
                if "wikipedia.org/wiki/" in url_rel and not wiki_title: wiki_title = url_rel.split("/wiki/")[-1]
            if wikidata_id:
                wd_url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"
                async with session.get(wd_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        wd_data = await resp.json()
                        claims  = wd_data.get("entities", {}).get(wikidata_id, {}).get("claims", {})
                        imagenes_wd = claims.get("P18", [])
                        if imagenes_wd:
                            nombre_archivo = imagenes_wd[0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
                            if nombre_archivo:
                                nombre_enc = nombre_archivo.replace(" ", "_")
                                md5        = hashlib.md5(nombre_enc.encode()).hexdigest()
                                return (f"https://upload.wikimedia.org/wikipedia/commons/"
                                        f"{md5[0]}/{md5[0:2]}/{urllib.parse.quote(nombre_enc)}")
            if wiki_title:
                wp_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
                async with session.get(wp_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        wp_data   = await resp.json()
                        thumbnail = wp_data.get("thumbnail", {}).get("source", "")
                        if thumbnail: return re.sub(r'/\d+px-', '/800px-', thumbnail)
    except Exception as e:
        print(f"[obtener_foto_artista] Error: {e}")
    return ""

# =========================================================
# PENSAMIENTO — VIEW
# =========================================================

class PensamientoView(discord.ui.View):
    def __init__(self, autor_id: int, texto: str):
        super().__init__(timeout=60)
        self.autor_id = autor_id; self.texto = texto

    @discord.ui.select(placeholder="Selecciona la duración", options=[
        discord.SelectOption(label="1 hora",     value="1h",      emoji="🕐"),
        discord.SelectOption(label="5 horas",    value="5h",      emoji="🕔"),
        discord.SelectOption(label="1 día",      value="1d",      emoji="📅"),
        discord.SelectOption(label="1 semana",   value="1w",      emoji="📆"),
        discord.SelectOption(label="1 mes",      value="1m",      emoji="🗓️"),
        discord.SelectOption(label="Para siempre", value="forever", emoji="♾️"),
    ])
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("> Solo quien ejecutó el comando puede seleccionar.", ephemeral=True); return
        dur = select.values[0]
        mapa = {"1h": (3600, "1 hora"), "5h": (18000, "5 horas"), "1d": (86400, "1 día"),
                "1w": (604800, "1 semana"), "1m": (2592000, "1 mes"), "forever": (None, "para siempre")}
        segundos, texto_dur = mapa[dur]
        texto_pens = self.texto[:120]+"..." if len(self.texto)>120 else self.texto
        try:
            await bot.change_presence(activity=discord.CustomActivity(name=texto_pens))
            embed = discord.Embed(title="Pensamiento actualizado",
                                  description=f"> **Pensamiento:** {texto_pens}\n> **Duración:** {texto_dur}",
                                  color=AZUL_IPOD_NUM)
            await interaction.response.edit_message(embed=embed, view=None)
            if segundos:
                await asyncio.sleep(segundos)
                actividad = bot.activity
                if actividad and isinstance(actividad, discord.CustomActivity) and actividad.name == texto_pens:
                    await bot.change_presence(activity=None)
                    try:
                        await interaction.channel.send(embed=discord.Embed(color=AZUL_IPOD_NUM,
                            description=f"> El pensamiento **{texto_pens}** ha expirado después de {texto_dur}"))
                    except: pass
        except Exception as e:
            await interaction.response.edit_message(content=f"> Error: `{str(e)[:100]}`", view=None)

# =========================================================
# GIVEAWAY — MODAL Y VIEW
# =========================================================

class GiveawayView(discord.ui.View):
    def __init__(self, premio, segundos, duracion_texto, organizador_id, mensaje_id, canal_id, guild_id):
        super().__init__(timeout=segundos)
        self.premio = premio; self.duracion_texto = duracion_texto
        self.organizador_id = organizador_id; self.mensaje_id = mensaje_id
        self.canal_id = canal_id; self.guild_id = guild_id
        self.participantes = []; self.finalizado = False

    @discord.ui.button(label="PARTICIPAR", style=discord.ButtonStyle.primary)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.finalizado:
            await interaction.response.send_message("> Este giveaway ya finalizó.", ephemeral=True); return
        if interaction.user.id in self.participantes:
            await interaction.response.send_message("> Ya estás participando.", ephemeral=True); return
        self.participantes.append(interaction.user.id)
        await interaction.response.send_message(f"> **{interaction.user.display_name}** participó!", ephemeral=True)
        try:
            canal  = interaction.guild.get_channel(self.canal_id)
            msg    = await canal.fetch_message(self.mensaje_id)
            old_e  = msg.embeds[0]
            new_e  = discord.Embed(title=old_e.title, description=old_e.description, color=old_e.color)
            for field in old_e.fields:
                new_e.add_field(name=field.name,
                                value=f"```{len(self.participantes)} personas```" if field.name == "> Participantes" else field.value,
                                inline=field.inline)
            if old_e.footer: new_e.set_footer(text=old_e.footer.text)
            await msg.edit(embed=new_e, view=self)
        except: pass

class GiveawayModal(discord.ui.Modal, title="Crear Giveaway"):
    def __init__(self, canal_id, guild_id):
        super().__init__(timeout=300)
        self.canal_id = canal_id; self.guild_id = guild_id
        self.premio   = discord.ui.TextInput(label="Cantidad del premio (monedas)", placeholder="1000", min_length=1, max_length=10)
        self.cantidad = discord.ui.TextInput(label="Cantidad de tiempo", placeholder="10", min_length=1, max_length=3)
        self.unidad   = discord.ui.TextInput(label="Unidad (m/h/d)", placeholder="m = minutos, h = horas, d = días", min_length=1, max_length=1)
        self.motivo   = discord.ui.TextInput(label="Motivo (opcional)", placeholder="Por llegar a 100 miembros", required=False, max_length=100)
        for item in [self.premio, self.cantidad, self.unidad, self.motivo]:
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            premio   = int(self.premio.value)
            cantidad = int(self.cantidad.value)
        except ValueError:
            await interaction.response.send_message("> Premio y tiempo deben ser números.", ephemeral=True); return
        if premio <= 0 or cantidad <= 0:
            await interaction.response.send_message("> Los valores deben ser mayores a 0.", ephemeral=True); return
        unidad = self.unidad.value.lower()
        if unidad == 'm':   segundos, duracion_texto = cantidad*60,    f"{cantidad} minuto{'s' if cantidad!=1 else ''}"
        elif unidad == 'h': segundos, duracion_texto = cantidad*3600,  f"{cantidad} hora{'s' if cantidad!=1 else ''}"
        elif unidad == 'd': segundos, duracion_texto = cantidad*86400, f"{cantidad} día{'s' if cantidad!=1 else ''}"
        else:
            await interaction.response.send_message("> Unidad inválida. Usa m, h o d.", ephemeral=True); return
        if segundos < 60:    await interaction.response.send_message("> Mínimo 1 minuto.", ephemeral=True); return
        if segundos > 604800: await interaction.response.send_message("> Máximo 7 días.", ephemeral=True); return
        motivo        = self.motivo.value or "Sorteo especial"
        fecha_fin     = datetime.now() + dt.timedelta(seconds=segundos)
        timestamp_fin = int(fecha_fin.timestamp())
        embed = discord.Embed(title="¡NUEVO GIVEAWAY!", color=AZUL_IPOD_NUM,
                              description=f"> **Premio:** ${premio:,} monedas\n> **Motivo:** {motivo}\n\n**¡Haz clic abajo para participar!**")
        embed.add_field(name="> Termina",         value=f"<t:{timestamp_fin}:R>", inline=True)
        embed.add_field(name="> Participantes",   value="```0 personas```",       inline=False)
        embed.add_field(name="> Organizado por",  value=interaction.user.mention, inline=False)
        embed.set_footer(text="¡Suerte a todos!")
        await interaction.response.defer()
        view   = GiveawayView(premio, segundos, duracion_texto, interaction.user.id, None, interaction.channel_id, interaction.guild_id)
        mensaje = await interaction.followup.send(embed=embed, view=view, wait=True)
        view.mensaje_id = mensaje.id
        giveaways_activos[mensaje.id] = view
        asyncio.create_task(_finalizar_giveaway(mensaje.id, segundos, view, interaction.channel_id, interaction.guild_id))

async def _finalizar_giveaway(mensaje_id, segundos, view, canal_id, guild_id):
    await asyncio.sleep(segundos)
    if mensaje_id not in giveaways_activos: return
    view.finalizado = True
    if view.participantes:
        ganador_id = random.choice(view.participantes)
        data = get_user_eco(guild_id, ganador_id)
        data["coins"] += view.premio
        guardar_economia()
        embed_final = discord.Embed(title="GIVEAWAY FINALIZADO",
                                    description=f"> **GANADOR:** <@{ganador_id}>\n> **Premio:** ${view.premio:,}\n\n¡Felicitaciones!",
                                    color=AZUL_IPOD_NUM)
        for guild in bot.guilds:
            if guild.id == guild_id:
                canal = guild.get_channel(canal_id)
                if canal:
                    try:
                        msg = await canal.fetch_message(mensaje_id)
                        await msg.edit(embed=embed_final, view=None)
                        await canal.send(f"¡Felicidades <@{ganador_id}>! Ganaste **${view.premio:,}**! 🎉")
                    except: pass
                break
    giveaways_activos.pop(mensaje_id, None)

# =========================================================
# ANONIMOS — MODAL Y VIEW
# =========================================================

class ModalAnonimo(discord.ui.Modal, title="Mensaje Anónimo"):
    contenido = discord.ui.TextInput(label="Tu mensaje", style=discord.TextStyle.long,
                                     placeholder="Escribe aquí tu mensaje anónimo...", min_length=1, max_length=1000)
    def __init__(self, canal_destino: discord.TextChannel):
        super().__init__()
        self.canal_destino = canal_destino

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        if gid not in anon_data:  anon_data[gid]  = []
        if gid not in anon_count: anon_count[gid] = 0
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
                       custom_id="btn_panel_anonimo", emoji="<:share:1505393406707372104>")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        gid = str(interaction.guild.id)
        if gid not in anon_config:
            await interaction.response.send_message("> El canal de anónimos no está configurado.", ephemeral=True); return
        canal = interaction.guild.get_channel(anon_config[gid]["canal_id"])
        if not canal:
            await interaction.response.send_message("> El canal configurado no existe.", ephemeral=True); return
        await interaction.response.send_modal(ModalAnonimo(canal))

# =========================================================
# COMANDOS — MODERACION
# =========================================================

@bot.hybrid_command(name="ban", description="Banea a un usuario")
@commands.has_permissions(ban_members=True)
async def cmd_ban(ctx: commands.Context, usuario: discord.Member, *, razon: str = "Sin razon"):
    if ctx.interaction: await ctx.defer()
    if usuario == ctx.author:
        await ctx.send("> No puedes banearte a ti mismo", ephemeral=True); return
    try:
        await usuario.ban(reason=razon)
        await ctx.send(file=await generar_ban(usuario, razon, ctx.author))
    except Exception as e:
        await ctx.send(f"> Error:\n```{e}```")

@bot.hybrid_command(name="kick", description="Expulsa a un usuario")
@commands.has_permissions(kick_members=True)
async def cmd_kick(ctx: commands.Context, usuario: discord.Member, *, razon: str = "Sin razon"):
    if ctx.interaction: await ctx.defer()
    if usuario == ctx.author:
        await ctx.send("> No puedes expulsarte a ti mismo"); return
    try:
        await usuario.kick(reason=razon)
        embed = discord.Embed(color=AZUL_IPOD_NUM)
        embed.description = f"> **{usuario.display_name}** fue expulsado\n> Razon: {razon}\n> Moderador: {ctx.author.mention}"
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error:\n```{e}```")

@bot.hybrid_command(name="timeout", description="Silencia a un usuario por X minutos")
@commands.has_permissions(moderate_members=True)
async def cmd_timeout(ctx: commands.Context, usuario: discord.Member, minutos: int, *, razon: str = "Sin razon"):
    if ctx.interaction: await ctx.defer()
    try:
        until = discord.utils.utcnow() + dt.timedelta(minutes=minutos)
        await usuario.timeout(until, reason=razon)
        embed = discord.Embed(color=AZUL_IPOD_NUM)
        embed.description = f"> **{usuario.display_name}** silenciado por `{minutos}` minutos\n> Razon: {razon}"
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error:\n```{e}```")

@bot.hybrid_command(name="warn", description="Advierte a un usuario")
@commands.has_permissions(manage_messages=True)
async def cmd_warn(ctx: commands.Context, usuario: discord.Member, *, razon: str):
    if ctx.interaction: await ctx.defer()
    gid, uid = str(ctx.guild.id), str(usuario.id)
    if gid not in warnings_data: warnings_data[gid] = {}
    if uid not in warnings_data[gid]: warnings_data[gid][uid] = []
    warnings_data[gid][uid].append({"razon": razon, "moderador": str(ctx.author), "fecha": str(datetime.now())})
    guardar_warnings()
    await ctx.send(file=await generar_warn(usuario, razon, len(warnings_data[gid][uid])))

@bot.hybrid_command(name="warnings", description="Ver warns de un usuario")
async def cmd_warnings(ctx: commands.Context, usuario: discord.Member):
    if ctx.interaction: await ctx.defer()
    gid, uid = str(ctx.guild.id), str(usuario.id)
    if gid not in warnings_data or uid not in warnings_data[gid]:
        await ctx.send("> Ese usuario no tiene warnings"); return
    await ctx.send(file=await generar_warnings_img(usuario, warnings_data[gid][uid]))

@bot.hybrid_command(name="clearwarns", description="Borra todos los warns de un usuario")
@commands.has_permissions(manage_messages=True)
async def cmd_clearwarns(ctx: commands.Context, usuario: discord.Member):
    gid, uid = str(ctx.guild.id), str(usuario.id)
    if gid in warnings_data and uid in warnings_data[gid]:
        warnings_data[gid][uid] = []
    guardar_warnings()
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Warns de **{usuario.display_name}** borrados"
    await ctx.send(embed=embed)

@bot.hybrid_command(name="lock", description="Bloquea el canal actual")
@commands.has_permissions(manage_channels=True)
async def cmd_lock(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    await ctx.send(file=await generar_lock(ctx.channel, bloqueado=True))

@bot.hybrid_command(name="unlock", description="Desbloquea el canal actual")
@commands.has_permissions(manage_channels=True)
async def cmd_unlock(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    await ctx.send(file=await generar_lock(ctx.channel, bloqueado=False))

@bot.hybrid_command(name="nuke", description="Clona y elimina el canal")
@commands.has_permissions(manage_channels=True)
async def cmd_nuke(ctx: commands.Context):
    canal = ctx.channel
    nuevo = await canal.clone()
    await canal.delete()
    await nuevo.send(embed=discord.Embed(title="Canal Nukeado", description="> Canal purificado exitosamente.", color=AZUL_IPOD_NUM))

@bot.hybrid_command(name="delete", description="Elimina mensajes del canal")
@commands.has_permissions(manage_messages=True)
async def cmd_delete(ctx: commands.Context, cantidad: int):
    if ctx.interaction: await ctx.defer(ephemeral=True)
    eliminados = await ctx.channel.purge(limit=cantidad)
    await ctx.send(f"> Se eliminaron {len(eliminados)} mensajes", ephemeral=True)

@bot.hybrid_command(name="afk", description="Activa tu modo AFK")
async def cmd_afk(ctx: commands.Context, *, motivo: str = "Sin motivo"):
    if ctx.interaction: await ctx.defer()
    afk_data[ctx.author.id] = {"motivo": motivo, "tiempo": time.time()}
    usuario = ctx.guild.get_member(ctx.author.id)
    await ctx.send(file=await generar_afk(usuario, motivo))

# =========================================================
# COMANDOS — ECONOMIA
# =========================================================

@bot.hybrid_command(name="balance", description="Ve tu saldo actual")
async def cmd_balance(ctx: commands.Context, usuario: discord.Member = None):
    if ctx.interaction: await ctx.defer()
    usuario = ctx.guild.get_member((usuario or ctx.author).id)
    data    = get_user_eco(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.hybrid_command(name="daily", description="Reclama tus monedas diarias")
async def cmd_daily(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    data  = get_user_eco(ctx.guild.id, ctx.author.id)
    ahora = time.time()
    if ahora - data["last_daily"] < 86400:
        restante = int(86400 - (ahora - data["last_daily"]))
        h, m, s  = restante // 3600, (restante % 3600) // 60, restante % 60
        await ctx.send(f"> Vuelve en `{h:02}:{m:02}:{s:02}`"); return
    recompensa         = random.randint(100, 500)
    data["coins"]     += recompensa
    data["last_daily"] = ahora
    guardar_economia()
    await ctx.send(content=f"> Recibiste **{recompensa}** monedas!",
                   file=await generar_balance(ctx.guild.get_member(ctx.author.id), data["coins"], data["last_daily"]))

@bot.hybrid_command(name="ranking", description="Top usuarios con más monedas")
async def cmd_ranking(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    gid = str(ctx.guild.id)
    if gid not in economia_data or not economia_data[gid]:
        await ctx.send("> Nadie tiene monedas todavia."); return
    top = sorted(economia_data[gid].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
    await ctx.send(file=await generar_ranking(ctx.guild, top))

@bot.hybrid_command(name="dar", description="(ADMIN) Agrega monedas a un usuario")
@commands.has_permissions(administrator=True)
async def cmd_dar(ctx: commands.Context, usuario: discord.Member, cantidad: int):
    if ctx.interaction: await ctx.defer()
    data = get_user_eco(ctx.guild.id, usuario.id)
    data["coins"] += cantidad
    guardar_economia()
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Se agregaron **${cantidad:,}** a {usuario.mention}\n> Saldo: **${data['coins']:,}**"
    await ctx.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.hybrid_command(name="quitar", description="(ADMIN) Quita monedas a un usuario")
@commands.has_permissions(administrator=True)
async def cmd_quitar(ctx: commands.Context, usuario: discord.Member, cantidad: int):
    if ctx.interaction: await ctx.defer()
    data = get_user_eco(ctx.guild.id, usuario.id)
    data["coins"] = max(0, data["coins"] - cantidad)
    guardar_economia()
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Se quitaron **${cantidad:,}** a {usuario.mention}\n> Saldo: **${data['coins']:,}**"
    await ctx.send(embed=embed, file=await generar_balance(usuario, data["coins"], data["last_daily"]))

@bot.hybrid_command(name="cupon", description="(ADMIN) Crea un cupón de recompensa")
@commands.has_permissions(administrator=True)
async def cmd_cupon(ctx: commands.Context, codigo: str, recompensa: int):
    gid = str(ctx.guild.id)
    if gid not in cupones_data: cupones_data[gid] = {}
    cupones_data[gid][codigo.upper()] = {"recompensa": recompensa, "usado_por": []}
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Cupon `{codigo.upper()}` creado\n> Recompensa: **${recompensa:,}**"
    await ctx.send(embed=embed)

@bot.hybrid_command(name="canjear", description="Canjea un cupón de recompensa")
async def cmd_canjear(ctx: commands.Context, codigo: str):
    gid = str(ctx.guild.id)
    if gid not in cupones_data or codigo.upper() not in cupones_data[gid]:
        await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> Cupon invalido")); return
    cupon = cupones_data[gid][codigo.upper()]
    if ctx.author.id in cupon["usado_por"]:
        await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> Ya usaste este cupon")); return
    cupon["usado_por"].append(ctx.author.id)
    eco = get_user_eco(ctx.guild.id, ctx.author.id)
    eco["coins"] += cupon["recompensa"]
    guardar_economia()
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> Canjeado! Ganaste: **${cupon['recompensa']:,}**"))

@bot.hybrid_command(name="tragamonedas", description="Juega en el tragamonedas")
async def cmd_tragamonedas(ctx: commands.Context, apuesta: int):
    if ctx.interaction: await ctx.defer()
    data = get_user_eco(ctx.guild.id, ctx.author.id)
    if apuesta <= 0:
        await ctx.send("> La apuesta debe ser positiva"); return
    if apuesta > data["coins"]:
        await ctx.send(f"> No tenes suficientes monedas. Tenes ${data['coins']}"); return
    emojis = ["🐬","🧊","🌊","🐳","🐋","💎","🪼"]
    s1, s2, s3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
    if s1==s2==s3=="💎": ganancia, msg = apuesta*5, "> PREMIO MAYOR! 3 DIAMANTES!"
    elif s1==s2==s3:     ganancia, msg = apuesta*3, "> 3 IGUALES!"
    elif s1==s2 or s2==s3 or s1==s3: ganancia, msg = apuesta*1, "> PAR! Recuperas tu apuesta"
    else:                ganancia, msg = 0, "> Nada, perdiste"
    data["coins"] += ganancia - apuesta
    guardar_economia()
    embed = discord.Embed(title="TRAGAMONEDAS", color=AZUL_IPOD_NUM)
    embed.add_field(name="> Resultado",   value=f"```| {s1} | {s2} | {s3} |```", inline=False)
    embed.add_field(name="> Apuesta",     value=f"${apuesta}",      inline=True)
    embed.add_field(name="> Ganancia",    value=f"${ganancia}",     inline=True)
    embed.add_field(name="> Resultado",   value=msg,                inline=False)
    embed.add_field(name="> Nuevo saldo", value=f"${data['coins']}", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="giveaway", description="(ADMIN) Crea un giveaway con premio en monedas")
@commands.has_permissions(administrator=True)
async def cmd_giveaway(ctx: commands.Context):
    if ctx.interaction:
        modal = GiveawayModal(ctx.channel.id, ctx.guild.id)
        await ctx.interaction.response.send_modal(modal)
    else:
        await ctx.send("> Este comando solo funciona como slash command `/giveaway`.")

# =========================================================
# COMANDOS — NIVELES
# =========================================================

@bot.hybrid_command(name="nivel", description="Ve tu nivel actual")
async def cmd_nivel(ctx: commands.Context, usuario: discord.Member = None):
    if ctx.interaction: await ctx.defer()
    usuario = ctx.guild.get_member((usuario or ctx.author).id)
    data    = get_xp(ctx.guild.id, usuario.id)
    await ctx.send(file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.hybrid_command(name="setcanalnivel", description="(ADMIN) Canal donde se anuncian los niveles")
@commands.has_permissions(administrator=True)
async def cmd_setcanalnivel(ctx: commands.Context, canal: discord.TextChannel):
    nivel_canal[ctx.guild.id] = canal.id
    guardar_config()
    await ctx.send(f"> Canal de niveles seteado en {canal.mention}")

@bot.hybrid_command(name="agregnivel", description="(ADMIN) Agrega niveles a un usuario")
@commands.has_permissions(administrator=True)
async def cmd_agregnivel(ctx: commands.Context, usuario: discord.Member, cantidad: int):
    if ctx.interaction: await ctx.defer()
    data = get_xp(ctx.guild.id, usuario.id)
    data["level"] += cantidad
    guardar_xp()
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Se agregaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await ctx.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

@bot.hybrid_command(name="quitarnivel", description="(ADMIN) Quita niveles a un usuario")
@commands.has_permissions(administrator=True)
async def cmd_quitarnivel(ctx: commands.Context, usuario: discord.Member, cantidad: int):
    if ctx.interaction: await ctx.defer()
    data = get_xp(ctx.guild.id, usuario.id)
    data["level"] = max(1, data["level"] - cantidad)
    guardar_xp()
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Se quitaron **{cantidad}** niveles a {usuario.mention}\n> Nivel actual: **{data['level']}**"
    await ctx.send(embed=embed, file=await generar_nivel(usuario, data["level"], data["xp"], xp_para_nivel(data["level"])))

# =========================================================
# COMANDOS — CONFIGURACION
# =========================================================

@bot.hybrid_command(name="setwelc", description="Configura el mensaje de bienvenida")
@commands.has_permissions(administrator=True)
async def cmd_setwelc(ctx: commands.Context, canal: discord.TextChannel,
                      titulo: str = None, descripcion: str = None, color: str = None,
                      imagen: str = None, footer: str = None):
    try:    color_final = int(color.replace("#", ""), 16) if color else AZUL_IPOD_NUM
    except: color_final = AZUL_IPOD_NUM
    welc_config[ctx.guild.id] = {"canal": canal.id, "titulo": titulo, "desc": descripcion,
                                  "color": color_final, "autor": (None, None), "imagen": imagen, "footer": (footer, None)}
    guardar_config()
    await ctx.send(f"> Bienvenida activada en {canal.mention}")

@bot.hybrid_command(name="setbye", description="Configura el mensaje de despedida")
@commands.has_permissions(administrator=True)
async def cmd_setbye(ctx: commands.Context, canal: discord.TextChannel,
                     titulo: str = None, descripcion: str = None, color: str = None,
                     imagen: str = None, footer: str = None):
    try:    color_final = int(color.replace("#", ""), 16) if color else AZUL_IPOD_NUM
    except: color_final = AZUL_IPOD_NUM
    bye_config[ctx.guild.id] = {"canal": canal.id, "titulo": titulo, "desc": descripcion,
                                 "color": color_final, "autor": (None, None), "imagen": imagen, "footer": (footer, None)}
    guardar_config()
    await ctx.send(f"> Despedida activada en {canal.mention}")

@bot.hybrid_command(name="resetwelc", description="Desactiva el mensaje de bienvenida")
@commands.has_permissions(administrator=True)
async def cmd_resetwelc(ctx: commands.Context):
    welc_config.pop(ctx.guild.id, None); guardar_config()
    await ctx.send("> Bienvenida desactivada")

@bot.hybrid_command(name="resetbye", description="Desactiva el mensaje de despedida")
@commands.has_permissions(administrator=True)
async def cmd_resetbye(ctx: commands.Context):
    bye_config.pop(ctx.guild.id, None); guardar_config()
    await ctx.send("> Despedida desactivada")

@bot.hybrid_command(name="embed", description="Envía un embed personalizado")
@commands.has_permissions(administrator=True)
async def cmd_embed(ctx: commands.Context, canal: discord.TextChannel = None,
                    titulo: str = None, descripcion: str = None, color: str = None,
                    imagen: str = None, footer: str = None):
    canal = canal or ctx.channel
    try:    color_final = int(color.replace("#", ""), 16) if color else AZUL_IPOD_NUM
    except: color_final = AZUL_IPOD_NUM
    embed = discord.Embed(title=titulo or "", description=descripcion or "", color=color_final)
    if imagen: embed.set_image(url=imagen)
    if footer: embed.set_footer(text=footer)
    await canal.send(embed=embed)
    await ctx.send("> Embed enviado", ephemeral=True)

@bot.hybrid_command(name="setanonimos", description="Configura el canal de mensajes anónimos")
@commands.has_permissions(administrator=True)
async def cmd_setanonimos(ctx: commands.Context, canal: discord.TextChannel):
    if ctx.interaction: await ctx.defer(ephemeral=True)
    gid = str(ctx.guild.id)
    anon_config[gid] = {"canal_id": canal.id}
    anon_count[gid]  = 0
    anon_data[gid]   = []
    guardar_anonimos(); guardar_config()
    embed_panel = discord.Embed(title="Mensajes Anónimos",
                                description="Estos son los mensajes anónimos.\n\n> Usa el botón de abajo para enviar tu mensaje anónimo.",
                                color=AZUL_IPOD_NUM)
    await canal.send(embed=embed_panel, view=VistaPanelAnonimo(canal))
    await ctx.send(f"> Panel configurado en {canal.mention}.", ephemeral=True)

@bot.hybrid_command(name="panelanonimos", description="Reenvía el panel de mensajes anónimos")
@commands.has_permissions(administrator=True)
async def cmd_panelanonimos(ctx: commands.Context):
    if ctx.interaction: await ctx.defer(ephemeral=True)
    gid = str(ctx.guild.id)
    if gid not in anon_config:
        await ctx.send("> Primero configura con `/setanonimos`."); return
    canal = ctx.guild.get_channel(anon_config[gid]["canal_id"])
    if not canal:
        await ctx.send("> Canal no encontrado."); return
    total = anon_count.get(gid, 0)
    embed_panel = discord.Embed(title="Mensajes Anónimos",
                                description="Estos son los mensajes anónimos.\n\n> Usa el botón de abajo para enviar tu mensaje anónimo.",
                                color=AZUL_IPOD_NUM)
    embed_panel.set_footer(text=f"Mensajes enviados hasta ahora: {total}")
    await canal.send(embed=embed_panel, view=VistaPanelAnonimo(canal))
    await ctx.send(f"> Panel reenviado en {canal.mention}.", ephemeral=True)

@bot.hybrid_command(name="pensamiento", description="(ADMIN) Cambia el estado del bot")
@commands.has_permissions(administrator=True)
async def cmd_pensamiento(ctx: commands.Context, *, texto: str):
    if len(texto) > 120:
        await ctx.send("> Máximo 120 caracteres."); return
    embed = discord.Embed(title="Establecer pensamiento",
                          description=f"> **Pensamiento:** {texto}\n\nSelecciona la duración:",
                          color=AZUL_IPOD_NUM)
    await ctx.send(embed=embed, view=PensamientoView(ctx.author.id, texto))

@bot.hybrid_command(name="resetpensamiento", description="(ADMIN) Elimina el estado del bot")
@commands.has_permissions(administrator=True)
async def cmd_resetpensamiento(ctx: commands.Context):
    await bot.change_presence(activity=None)
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> Pensamiento eliminado."))

# =========================================================
# COMANDOS — MUSICA
# =========================================================

@bot.hybrid_command(name="spotify", description="Muestra la música que escucha un usuario")
async def cmd_spotify(ctx: commands.Context, usuario: discord.Member = None):
    if ctx.interaction: await ctx.defer()
    usuario   = ctx.guild.get_member((usuario or ctx.author).id)
    actividad = discord.utils.find(lambda a: isinstance(a, discord.Spotify), usuario.activities)
    if not actividad:
        await ctx.send(f"> **{usuario.name} no esta escuchando Spotify**"); return
    await ctx.send(file=await generar_spotify_card(usuario, actividad))

@bot.hybrid_command(name="cancion", description="Busca una canción exacta en Last.fm")
async def cmd_cancion(ctx: commands.Context, artista: str, *, cancion: str):
    if ctx.interaction: await ctx.defer()
    if not LASTFM_API_KEY:
        await ctx.send("> `LASTFM_API_KEY` no configurada."); return
    if len(artista.strip()) < 2 or len(cancion.strip()) < 2:
        await ctx.send("> Artista y canción deben tener al menos 2 caracteres."); return
    try:
        track = await buscar_cancion_exacta(artista, cancion)
        if not track:
            await ctx.send(f"> No se encontró **{cancion}** de **{artista}**"); return
        embed = discord.Embed(title=track["nombre"], description=f"**{track['artista']}**",
                              color=AZUL_IPOD_NUM, url=track["url"] or None)
        embed.add_field(name="> Álbum",    value=track["album"],    inline=True)
        embed.add_field(name="> Duración", value=track["duracion"], inline=True)
        if track["año"]:     embed.add_field(name="> Año",     value=track["año"],     inline=True)
        if track["oyentes"] != "N/A": embed.add_field(name="> Oyentes", value=track["oyentes"], inline=True)
        if track["cover"]:   embed.set_thumbnail(url=track["cover"])
        embed.set_footer(text=f"Last.fm | {artista} - {cancion}")
        embed.set_author(name="Misti Music")
        view = discord.ui.View()
        if track["url"]: view.add_item(discord.ui.Button(label="Escuchar en Last.fm", url=track["url"], style=discord.ButtonStyle.link))
        await ctx.send(embed=embed, view=view)
    except Exception as e:
        await ctx.send(f"> Error: `{str(e)[:100]}`")

@bot.hybrid_command(name="artista", description="Busca información de un artista en Last.fm")
async def cmd_artista(ctx: commands.Context, *, artista: str):
    if ctx.interaction: await ctx.defer()
    if not LASTFM_API_KEY:
        await ctx.send("> `LASTFM_API_KEY` no configurada."); return
    if len(artista.strip()) < 2:
        await ctx.send("> Mínimo 2 caracteres."); return
    try:
        url = (f"http://ws.audioscrobbler.com/2.0/?method=artist.getInfo"
               f"&api_key={LASTFM_API_KEY}&artist={urllib.parse.quote(artista.strip())}&format=json")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    await ctx.send(f"> Error Last.fm ({resp.status})"); return
                data = await resp.json()
        if "error" in data:
            await ctx.send(f"> Artista **{artista}** no encontrado."); return
        info = data.get("artist")
        if not info:
            await ctx.send("> Sin información."); return
        nombre     = info.get("name", artista)
        url_lastfm = info.get("url", "")
        stats      = info.get("stats", {})
        try:    oyentes = f"{int(stats.get('listeners', 0)):,}".replace(",", ".")
        except: oyentes = "N/A"
        try:    reproducciones = f"{int(stats.get('playcount', 0)):,}".replace(",", ".")
        except: reproducciones = "N/A"
        bio_raw = info.get("bio", {}).get("summary", "")
        bio     = re.sub(r'<a href="[^"]*">[^<]*</a>', '', bio_raw)
        bio     = re.sub(r'<[^>]+>', '', bio).strip()
        bio     = (bio[:500] + "...") if len(bio) > 500 else bio or "Sin biografía."
        tags_raw = info.get("tags", {}).get("tag", [])
        if isinstance(tags_raw, dict): tags_raw = [tags_raw]
        generos = ", ".join([t.get("name", "") for t in tags_raw[:5]]) or "Sin géneros"
        similares_raw = info.get("similar", {}).get("artist", [])
        if isinstance(similares_raw, dict): similares_raw = [similares_raw]
        similares = ", ".join([a.get("name", "") for a in similares_raw[:4]]) or "N/A"
        imagen_url = await obtener_foto_artista(nombre)
        embed = discord.Embed(title=nombre, description=bio, color=AZUL_IPOD_NUM, url=url_lastfm or None)
        embed.add_field(name="> Oyentes mensuales", value=oyentes,        inline=True)
        embed.add_field(name="> Reproducciones",    value=reproducciones, inline=True)
        embed.add_field(name="> Géneros",           value=generos,        inline=False)
        if similares != "N/A": embed.add_field(name="> Artistas similares", value=similares, inline=False)
        if imagen_url: embed.set_thumbnail(url=imagen_url)
        embed.set_footer(text=f"Last.fm • {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.set_author(name="Misti Music")
        view = discord.ui.View()
        if url_lastfm: view.add_item(discord.ui.Button(label="Ver en Last.fm", url=url_lastfm, style=discord.ButtonStyle.link))
        await ctx.send(embed=embed, view=view)
    except asyncio.TimeoutError:
        await ctx.send("> Tiempo agotado.")
    except Exception as e:
        await ctx.send(f"> Error: `{str(e)[:100]}`")

@bot.hybrid_command(name="lyrics", description="Obtén la letra de una canción")
async def cmd_lyrics(ctx: commands.Context, *, cancion: str):
    if ctx.interaction: await ctx.defer()
    try:
        url = f"https://lrclib.net/api/search?q={cancion.replace(' ', '+')}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200: raise Exception(f"Error {resp.status}")
                data = await resp.json()
        if not data:
            await ctx.send("> No se encontraron resultados."); return
        r       = data[0]
        nombre  = r.get("trackName", "Sin nombre")
        artista = r.get("artistName", "Desconocido")
        album   = r.get("albumName", "")
        letra   = r.get("plainLyrics") or r.get("syncedLyrics") or "Letra no disponible"
        if letra and letra.startswith("["): letra = re.sub(r'\[\d+:\d+\.\d+\]', '', letra).strip()
        if len(letra) > 4096: letra = letra[:4000] + "\n\n*[Letra cortada]*"
        embed = discord.Embed(title=nombre, description=letra, color=AZUL_IPOD_NUM)
        embed.set_author(name=artista)
        if album: embed.set_footer(text=f"Album: {album}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error: `{str(e)[:100]}`")

@bot.hybrid_command(name="youtube", description="Busca un video en YouTube")
async def cmd_youtube(ctx: commands.Context, *, busqueda: str):
    if ctx.interaction: await ctx.defer()
    try:
        url     = "https://www.youtube.com/youtubei/v1/search?key=AIzaSyAO90d0o_cqFbnSa2Bx0-Dmp5BaM9aW0uM"
        payload = {"context": {"client": {"clientName": "WEB", "clientVersion": "2.20230101.00.00"}},
                   "query": busqueda, "params": "EgIQAQ%3D%3D"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data     = await resp.json()
                    contents = (data.get('contents',{}).get('twoColumnSearchResultsRenderer',{})
                                    .get('primaryContents',{}).get('sectionListRenderer',{}).get('contents',[]))
                    if contents and 'itemSectionRenderer' in contents[0]:
                        videos = contents[0]['itemSectionRenderer']['contents']
                        if videos:
                            v         = videos[0].get('videoRenderer', {})
                            titulo    = v.get('title',{}).get('runs',[{}])[0].get('text','Sin titulo')
                            video_id  = v.get('videoId','')
                            duracion  = v.get('lengthText',{}).get('simpleText','0:00')
                            canal     = v.get('longBylineText',{}).get('runs',[{}])[0].get('text','Desconocido')
                            thumbnail = v.get('thumbnail',{}).get('thumbnails',[{}])[-1].get('url','')
                            vistas    = v.get('viewCountText',{}).get('simpleText','0 vistas')
                            url_video = f"https://www.youtube.com/watch?v={video_id}"
                            embed = discord.Embed(color=AZUL_IPOD_NUM, title="Video Encontrado")
                            embed.add_field(name="> Titulo",   value=titulo[:100], inline=False)
                            embed.add_field(name="> Duracion", value=duracion,     inline=True)
                            embed.add_field(name="> Canal",    value=canal[:50],   inline=True)
                            embed.add_field(name="> Vistas",   value=vistas,       inline=True)
                            embed.add_field(name="> Link",     value=f"[Abrir en YouTube]({url_video})", inline=False)
                            if thumbnail: embed.set_thumbnail(url=thumbnail)
                            await ctx.send(embed=embed); return
        await ctx.send("> No se encontraron resultados")
    except Exception as e:
        await ctx.send(f"```{str(e)[:200]}```")

# =========================================================
# COMANDOS — INFO
# =========================================================

@bot.hybrid_command(name="usuario", description="Información de un usuario")
async def cmd_usuario(ctx: commands.Context, usuario: discord.Member = None):
    if ctx.interaction: await ctx.defer()
    usuario = ctx.guild.get_member((usuario or ctx.author).id)
    await ctx.send(file=await generar_userinfo(usuario))

@bot.hybrid_command(name="servidor", description="Información del servidor")
async def cmd_servidor(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    await ctx.send(file=await generar_serverinfo(ctx.guild, ctx.author))

@bot.hybrid_command(name="avatar", description="Ver avatar de un usuario")
async def cmd_avatar(ctx: commands.Context, usuario: discord.Member = None):
    usuario = usuario or ctx.author
    embed   = discord.Embed(title=f"Avatar de {usuario.name}", color=AZUL_IPOD_NUM)
    embed.set_image(url=usuario.display_avatar.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="banner", description="Banner del servidor")
async def cmd_banner(ctx: commands.Context):
    if ctx.guild.banner:
        embed = discord.Embed(title=f"Banner de {ctx.guild.name}", color=AZUL_IPOD_NUM)
        embed.set_image(url=ctx.guild.banner.url)
        await ctx.send(embed=embed)
    else:
        await ctx.send("> Este servidor no tiene banner")

@bot.hybrid_command(name="roblox", description="Perfil de Roblox de un usuario")
async def cmd_roblox(ctx: commands.Context, *, usuario: str):
    if ctx.interaction: await ctx.defer()
    try:
        async with aiohttp.ClientSession() as session:
            data_user = {"usernames": [usuario], "excludeBannedUsers": False}
            async with session.post("https://users.roblox.com/v1/usernames/users", json=data_user) as resp:
                if resp.status != 200:
                    await ctx.send("> Error conectando con Roblox"); return
                res_user = await resp.json()
                if not res_user["data"]:
                    await ctx.send(f"> El usuario **{usuario}** no existe"); return
                user_info    = res_user["data"][0]
                user_id      = user_info["id"]
                roblox_user  = user_info["name"]
                display_name = user_info["displayName"]
            async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as resp:
                res_details   = await resp.json()
                fecha_iso     = res_details["created"].split("T")[0]
                cuenta_creada = datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
            async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count") as resp:
                cantidad_amigos = (await resp.json()).get("count", 0)
            avatar_url = "https://images.rbxcdn.com/default_avatar.png"
            async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false") as resp:
                if resp.status == 200:
                    res_thumb = await resp.json()
                    if res_thumb["data"]: avatar_url = res_thumb["data"][0]["imageUrl"]
        embed = discord.Embed(color=AZUL_IPOD_NUM, title="Perfil de Roblox")
        embed.add_field(name="Usuario",       value=roblox_user,     inline=True)
        embed.add_field(name="ID",            value=user_id,         inline=True)
        embed.add_field(name="Apodo",         value=display_name,    inline=False)
        embed.add_field(name="Cuenta Creada", value=cuenta_creada,   inline=True)
        embed.add_field(name="Amigos",        value=cantidad_amigos, inline=True)
        embed.add_field(name="Perfil",        value=f"[ver](https://www.roblox.com/users/{user_id}/profile)", inline=False)
        embed.set_thumbnail(url=avatar_url)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error: {str(e)[:100]}")

@bot.hybrid_command(name="pokemon", description="Información de un Pokémon")
async def cmd_pokemon(ctx: commands.Context, *, nombre: str):
    if ctx.interaction: await ctx.defer()
    url = f"https://pokeapi.co/api/v2/pokemon/{urllib.parse.quote(nombre.lower().strip())}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send(f"> No se encontró el Pokémon: **{nombre}**"); return
            data = await resp.json()
    embed = discord.Embed(title=f"{data.get('name', nombre).capitalize()} #{data.get('id', 0)}", color=AZUL_IPOD_NUM)
    embed.add_field(name="> Altura",      value=f"{data.get('height',0)/10} m",  inline=True)
    embed.add_field(name="> Peso",        value=f"{data.get('weight',0)/10} kg", inline=True)
    embed.add_field(name="> Tipo",        value=", ".join([t['type']['name'].capitalize() for t in data.get('types',[])]), inline=True)
    embed.add_field(name="> Habilidades", value=", ".join([h['ability']['name'].capitalize() for h in data.get('abilities',[])[:3]]), inline=False)
    stats = {s['stat']['name']: s['base_stat'] for s in data.get('stats', [])}
    if stats:
        embed.add_field(name="> HP",      value=stats.get('hp',0),      inline=True)
        embed.add_field(name="> Ataque",  value=stats.get('attack',0),  inline=True)
        embed.add_field(name="> Defensa", value=stats.get('defense',0), inline=True)
    sprite = data.get('sprites', {}).get('front_default', '')
    if sprite: embed.set_thumbnail(url=sprite)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="pais", description="Información de un país")
async def cmd_pais(ctx: commands.Context, *, nombre: str):
    if ctx.interaction: await ctx.defer()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://restcountries.com/v3.1/name/{urllib.parse.quote(nombre)}") as resp:
                if resp.status != 200:
                    await ctx.send(f"> País **{nombre}** no encontrado."); return
                data = await resp.json()
        d = data[0]
        embed = discord.Embed(title=d.get('name',{}).get('official','Desconocido'), color=AZUL_IPOD_NUM)
        embed.add_field(name="> Capital",   value=", ".join(d.get('capital',['Desconocida'])), inline=True)
        embed.add_field(name="> Población", value=f"{d.get('population',0):,}",                inline=True)
        embed.add_field(name="> Área",      value=f"{d.get('area',0):,} km",                   inline=True)
        embed.add_field(name="> Idiomas",   value=", ".join(d.get('languages',{}).values())[:50], inline=True)
        moneda = list(d.get('currencies',{}).values())[0].get('name','Desconocida') if d.get('currencies') else 'Desconocida'
        embed.add_field(name="> Moneda",    value=moneda, inline=True)
        mapa    = d.get('maps',{}).get('googleMaps','')
        bandera = d.get('flags',{}).get('png','')
        if mapa:    embed.add_field(name="> Google Maps", value=f"[Ver mapa]({mapa})", inline=False)
        if bandera: embed.set_thumbnail(url=bandera)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error: `{str(e)[:100]}`")

@bot.hybrid_command(name="pelicula", description="Busca información de una película")
async def cmd_pelicula(ctx: commands.Context, *, nombre: str):
    if ctx.interaction: await ctx.defer()
    API_KEY = os.getenv("TMDB_API_KEY")
    if not API_KEY:
        await ctx.send("> `TMDB_API_KEY` no configurada."); return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={urllib.parse.quote(nombre)}&language=es") as resp:
            data       = await resp.json()
            resultados = data.get('results', [])
            if not resultados:
                await ctx.send(f"> No se encontró: **{nombre}**"); return
            peli = resultados[0]
        async with session.get(f"https://api.themoviedb.org/3/movie/{peli.get('id')}?api_key={API_KEY}&language=es") as resp:
            detalles = await resp.json()
    titulo     = detalles.get('title','Sin título')
    fecha      = detalles.get('release_date','Desconocida')[:4]
    duracion   = detalles.get('runtime',0)
    generos    = ", ".join([g.get('name','') for g in detalles.get('genres',[])])
    descripcion = detalles.get('overview','Sin descripción')
    puntaje    = detalles.get('vote_average',0)
    poster     = detalles.get('poster_path','')
    embed = discord.Embed(title=f"{titulo} ({fecha})",
                          description=descripcion[:300]+"..." if len(descripcion)>300 else descripcion,
                          color=AZUL_IPOD_NUM)
    embed.add_field(name="> Puntuación", value=f"{puntaje}/10",   inline=True)
    embed.add_field(name="> Duración",   value=f"{duracion} min", inline=True)
    embed.add_field(name="> Géneros",    value=generos[:50],      inline=True)
    if poster: embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{poster}")
    await ctx.send(embed=embed)

@bot.hybrid_command(name="libro", description="Busca información de un libro")
async def cmd_libro(ctx: commands.Context, *, query: str):
    if ctx.interaction: await ctx.defer()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&maxResults=1",
                                   timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    await ctx.send(f"> Error ({resp.status})"); return
                data = await resp.json()
        if "items" not in data:
            await ctx.send(f"> Sin resultados para: **{query}**"); return
        info       = data["items"][0]["volumeInfo"]
        titulo     = info.get("title","Sin titulo")
        autores    = ", ".join(info.get("authors",["Desconocido"]))
        raw_desc   = info.get("description","Sin descripción.")
        descripcion = (raw_desc[:500]+"...") if len(raw_desc)>500 else raw_desc
        fecha      = info.get("publishedDate","Desconocida")
        paginas    = info.get("pageCount","N/A")
        categorias = ", ".join(info.get("categories",["Sin categoria"]))
        editorial  = info.get("publisher","Desconocida")
        idioma_map = {"es":"Español","en":"Inglés","fr":"Francés","pt":"Portugués","de":"Alemán"}
        idioma     = idioma_map.get(info.get("language",""), info.get("language","Desconocido").upper())
        portada    = info.get("imageLinks",{}).get("thumbnail","").replace("http://","https://")
        enlace     = info.get("infoLink","")
        embed = discord.Embed(title=titulo, description=descripcion, color=AZUL_IPOD_NUM, url=enlace)
        embed.add_field(name="> Autor(es)",   value=autores,        inline=False)
        embed.add_field(name="> Publicación", value=fecha,          inline=True)
        embed.add_field(name="> Páginas",     value=str(paginas),   inline=True)
        embed.add_field(name="> Editorial",   value=editorial,      inline=True)
        embed.add_field(name="> Idioma",      value=idioma,         inline=True)
        embed.add_field(name="> Categorías",  value=categorias[:50], inline=False)
        if portada: embed.set_thumbnail(url=portada)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    except asyncio.TimeoutError:
        await ctx.send("> Tiempo agotado.")
    except Exception as e:
        await ctx.send(f"> Error: `{str(e)[:100]}`")

@bot.hybrid_command(name="steam", description="Busca información de un juego en Steam")
async def cmd_steam(ctx: commands.Context, *, juego: str):
    if ctx.interaction: await ctx.defer()
    async with aiohttp.ClientSession() as session:
        async with session.get("https://steamcommunity.com/api/ISteamApps/GetAppList/v2/") as resp:
            if resp.status != 200:
                await ctx.send("> Error conectando con Steam"); return
            apps = (await resp.json()).get('applist',{}).get('apps',[])
    resultados = [app for app in apps if juego.lower() in app['name'].lower()]
    if not resultados:
        await ctx.send(f"> No se encontró: **{juego}**"); return
    app_id, nombre = resultados[0]['appid'], resultados[0]['name']
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://store.steampowered.com/api/appdetails?appids={app_id}") as resp:
            data = await resp.json()
    detalles = data.get(str(app_id), {})
    if not detalles.get('success'):
        await ctx.send(f"> Sin detalles para `{nombre}`"); return
    info         = detalles.get('data', {})
    descripcion  = info.get('short_description','Sin descripción')
    precio       = info.get('price_overview',{})
    precio_final = precio.get('final_formatted','Gratis') if precio else 'No disponible'
    plataformas  = []
    if info.get('platforms',{}).get('windows'): plataformas.append("🪟 Windows")
    if info.get('platforms',{}).get('mac'):     plataformas.append("🍎 Mac")
    if info.get('platforms',{}).get('linux'):   plataformas.append("🐧 Linux")
    generos_texto = ", ".join([g['description'] for g in info.get('genres',[])][:3]) or "N/A"
    puntaje = info.get('metacritic',{}).get('score','N/A')
    embed = discord.Embed(title=nombre, description=descripcion[:200]+"..." if len(descripcion)>200 else descripcion,
                          color=AZUL_IPOD_NUM, url=f"https://store.steampowered.com/app/{app_id}")
    embed.add_field(name="> Precio",      value=precio_final,                  inline=True)
    embed.add_field(name="> Metacritic",  value=f"{puntaje}/100" if puntaje!='N/A' else puntaje, inline=True)
    embed.add_field(name="> Géneros",     value=generos_texto,                 inline=False)
    embed.add_field(name="> Plataformas", value=", ".join(plataformas) or "N/A", inline=True)
    url_imagen = info.get('header_image','')
    if url_imagen: embed.set_thumbnail(url=url_imagen)
    embed.set_footer(text=f"ID: {app_id} | Steam Store")
    await ctx.send(embed=embed)

@bot.hybrid_command(name="nasa", description="Foto astronómica del día (NASA APOD)")
async def cmd_nasa(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    años            = list(range(1995, 2025))
    fecha_aleatoria = f"{random.choice(años)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    fecha_actual    = datetime.now().strftime("%Y-%m-%d")
    usar_actual     = random.choice([True, False])
    fecha           = fecha_actual if usar_actual else fecha_aleatoria
    tipo            = "Imagen del Día" if usar_actual else "Imagen Aleatoria (Archivo NASA)"
    url = f"https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&date={fecha}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send("> Error obteniendo imagen de NASA."); return
            data = await resp.json()
    if 'error' in data:
        await ctx.send(f"> {data.get('error',{}).get('message','Error desconocido')}"); return
    titulo      = data.get('title','Imagen del día')
    explicacion = data.get('explanation','Sin explicación')
    if len(explicacion) > 500: explicacion = explicacion[:500] + "..."
    imagen       = data.get('url','')
    fecha_nasa   = data.get('date', fecha)
    copyright_nt = data.get('copyright','NASA')
    if imagen.endswith('.mp4') or 'youtube' in imagen or 'vimeo' in imagen:
        embed = discord.Embed(title=titulo, description=f"**Video del día**\n\n{explicacion}", color=AZUL_IPOD_NUM)
        embed.add_field(name="**Ver video**", value=f"[Clic aquí]({imagen})", inline=False)
    else:
        embed = discord.Embed(title=titulo, description=explicacion, color=AZUL_IPOD_NUM, url=imagen)
        embed.set_image(url=imagen)
    embed.add_field(name="> Fecha",   value=fecha_nasa,   inline=True)
    embed.add_field(name="> Crédito", value=copyright_nt, inline=True)
    embed.add_field(name="> Tipo",    value=tipo,         inline=True)
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name} | NASA APOD")
    await ctx.send(embed=embed)

@bot.hybrid_command(name="covid", description="Datos actualizados de COVID-19")
async def cmd_covid(ctx: commands.Context, *, pais: str = "mexico"):
    if ctx.interaction: await ctx.defer()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://disease.sh/v3/covid-19/countries/{urllib.parse.quote(pais)}") as resp:
            if resp.status != 200:
                await ctx.send(f"> Sin datos para: {pais}"); return
            data = await resp.json()
    nombre      = data.get('country', pais.capitalize())
    casos       = data.get('cases', 0);       muertes    = data.get('deaths', 0)
    casos_hoy   = data.get('todayCases', 0);  muertes_hoy = data.get('todayDeaths', 0)
    recuperados = data.get('recovered', 0);   activos    = data.get('active', 0)
    criticos    = data.get('critical', 0);    pruebas    = data.get('tests', 0)
    bandera    = data.get('countryInfo',{}).get('flag','')
    tm = (muertes/casos*100) if casos>0 else 0
    tr = (recuperados/casos*100) if casos>0 else 0
    embed = discord.Embed(title=f"COVID-19: {nombre}", color=AZUL_IPOD_NUM)
    if bandera: embed.set_thumbnail(url=bandera)
    embed.add_field(name="> Casos totales",     value=f"{casos:,}",        inline=True)
    embed.add_field(name="> Casos hoy",         value=f"+{casos_hoy:,}",   inline=True)
    embed.add_field(name="> Muertes",           value=f"{muertes:,}",      inline=True)
    embed.add_field(name="> Muertes hoy",       value=f"+{muertes_hoy:,}", inline=True)
    embed.add_field(name="> Recuperados",       value=f"{recuperados:,}",  inline=True)
    embed.add_field(name="> Activos",           value=f"{activos:,}",      inline=True)
    embed.add_field(name="> Críticos",          value=f"{criticos:,}",     inline=True)
    embed.add_field(name="> Pruebas",           value=f"{pruebas:,}",      inline=True)
    embed.add_field(name="> Tasa mortalidad",   value=f"{tm:.2f}%",        inline=True)
    embed.add_field(name="> Tasa recuperación", value=f"{tr:.2f}%",        inline=True)
    embed.set_footer(text="Actualizado | disease.sh API")
    await ctx.send(embed=embed)

# =========================================================
# COMANDOS — UTILIDADES
# =========================================================

@bot.hybrid_command(name="ping", description="Latencia del bot")
async def cmd_ping(ctx: commands.Context):
    ms    = round(bot.latency * 1000)
    embed = discord.Embed(color=AZUL_IPOD_NUM)
    embed.description = f"> Pong! `{ms}ms`"
    await ctx.send(embed=embed)

@bot.hybrid_command(name="calcular", description="Calcula una operación matemática")
async def cmd_calcular(ctx: commands.Context, *, operacion: str):
    if not _CALC_ALLOWED.match(operacion):
        await ctx.send("> Solo se permiten operaciones básicas (+, -, *, /, **, %)"); return
    try:
        resultado = eval(operacion, {"__builtins__": {}}, {})
        embed = discord.Embed(color=AZUL_IPOD_NUM)
        embed.description = f"> **Operación:** {operacion}\n> **Resultado:** {resultado}"
        await ctx.send(embed=embed)
    except ZeroDivisionError:
        await ctx.send("> División entre cero")
    except:
        await ctx.send("> Operación inválida")

@bot.hybrid_command(name="qr", description="Genera un código QR")
async def cmd_qr(ctx: commands.Context, *, texto: str):
    url   = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(texto)}"
    embed = discord.Embed(title="Código QR", description=f"**Contenido:** {texto[:100]}{'...' if len(texto)>100 else ''}", color=AZUL_IPOD_NUM)
    embed.set_image(url=url)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="color", description="Muestra un color HEX o genera uno aleatorio")
async def cmd_color(ctx: commands.Context, hex_code: str = None):
    if not hex_code:
        hex_code     = ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
        es_aleatorio = True
    else:
        hex_code     = hex_code.strip().lstrip('#').upper()
        es_aleatorio = False
    if not re.match(r'^[0-9A-F]{6}$', hex_code):
        await ctx.send(f"> HEX inválido: `{hex_code}`"); return
    r, g, b              = int(hex_code[0:2],16), int(hex_code[2:4],16), int(hex_code[4:6],16)
    r_c, g_c, b_c        = 255-r, 255-g, 255-b
    hex_comp             = f"{r_c:02X}{g_c:02X}{b_c:02X}"
    img  = Image.new("RGB", (400, 200), (r, g, b))
    draw = ImageDraw.Draw(img)
    draw.text((200,  80), f"#{hex_code}",          font=fuente(24, bold=True), fill=(255,255,255), anchor="mm")
    draw.text((200, 120), f"RGB({r}, {g}, {b})",   font=fuente(16),           fill=(255,255,255), anchor="mm")
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    archivo = discord.File(buf, filename="color.png")
    embed   = discord.Embed(title="Color Aleatorio" if es_aleatorio else "Color", color=int(hex_code,16))
    embed.add_field(name="> Código HEX",    value=f"`#{hex_code}`",        inline=True)
    embed.add_field(name="> RGB",           value=f"`({r}, {g}, {b})`",    inline=True)
    embed.add_field(name="> Complementario", value=f"`#{hex_comp}`",        inline=True)
    embed.set_image(url="attachment://color.png")
    await ctx.send(embed=embed, file=archivo)

@bot.hybrid_command(name="traducir", description="Traduce texto a cualquier idioma")
async def cmd_traducir(ctx: commands.Context, idioma: str, *, texto: str):
    if ctx.interaction: await ctx.defer()
    idiomas_nombres = {
        "es":"Español","en":"Inglés","fr":"Francés","de":"Alemán","it":"Italiano",
        "pt":"Portugués","ja":"Japonés","ko":"Coreano","zh":"Chino","ru":"Ruso",
        "ar":"Árabe","hi":"Hindi","nl":"Holandés","pl":"Polaco","tr":"Turco",
        "vi":"Vietnamita","th":"Tailandés","el":"Griego","he":"Hebreo","sv":"Sueco",
        "no":"Noruego","da":"Danés","fi":"Finlandés",
    }
    idioma = idioma.lower()
    if idioma not in idiomas_nombres:
        codigos = ", ".join(list(idiomas_nombres.keys())[:15])
        await ctx.send(f"> Idioma **{idioma}** no válido. Disponibles: {codigos}..."); return
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&dj=1&q={urllib.parse.quote(texto)}&sl=auto&tl={idioma}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("> Error con el traductor."); return
                data = await resp.json()
        traduccion = "".join(s.get('trans','') for s in data.get('sentences',[]) if 'trans' in s)
        if not traduccion:
            await ctx.send("> No se pudo traducir."); return
        idioma_origen_nombre  = idiomas_nombres.get(data.get('src',''), data.get('src','').upper())
        idioma_destino_nombre = idiomas_nombres.get(idioma, idioma.upper())
        embed = discord.Embed(title="Traductor", color=AZUL_IPOD_NUM)
        embed.add_field(name=f"> Original ({idioma_origen_nombre})",    value=f"```{texto[:500]}```",      inline=False)
        embed.add_field(name=f"> Traducción ({idioma_destino_nombre})", value=f"```{traduccion[:500]}```", inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error al traducir: ```{str(e)[:100]}```")

@bot.hybrid_command(name="definir", description="Busca el significado de una palabra (en inglés)")
async def cmd_definir(ctx: commands.Context, *, palabra: str):
    if ctx.interaction: await ctx.defer()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(palabra)}") as resp:
            if resp.status != 200:
                await ctx.send(f"> No se encontró: **{palabra}**"); return
            data = await resp.json()
    if not data:
        await ctx.send(f"> Sin resultados para **{palabra}**"); return
    embed = discord.Embed(title=data[0].get('word', palabra).capitalize(), color=AZUL_IPOD_NUM)
    for significado in data[0].get('meanings', [])[:3]:
        tipo  = significado.get('partOfSpeech','Desconocido')
        defs  = significado.get('definitions', [])
        if defs:
            d = defs[0].get('definition','')
            e = defs[0].get('example','')
            texto = f"**{tipo}**\n{d[:200]}"
            if e: texto += f"\n*Ejemplo: {e[:100]}*"
            embed.add_field(name=tipo.capitalize(), value=texto[:250], inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="base64", description="Codifica o decodifica texto en base64")
async def cmd_base64(ctx: commands.Context, accion: str, *, texto: str):
    import base64
    try:
        if accion.lower() == "codificar":
            resultado = base64.b64encode(texto.encode()).decode()
            embed = discord.Embed(color=AZUL_IPOD_NUM)
            embed.add_field(name="Original", value=texto[:1000],              inline=False)
            embed.add_field(name="Base64",   value=f"`{resultado[:1000]}`",   inline=False)
        elif accion.lower() == "decodificar":
            resultado = base64.b64decode(texto).decode()
            embed = discord.Embed(color=AZUL_IPOD_NUM)
            embed.add_field(name="Base64",   value=texto[:1000],    inline=False)
            embed.add_field(name="Original", value=resultado[:1000], inline=False)
        else:
            await ctx.send("> Usa `codificar` o `decodificar`"); return
        await ctx.send(embed=embed)
    except:
        await ctx.send("> Texto inválido")

@bot.hybrid_command(name="ip", description="Información de una dirección IP")
async def cmd_ip(ctx: commands.Context, *, direccion: str):
    if ctx.interaction: await ctx.defer()
    partes = direccion.split(".")
    if len(partes) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in partes):
        await ctx.send("> Formato de IP inválido"); return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://ip-api.com/json/{direccion}?lang=es") as resp:
            if resp.status != 200:
                await ctx.send("> Error obteniendo info de la IP"); return
            data = await resp.json()
    if data.get('status') == 'fail':
        await ctx.send(f"> IP **{direccion}** no válida o no encontrada"); return
    embed = discord.Embed(title=f"IP: {direccion}", color=AZUL_IPOD_NUM)
    embed.add_field(name="> País",    value=data.get('country','Desconocido'),    inline=True)
    embed.add_field(name="> Ciudad",  value=data.get('city','Desconocida'),       inline=True)
    embed.add_field(name="> ISP",     value=data.get('isp','Desconocido'),        inline=True)
    embed.add_field(name="> Región",  value=data.get('regionName','Desconocida'), inline=True)
    embed.add_field(name="> Tipo",    value="Móvil" if data.get('mobile') else "Fijo", inline=True)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="recordar", description="Crea un recordatorio")
async def cmd_recordar(ctx: commands.Context, tiempo: str, *, mensaje: str):
    unidad = tiempo[-1].lower()
    try: cantidad = int(tiempo[:-1])
    except:
        await ctx.send("> Formato inválido. Usa: `10s`, `5m`, `2h`, `1d`"); return
    if unidad == 's':   segundos, texto_u = cantidad,         "segundo" if cantidad==1 else "segundos"
    elif unidad == 'm': segundos, texto_u = cantidad*60,    "minuto"  if cantidad==1 else "minutos"
    elif unidad == 'h': segundos, texto_u = cantidad*3600,  "hora"    if cantidad==1 else "horas"
    elif unidad == 'd': segundos, texto_u = cantidad*86400, "día"     if cantidad==1 else "días"
    else:
        await ctx.send("> Usa: s, m, h, d"); return
    if segundos > 604800 or segundos < 5:
        await ctx.send("> Entre 5 segundos y 7 días"); return
    await ctx.send(embed=discord.Embed(title="Recordatorio creado",
        description=f"Te recordaré **{mensaje}** en **{cantidad} {texto_u}**", color=AZUL_IPOD_NUM))
    await asyncio.sleep(segundos)
    await ctx.channel.send(content=ctx.author.mention,
        embed=discord.Embed(title="RECORDATORIO", description=f"> {ctx.author.mention}\n**{mensaje}**", color=AZUL_IPOD_NUM))

@bot.hybrid_command(name="google", description="Busca en Google")
async def cmd_google(ctx: commands.Context, *, query: str):
    if ctx.interaction: await ctx.defer()
    API_KEY = os.getenv("SERPER_API_KEY")
    if not API_KEY:
        await ctx.send("> `SERPER_API_KEY` no configurada"); return
    async with aiohttp.ClientSession() as session:
        async with session.post("https://google.serper.dev/search",
                                headers={"X-API-KEY": API_KEY, "Content-Type": "application/json"},
                                json={"q": query, "num": 5, "gl": "es", "hl": "es"}) as resp:
            data = await resp.json()
    resultados = data.get("organic", [])
    if not resultados:
        await ctx.send(f"> Sin resultados para: **{query}**"); return
    embed = discord.Embed(title=f"Google: {query[:50]}", color=AZUL_IPOD_NUM)
    for n, res in enumerate(resultados[:5]):
        embed.add_field(name=f"{n+1}. {res.get('title','')[:70]}",
                        value=f"> {res.get('snippet','')[:150]}\n[Leer más]({res.get('link','#')})",
                        inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="imagenes", description="Busca imágenes en Google")
async def cmd_imagenes(ctx: commands.Context, *, query: str):
    if ctx.interaction: await ctx.defer()
    API_KEY = os.getenv("SERPER_API_KEY")
    if not API_KEY:
        await ctx.send("> `SERPER_API_KEY` no configurada"); return
    async with aiohttp.ClientSession() as session:
        async with session.post("https://google.serper.dev/images",
                                headers={"X-API-KEY": API_KEY, "Content-Type": "application/json"},
                                json={"q": query, "num": 5}) as resp:
            data = await resp.json()
    imagenes = data.get("images", [])
    if not imagenes:
        await ctx.send(f"> Sin imágenes para: **{query}**"); return
    embed = discord.Embed(title=f"Imágenes: {query[:50]}", color=AZUL_IPOD_NUM)
    embed.set_image(url=imagenes[0].get('imageUrl',''))
    for n, img in enumerate(imagenes[:3]):
        embed.add_field(name=f"> Imagen {n+1}", value=f"[Ver imagen]({img.get('imageUrl','#')})", inline=True)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="lugares", description="Busca lugares en Google Maps")
async def cmd_lugares(ctx: commands.Context, *, lugar: str):
    if ctx.interaction: await ctx.defer()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://nominatim.openstreetmap.org/search",
                                   params={"q": lugar, "format": "json", "limit": "5", "addressdetails": "1"},
                                   headers={"User-Agent": "MistiBot/1.0"}) as resp:
                if resp.status != 200:
                    await ctx.send(f"> Error ({resp.status})"); return
                data = await resp.json()
        if not data:
            await ctx.send(f"> Sin resultados para: **{lugar}**"); return
        embed = discord.Embed(title=f"Lugares: {lugar}", color=AZUL_IPOD_NUM)
        for sitio in data[:5]:
            lat, lon     = sitio.get("lat",""), sitio.get("lon","")
            nombre_corto = sitio.get("display_name","Sin nombre")[:60]+"..." if len(sitio.get("display_name",""))>60 else sitio.get("display_name","Sin nombre")
            embed.add_field(name=nombre_corto,
                            value=f"> **Tipo:** {sitio.get('type','lugar').replace('_',' ').capitalize()}\n> **Coords:** `{float(lat):.4f}, {float(lon):.4f}`\n> [Google Maps](https://www.google.com/maps?q={lat},{lon})",
                            inline=False)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name} | OpenStreetMap")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"> Error: `{str(e)[:100]}`")

@bot.hybrid_command(name="noticias", description="Últimas noticias de actualidad")
async def cmd_noticias(ctx: commands.Context, *, query: str = None):
    if ctx.interaction: await ctx.defer()
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
                if len(noticias_lista) >= 5: break
                try:
                    async with session.get(feed_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status != 200: continue
                        contenido = await resp.text()
                    root  = ET.fromstring(contenido)
                    canal = root.find("channel")
                    if canal is None: continue
                    for item in canal.findall("item"):
                        if len(noticias_lista) >= 5: break
                        titulo = re.sub(r"<[^>]+>", "", item.findtext("title","Sin título").strip())
                        enlace = item.findtext("link","#").strip()
                        fecha  = item.findtext("pubDate","")
                        fuente_tag = item.find("{http://purl.org/dc/elements/1.1/}creator")
                        fuente     = fuente_tag.text if fuente_tag is not None else feed_url.split("/")[2]
                        fecha_texto = ""
                        if fecha:
                            try: fecha_texto = parsedate_to_datetime(fecha).strftime("%d/%m/%Y %H:%M")
                            except: fecha_texto = fecha[:16]
                        noticias_lista.append({"titulo": titulo, "enlace": enlace, "fuente": fuente, "fecha": fecha_texto})
                except: continue
        if not noticias_lista:
            await ctx.send(f"> Sin noticias para: **{query or 'hoy'}**"); return
        embed = discord.Embed(title=f"Noticias: {query or 'Últimas'}", color=AZUL_IPOD_NUM)
        for n in noticias_lista[:5]:
            titulo_corto = (n["titulo"][:60]+"...") if len(n["titulo"])>60 else n["titulo"]
            embed.add_field(name=titulo_corto,
                            value=f"> **{n['fuente']}** | {n['fecha']}\n> [Leer más]({n['enlace']})",
                            inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"Error noticias: {e}")
        await ctx.send("> Error al procesar las noticias.")

@bot.hybrid_command(name="clima", description="Clima actual de una ciudad")
async def cmd_clima(ctx: commands.Context, *, ciudad: str):
    if ctx.interaction: await ctx.defer()
    API_KEY = os.getenv("WEATHER_API_KEY")
    if not API_KEY:
        await ctx.send("> `WEATHER_API_KEY` no configurada."); return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.openweathermap.org/data/2.5/weather?q={urllib.parse.quote(ciudad)}&appid={API_KEY}&units=metric&lang=es") as resp:
                if resp.status == 404:
                    await ctx.send(f"> Ciudad **{ciudad}** no encontrada."); return
                if resp.status != 200:
                    await ctx.send(f"> Error ({resp.status})"); return
                datos = await resp.json()
    except Exception as e:
        await ctx.send(f"> Error de conexión: ```{str(e)}```"); return
    embed = discord.Embed(title=f"Clima en {datos['name']}, {datos['sys']['country']}", color=AZUL_IPOD_NUM)
    embed.add_field(name="> Temperatura", value=f"{datos['main']['temp']}°C",       inline=True)
    embed.add_field(name="> Sensación",   value=f"{datos['main']['feels_like']}°C", inline=True)
    embed.add_field(name="> Humedad",     value=f"{datos['main']['humidity']}%",    inline=True)
    embed.add_field(name="> Viento",      value=f"{datos['wind']['speed']} m/s",    inline=True)
    embed.add_field(name="> Descripción", value=datos['weather'][0]['description'].capitalize(), inline=False)
    embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{datos['weather'][0]['icon']}@2x.png")
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="recetas", description="Busca recetas de cocina")
async def cmd_recetas(ctx: commands.Context, *, plato: str):
    if ctx.interaction: await ctx.defer()
    API_KEY = os.getenv("SERPER_API_KEY")
    if not API_KEY:
        await ctx.send("> `SERPER_API_KEY` no configurada"); return
    async with aiohttp.ClientSession() as session:
        async with session.post("https://google.serper.dev/search",
                                headers={"X-API-KEY": API_KEY, "Content-Type": "application/json"},
                                json={"q": f"{plato} receta", "num": 5}) as resp:
            data = await resp.json()
    resultados = data.get("organic", [])
    if not resultados:
        await ctx.send(f"> Sin recetas para: **{plato}**"); return
    embed = discord.Embed(title=f"Recetas de: {plato}", color=AZUL_IPOD_NUM)
    for r in resultados[:5]:
        embed.add_field(name=f"> {r.get('title','')[:60]}",
                        value=f"{r.get('snippet','')[:120]}\n[Ver receta]({r.get('link','#')})",
                        inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="shopping", description="Busca productos para comprar")
async def cmd_shopping(ctx: commands.Context, *, producto: str):
    if ctx.interaction: await ctx.defer()
    API_KEY = os.getenv("SERPER_API_KEY")
    if not API_KEY:
        await ctx.send("> `SERPER_API_KEY` no configurada"); return
    async with aiohttp.ClientSession() as session:
        async with session.post("https://google.serper.dev/shopping",
                                headers={"X-API-KEY": API_KEY, "Content-Type": "application/json"},
                                json={"q": producto, "num": 5}) as resp:
            data = await resp.json()
    productos = data.get("shopping", [])
    if not productos:
        await ctx.send(f"> Sin productos para: **{producto}**"); return
    embed = discord.Embed(title=f"Productos: {producto}", color=AZUL_IPOD_NUM)
    for item in productos[:5]:
        embed.add_field(name=f"> {item.get('title','')[:50]}",
                        value=f"{item.get('price','N/A')} | {item.get('source','')}\n[Ver producto]({item.get('link','#')})",
                        inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="doctor", description="Diagnóstico de permisos del bot")
async def cmd_doctor(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    me  = ctx.guild.me
    cp  = ctx.channel.permissions_for(me)
    gp  = me.guild_permissions
    permisos_canal = {
        "Ver Canal":              cp.view_channel,      "Enviar Mensajes":    cp.send_messages,
        "Crear Embeds":           cp.embed_links,       "Adjuntar Archivos":  cp.attach_files,
        "Emojis Externos":        cp.use_external_emojis, "Añadir Reacciones": cp.add_reactions,
        "Leer Historial":         cp.read_message_history,
    }
    permisos_servidor = {
        "Administrador":          gp.administrator,   "Gestionar Mensajes": gp.manage_messages,
        "Gestionar Canales":      gp.manage_channels, "Gestionar Roles":    gp.manage_roles,
        "Expulsar Miembros":      gp.kick_members,    "Banear Miembros":    gp.ban_members,
        "Silenciar Miembros":     gp.mute_members,
    }
    def fmt(d):
        return "\n".join(f"{'<:Check:1504584129302499399>' if v else '<:fail:1504584129302499399>'} **{k}**" for k, v in d.items())
    embed = discord.Embed(title="Diagnóstico del Bot", description="Estado de permisos", color=AZUL_IPOD_NUM)
    embed.add_field(name="Canal",    value=fmt(permisos_canal),    inline=False)
    embed.add_field(name="Servidor", value=fmt(permisos_servidor), inline=False)
    errores = [k for k, v in permisos_canal.items() if not v]
    if gp.administrator:   diagnostico = "> Tiene permiso de **Administrador**. Sin restricciones."
    elif not errores:      diagnostico = "> ¡Excelente! Todos los permisos fundamentales activos."
    else:                  diagnostico = f"> Faltan permisos: **{', '.join(errores[:2])}**"
    embed.add_field(name="Conclusión", value=diagnostico, inline=False)
    embed.set_footer(text=f"Latencia: {round(bot.latency * 1000)}ms", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="primermensaje", description="Muestra el primer mensaje del canal")
async def cmd_primermensaje(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    try:
        primer_msg = None
        async for message in ctx.channel.history(limit=1, oldest_first=True):
            primer_msg = message
        if not primer_msg:
            await ctx.send("> No se encontró el primer mensaje"); return
        autor     = primer_msg.author
        contenido = primer_msg.content if primer_msg.content else "*[Sin texto]*"
        if len(contenido) > 400: contenido = contenido[:400] + "..."
        embed = discord.Embed(title="Primer mensaje del canal",
                              description=f"**Canal:** {ctx.channel.mention}\n**Autor:** {autor.mention}\n**Fecha:** {primer_msg.created_at.strftime('%d/%m/%Y %H:%M:%S')}",
                              color=AZUL_IPOD_NUM)
        embed.add_field(name="> Contenido", value=f"```{contenido}```", inline=False)
        embed.add_field(name="> Enlace",    value=f"[Ir al mensaje]({primer_msg.jump_url})", inline=False)
        if autor.avatar: embed.set_thumbnail(url=autor.display_avatar.url)
        embed.set_footer(text=f"ID: {primer_msg.id}")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("> Sin permisos para leer el historial")
    except Exception as e:
        await ctx.send(f"> Error: `{str(e)[:100]}`")

# =========================================================
# COMANDOS — JUEGOS
# =========================================================

@bot.hybrid_command(name="ship", description="Compatibilidad entre dos usuarios")
async def cmd_ship(ctx: commands.Context, usuario1: discord.Member, usuario2: discord.Member):
    if ctx.interaction: await ctx.defer()
    seed = (usuario1.id + usuario2.id) % 101
    random.seed(seed); pct = random.randint(0, 100); random.seed()
    await ctx.send(file=await generar_ship(usuario1, usuario2, pct))

@bot.hybrid_command(name="moneda", description="Tira una moneda")
async def cmd_moneda(ctx: commands.Context):
    resultado = random.choice(["Cara", "Cruz"])
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> Resultado: **{resultado}**"))

@bot.hybrid_command(name="dado", description="Tira un dado de N caras")
async def cmd_dado(ctx: commands.Context, caras: int = 6):
    resultado = random.randint(1, max(caras, 2))
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> Dado de {caras} caras: **{resultado}**"))

@bot.hybrid_command(name="8ball", description="Pregúntale algo al futuro")
async def cmd_8ball(ctx: commands.Context, *, pregunta: str):
    respuestas = ["Si","No","Tal vez","Definitivamente si","Ni lo sueñes","Claro que si",
                  "Las estrellas dicen que no","Pregunta mas tarde","No cuentes con ello"]
    await ctx.send(embed=discord.Embed(title="Pregunta Mágica",
        description=f"> **Pregunta:** {pregunta}\n> **Respuesta:** {random.choice(respuestas)}",
        color=AZUL_IPOD_NUM))

@bot.hybrid_command(name="trivia", description="Juega una pregunta de trivia")
async def cmd_trivia(ctx: commands.Context):
    PREGUNTAS = [
        {"pregunta": "¿Cuál es la capital de Francia?",               "respuestas": ["Paris","Londres","Berlin"],           "correcta": 0},
        {"pregunta": "¿Cuál es el planeta más grande?",               "respuestas": ["Jupiter","Saturno","Tierra"],         "correcta": 0},
        {"pregunta": "¿En qué año terminó la 2da Guerra Mundial?",    "respuestas": ["1943","1944","1945"],                  "correcta": 2},
        {"pregunta": "¿Cuál es el elemento químico con símbolo Au?",  "respuestas": ["Plata","Oro","Aluminio"],             "correcta": 1},
        {"pregunta": "¿Quién escribió Don Quijote?",                  "respuestas": ["Borges","Cervantes","Garcia Marquez"], "correcta": 1},
    ]
    pd = random.choice(PREGUNTAS)

    class TriviaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.respondio = False
            for n, r in enumerate(pd['respuestas']):
                btn          = discord.ui.Button(label=r, style=discord.ButtonStyle.primary, custom_id=f"trivia_{n}")
                btn.callback = self.responder
                self.add_item(btn)
        async def responder(self, interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Esta no es tu trivia", ephemeral=True); return
            if self.respondio: return
            self.respondio = True
            num      = int(interaction.data['custom_id'].split('_')[1])
            correcta = num == pd['correcta']
            gid, uid = str(interaction.guild.id), str(ctx.author.id)
            if gid not in puntuaciones_trivia: puntuaciones_trivia[gid] = {}
            if uid not in puntuaciones_trivia[gid]: puntuaciones_trivia[gid][uid] = 0
            if correcta: puntuaciones_trivia[gid][uid] += 10
            embed_r = discord.Embed(color=AZUL_IPOD_NUM)
            embed_r.description = "> ¡Correcto! +10 puntos" if correcta else f"> Incorrecto. Era: **{pd['respuestas'][pd['correcta']]}**"
            embed_r.add_field(name="Puntos Totales", value=puntuaciones_trivia[gid][uid])
            await interaction.response.edit_message(embed=embed_r, view=None)

    embed = discord.Embed(color=AZUL_IPOD_NUM, title="Trivia", description=pd['pregunta'])
    await ctx.send(embed=embed, view=TriviaView())

@bot.hybrid_command(name="puntaje", description="Ver tu puntuación de trivia")
async def cmd_puntaje(ctx: commands.Context):
    puntos = puntuaciones_trivia.get(str(ctx.guild.id), {}).get(str(ctx.author.id), 0)
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, title="Tu Puntuación",
        description=f"> Puntos de trivia: **{puntos}**"))

@bot.hybrid_command(name="ahorcado", description="Juega al ahorcado")
async def cmd_ahorcado(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    palabras          = ["frutas","mantequilla","computadora","celular","pais","diva","musica","discord","python","servidor"]
    palabra_secreta   = random.choice(palabras).upper()
    letras_adivinadas = set()
    intentos          = 6
    def mostrar_palabra(): return ' '.join([l if l in letras_adivinadas else '_' for l in palabra_secreta])
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, title="Ahorcado",
        description=f"> `{mostrar_palabra()}`\n> Intentos: **{intentos}**"))
    def check(m): return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1
    while intentos > 0 and set(palabra_secreta) != letras_adivinadas:
        try:
            msg   = await bot.wait_for('message', check=check, timeout=60)
            letra = msg.content.upper()
            if letra in letras_adivinadas:
                await ctx.channel.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> Ya adivinaste esa letra")); continue
            letras_adivinadas.add(letra)
            if letra not in palabra_secreta: intentos -= 1
            await ctx.channel.send(embed=discord.Embed(color=AZUL_IPOD_NUM,
                description=f"> `{mostrar_palabra()}`\n> Intentos: **{intentos}**"))
        except asyncio.TimeoutError: break
    if set(palabra_secreta) == letras_adivinadas:
        await ctx.channel.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> ¡GANASTE! La palabra era: **{palabra_secreta}**"))
    else:
        await ctx.channel.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> PERDISTE. La palabra era: **{palabra_secreta}**"))

@bot.hybrid_command(name="ppt", description="Piedra, papel o tijera")
async def cmd_ppt(ctx: commands.Context):
    opciones = ["Piedra","Papel","Tijera"]
    async def ppt_seleccionar(interaction: discord.Interaction, opcion_usuario: str):
        opcion_bot = random.choice(opciones)
        if opcion_usuario == opcion_bot: resultado = "EMPATE"
        elif (opcion_usuario=="Piedra" and opcion_bot=="Tijera") or \
             (opcion_usuario=="Papel"  and opcion_bot=="Piedra") or \
             (opcion_usuario=="Tijera" and opcion_bot=="Papel"):  resultado = "GANASTE"
        else: resultado = "PERDISTE"
        embed = discord.Embed(color=AZUL_IPOD_NUM)
        embed.description = f"> Tu: **{opcion_usuario}**\n> Bot: **{opcion_bot}**\n> **{resultado}**"
        await interaction.response.send_message(embed=embed, ephemeral=True)
    view = discord.ui.View()
    for opcion in opciones:
        btn = discord.ui.Button(label=opcion, style=discord.ButtonStyle.primary)
        btn.callback = lambda interaction, op=opcion: ppt_seleccionar(interaction, op)
        view.add_item(btn)
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, title="PPT", description="> Elige tu opcion"), view=view)

@bot.hybrid_command(name="adivina", description="Adivina un número del 1 al 100")
async def cmd_adivina(ctx: commands.Context):
    if ctx.interaction: await ctx.defer()
    numero_secreto = random.randint(1, 100)
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, title="Adivina el Número",
        description="> Piensa un número entre 1 y 100. Tienes 10 intentos"))
    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    for intento in range(10):
        try:
            msg = await bot.wait_for('message', check=check, timeout=60)
            if not msg.content.isdigit(): continue
            numero = int(msg.content)
            if numero == numero_secreto:
                await ctx.channel.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> ¡Correcto! El número era **{numero_secreto}**\n> Intentos: **{intento+1}**")); return
            elif numero < numero_secreto: msg_text = f"> El número es **mayor** ({intento+1}/10)"
            else:                         msg_text = f"> El número es **menor** ({intento+1}/10)"
            await ctx.channel.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description=msg_text))
        except asyncio.TimeoutError: break
    await ctx.channel.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description=f"> ¡Se acabaron los intentos! Era **{numero_secreto}**"))

@bot.hybrid_command(name="acertijo", description="Resuelve un acertijo")
async def cmd_acertijo(ctx: commands.Context):
    acertijos = [
        {"pregunta": "Blanco por dentro, verde por fuera. Si quieres que te lo diga, espera.",  "respuesta": "pera"},
        {"pregunta": "Tiene dientes pero no come, tiene cabeza pero no es hombre.",             "respuesta": "ajo"},
        {"pregunta": "¿Qué cosa es que cuanto más le quitas, más grande se hace?",             "respuesta": "agujero"},
        {"pregunta": "Vuelo sin alas, lloro sin ojos. ¿Quién soy?",                            "respuesta": "nube"},
        {"pregunta": "Siempre en la boca pero nunca se come.",                                  "respuesta": "sonrisa"},
    ]
    a = random.choice(acertijos)
    embed = discord.Embed(title="Acertijo", description=f"**{a['pregunta']}**\n\n*Responde con: `>respuesta [tu respuesta]`*", color=AZUL_IPOD_NUM)
    await ctx.send(embed=embed)
    def check(m): return m.author == ctx.author and m.content.lower().startswith(">respuesta")
    try:
        msg       = await bot.wait_for("message", timeout=30.0, check=check)
        respuesta = msg.content.lower().replace(">respuesta","").strip()
        if respuesta == a["respuesta"]:
            data = get_user_eco(ctx.guild.id, ctx.author.id)
            recompensa = random.randint(50, 150)
            data["coins"] += recompensa
            guardar_economia()
            await msg.reply(f"> **¡Correcto!** Ganaste **${recompensa}**")
        else:
            await msg.reply(f"> **Incorrecto.** Era: **{a['respuesta']}**")
    except asyncio.TimeoutError:
        await ctx.channel.send(f"> Tiempo agotado. Era: **{a['respuesta']}**")

@bot.hybrid_command(name="gayrate", description="Calcula el nivel de gay (broma)")
async def cmd_gayrate(ctx: commands.Context, usuario: discord.Member = None):
    usuario    = usuario or ctx.author
    porcentaje = (usuario.id % 101)
    barra      = "█" * (porcentaje // 10) + "░" * (10 - (porcentaje // 10))
    if porcentaje >= 80:   texto = "> FOLLO CON UN CHICO"
    elif porcentaje >= 50: texto = "> Un poco... bastante"
    elif porcentaje >= 20: texto = "> Normal, nada del otro mundo"
    else:                  texto = "> Hetero nivel Dios"
    embed = discord.Embed(title=f"Nivel de gay de {usuario.display_name}", color=AZUL_IPOD_NUM)
    embed.add_field(name="> Porcentaje", value=f"```{barra} {porcentaje}%```", inline=False)
    embed.add_field(name="> Veredicto",  value=texto, inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="horoscopo", description="Horóscopo del día")
async def cmd_horoscopo(ctx: commands.Context, *, signo: str):
    signos_validos = ["aries","tauro","geminis","cancer","leo","virgo","libra","escorpio","sagitario","capricornio","acuario","piscis"]
    if signo.lower() not in signos_validos:
        await ctx.send(f"> Signo inválido. Válidos: {', '.join(signos_validos)}"); return
    mensajes = ["Hoy es un buen dia para tomar decisiones importantes.",
                "El universo tiene planes positivos para ti.",
                "Evita conflictos innecesarios.",
                "Una oportunidad inesperada llegara a tu vida.",
                "La suerte esta de tu lado."]
    await ctx.send(embed=discord.Embed(title=f"Horóscopo de {signo.capitalize()}",
        description=f"> {random.choice(mensajes)}", color=AZUL_IPOD_NUM))

@bot.hybrid_command(name="logro", description="Genera una tarjeta de logro para un usuario")
async def cmd_logro(ctx: commands.Context, usuario: discord.Member, titulo: str, *, descripcion: str = "Ha completado un gran desafío"):
    if ctx.interaction: await ctx.defer()
    await ctx.send(file=await generar_logro(usuario, titulo, descripcion))

@bot.hybrid_command(name="ipod", description="Genera un reproductor iPod Classic")
async def cmd_ipod(ctx: commands.Context, cancion: str, artista: str, duracion: str = "3:45", progreso: int = 45):
    if ctx.interaction: await ctx.defer()
    W, H = 340, 500
    PANTALLA_FONDO = (173, 232, 244)
    PANTALLA_TEXTO = (3, 4, 94)
    img  = Image.new("RGBA", (W, H), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(10,10),(W-10,H-10)], radius=30, fill=AZUL_IPOD)
    draw.rounded_rectangle([(10,10),(W-10,H-10)], radius=30, outline=BLANCO, width=2)
    draw.rounded_rectangle([(30,30),(W-30,210)],  radius=10, fill=PANTALLA_FONDO)
    draw.rounded_rectangle([(30,30),(W-30,210)],  radius=10, outline=(100,200,255), width=2)
    draw.text((45, 45), "Ahora Sonando", font=fuente(12, bold=True), fill=(10,50,120))
    draw.text((45, 75),  (cancion[:20]+"..." if len(cancion)>20 else cancion), font=fuente(18, bold=True), fill=PANTALLA_TEXTO)
    draw.text((45, 105), (artista[:24]+"..." if len(artista)>24 else artista), font=fuente(13),            fill=PANTALLA_TEXTO)
    draw.rounded_rectangle([(45,140),(W-45,148)], radius=4, fill=(210,210,210))
    progreso_px = 45 + int((W-90) * (max(0,min(progreso,100)) / 100))
    draw.rounded_rectangle([(45,140),(progreso_px,148)], radius=4, fill=AZUL_IPOD)
    draw.text((45, 160),     "0:00",   font=fuente(11), fill=PANTALLA_TEXTO)
    draw.text((W-45, 160),   duracion, font=fuente(11), fill=PANTALLA_TEXTO, anchor="ra")
    cx, cy, r_rueda = W//2, 350, 90
    draw.ellipse([(cx-r_rueda,cy-r_rueda),(cx+r_rueda,cy+r_rueda)], fill=(240,240,240))
    draw.ellipse([(cx-r_rueda,cy-r_rueda),(cx+r_rueda,cy+r_rueda)], outline=(200,200,200), width=3)
    draw.ellipse([(cx-30,cy-30),(cx+30,cy+30)], fill=(210,210,210))
    draw.text((cx,cy-75), "MENU", font=fuente(12, bold=True), fill=(120,120,120), anchor="mm")
    draw.text((cx,cy+70), "▶||",  font=fuente(12, bold=True), fill=(120,120,120), anchor="mm")
    draw.text((cx-65,cy), "|◀◀",  font=fuente(11, bold=True), fill=(120,120,120), anchor="mm")
    draw.text((cx+65,cy), "▶▶|",  font=fuente(11, bold=True), fill=(120,120,120), anchor="mm")
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    await ctx.send(file=discord.File(buf, filename="ipod.png"))

# =========================================================
# COMANDOS — IA
# =========================================================

@bot.hybrid_command(name="ask", description="Habla con Misti")
async def cmd_ask(ctx: commands.Context, *, texto: str):
    if ctx.interaction: await ctx.defer()
    nombre_servidor = ctx.guild.name if ctx.guild else "DM"
    if any(p in texto.lower() for p in PALABRAS_IMAGEN):
        img_data, prompt, seed = await generar_imagen_ia(texto)
        if img_data:
            archivo = discord.File(io.BytesIO(img_data), filename="misti_art.png")
            embed   = discord.Embed(title="Imagen generada", description=f"> **Prompt:** {prompt[:200]}", color=AZUL_IPOD_NUM)
            embed.set_image(url="attachment://misti_art.png")
            if seed: embed.set_footer(text=f"Seed: {seed}")
            await ctx.send(embed=embed, file=archivo)
        else:
            await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> No pude generar la imagen, intenta con otro prompt."))
        return
    agregar_memoria(ctx.author.id, "user", texto)
    respuesta = await generar_respuesta_groq(ctx.author.id, texto, ctx.author.display_name, nombre_servidor)
    agregar_memoria(ctx.author.id, "assistant", respuesta)
    embed     = discord.Embed(color=AZUL_IPOD_NUM)
    user_text = texto[:500]+"..." if len(texto)>500 else texto
    embed.add_field(name=f"**{ctx.author.display_name}**", value=f"> {user_text}", inline=False)
    bot_text  = respuesta[:500]+"..." if len(respuesta)>500 else respuesta
    embed.add_field(name="**Misti**", value=f"> {bot_text}", inline=False)
    await ctx.send(embed=embed, view=RegenerarButton(ctx.author.id, texto))

@bot.hybrid_command(name="forget", description="Borra tu historial de conversación con Misti")
async def cmd_forget(ctx: commands.Context):
    limpiar_memoria(ctx.author.id)
    await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> Misti ya no recuerda nada de ti."))

@bot.hybrid_command(name="imagen", description="Genera una imagen con IA")
async def cmd_imagen(ctx: commands.Context, *, prompt: str):
    if ctx.interaction: await ctx.defer()
    img_data, prompt_usado, seed = await generar_imagen_ia(prompt)
    if img_data:
        archivo = discord.File(io.BytesIO(img_data), filename="misti_art.png")
        embed   = discord.Embed(title="Imagen generada", description=f"> **Prompt:** {prompt_usado[:200]}", color=AZUL_IPOD_NUM)
        embed.set_image(url="attachment://misti_art.png")
        if seed: embed.set_footer(text=f"Seed: {seed}")
        await ctx.send(embed=embed, file=archivo)
    else:
        await ctx.send(embed=discord.Embed(color=AZUL_IPOD_NUM, description="> No pude generar la imagen, intenta con otro prompt."))

# =========================================================
# COMANDOS — ANONIMOS
# =========================================================

@bot.hybrid_command(name="anonimo", description="Envía un mensaje anónimo")
async def cmd_anonimo(ctx: commands.Context):
    gid = str(ctx.guild.id)
    if gid not in anon_config:
        await ctx.send("> Los mensajes anónimos no están configurados en este servidor."); return
    canal = ctx.guild.get_channel(anon_config[gid]["canal_id"])
    if not canal:
        await ctx.send("> El canal configurado no existe."); return
    if ctx.interaction:
        await ctx.interaction.response.send_modal(ModalAnonimo(canal))
    else:
        await ctx.send("> Este comando solo funciona como slash command `/anonimo`.")

# =========================================================
# EVENTOS
# =========================================================

@bot.listen("on_message")
async def dar_xp(message):
    if message.author.bot or not message.guild: return
    uid   = message.author.id
    ahora = time.time()
    if ahora - xp_cooldown.get(uid, 0) < 120: return
    xp_cooldown[uid] = ahora
    data             = get_xp(message.guild.id, uid)
    data["xp"]      += random.randint(10, 20)
    xp_needed        = xp_para_nivel(data["level"])
    if data["xp"] >= xp_needed:
        data["xp"]    -= xp_needed
        data["level"] += 1
        guardar_xp()
        canal_id = nivel_canal.get(message.guild.id)
        canal    = message.guild.get_channel(canal_id) if canal_id else message.channel
        try:
            await canal.send(content=message.author.mention,
                             file=await generar_nivel(message.author, data["level"], data["xp"], xp_para_nivel(data["level"])))
        except Exception as e:
            print(f"Error nivel: {e}")

@bot.event
async def on_member_join(member):
    if member.bot: return
    cfg = welc_config.get(member.guild.id)
    if not cfg: return
    canal = member.guild.get_channel(cfg["canal"])
    if not canal: return
    embed = discord.Embed(
        title=parse_text(cfg.get("titulo") or f"Bienvenido {member.name}", member),
        description=parse_text(cfg.get("desc") or "", member),
        color=cfg.get("color", AZUL_IPOD_NUM))
    autor_n, autor_i = cfg.get("autor", (None, None))
    if autor_n: embed.set_author(name=parse_text(autor_n, member), icon_url=parse_text(autor_i or "", member) or None)
    if cfg.get("imagen"): embed.set_image(url=parse_text(cfg["imagen"], member))
    footer_t, footer_i = cfg.get("footer", (None, None))
    if footer_t: embed.set_footer(text=parse_text(footer_t, member), icon_url=parse_text(footer_i or "", member) or None)
    await canal.send(embed=embed)

@bot.event
async def on_member_remove(member):
    if member.bot: return
    cfg = bye_config.get(member.guild.id)
    if not cfg: return
    canal = member.guild.get_channel(cfg["canal"])
    if not canal: return
    embed = discord.Embed(
        title=parse_text(cfg.get("titulo") or f"Adios {member.name}", member),
        description=parse_text(cfg.get("desc") or "", member),
        color=cfg.get("color", AZUL_IPOD_NUM))
    autor_n, autor_i = cfg.get("autor", (None, None))
    if autor_n: embed.set_author(name=parse_text(autor_n, member), icon_url=parse_text(autor_i or "", member) or None)
    if cfg.get("imagen"): embed.set_image(url=parse_text(cfg["imagen"], member))
    footer_t, footer_i = cfg.get("footer", (None, None))
    if footer_t: embed.set_footer(text=parse_text(footer_t, member), icon_url=parse_text(footer_i or "", member) or None)
    await canal.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot: return

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

    # SISTEMA DE CLAVES
    if message.guild:
        gid = str(message.guild.id)
        uid = str(message.author.id)
        if gid in claves_data and uid in claves_data[gid]:
            mensaje_lower = message.content.lower()
            for clave, respuesta in claves_data[gid][uid].items():
                if mensaje_lower == clave:
                    await message.reply(respuesta, mention_author=False); break

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
        mensaje_limpio = message.content.replace(f"<@{bot.user.id}>","").replace(f"<@!{bot.user.id}>","").strip()
        if not mensaje_limpio:
            await message.reply("> Mencioname con un mensaje para que te responda.", mention_author=False)
        else:
            await responder_ask(message, message.author, mensaje_limpio, es_reply=True)
        await bot.process_commands(message)
        return

    # REPLY AL BOT
    if message.reference:
        try:
            replied = await message.channel.fetch_message(message.reference.message_id)
            if replied.author.id == bot.user.id:
                await responder_ask(message, message.author, message.content, es_reply=True)
                await bot.process_commands(message)
                return
        except: pass

    await bot.process_commands(message)

# ----------- Seccion 2 ------------------

intents = discord.Intents.default()
intents.message_content = True

# Diccionario para el estado del autosay
autosay_users = {}

@bot.event
async def on_ready():
    await bot.tree.sync() # Sincroniza los comandos híbridos
    print(f"Bot listo como {bot.user}")

# --- COMANDO SAY HÍBRIDO ---
@bot.hybrid_command(name="say", description="El bot repite lo que digas")
async def say(ctx, *, mensaje: str):
    await ctx.send(mensaje)
    # En comandos híbridos, ctx.message puede ser None si se usa como slash, 
    # por eso verificamos antes de borrar
    if ctx.message:
        await ctx.message.delete()

# --- COMANDO AUTOSAY HÍBRIDO ---
@bot.hybrid_command(name="autosay", description="Activa/desactiva el modo espejo")
async def autosay(ctx):
    user_id = ctx.author.id
    status = not autosay_users.get(user_id, False)
    autosay_users[user_id] = status
    await ctx.send(f"Auto-say: {'Activado' if status else 'Desactivado'}")

# --- LÓGICA DE EVENTO PARA EL ESPEJO ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Comando de desactivación manual
    if message.content == ">mt sayoff":
        autosay_users[message.author.id] = False
        await message.channel.send("Auto-say desactivado.")
        return

    # Lógica de espejo
    if autosay_users.get(message.author.id, False):
        if not message.content.startswith(">"):
            await message.channel.send(message.content)

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
