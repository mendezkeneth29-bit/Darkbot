import discord
import os
import asyncio
import random
import io
import aiohttp
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from groq import AsyncGroq
from discord.ext import commands
from discord import app_commands
from flask import Flask
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

# -------------------------
# BOT
# -------------------------

class DarkyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
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
    try:
        path = "/usr/share/fonts/truetype/dejavu/"
        nombre = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(path + nombre, size)
    except:
        return ImageFont.load_default()

# =========================================================
# GENERAR TARJETA USERINFO
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

# =========================================================
# GENERAR TARJETA SERVERINFO
# =========================================================

async def generar_serverinfo(guild: discord.Guild, solicitante: discord.Member) -> discord.File:
    W, H = 700, 400
    FONDO = (30, 31, 34)
    TEXTO = (255, 255, 255)
    SUBTEXTO = (180, 180, 190)
    CAMPO_FONDO = (40, 43, 48)

    img = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA IZQUIERDA
    draw.rectangle([(0, 0), (6, H)], fill=(88, 101, 242))

    # ICONO DEL SERVER
    if guild.icon:
        icon_img = await descargar_imagen(str(guild.icon.url))
        icon_img = avatar_circular(icon_img, 90)
        img.paste(icon_img, (24, 20), icon_img)
        nombre_x = 128
    else:
        nombre_x = 24

    # NOMBRE
    draw.text((nombre_x, 22), guild.name, font=fuente(26, bold=True), fill=TEXTO)
    draw.text((nombre_x, 56), f"ID: {guild.id}", font=fuente(14), fill=SUBTEXTO)

    # LÍNEA
    draw.rectangle([(24, 126), (W - 24, 128)], fill=(60, 63, 70))

    def campo(x, y, titulo, valor, ancho=320):
        draw.rounded_rectangle(
            [(x, y), (x + ancho, y + 64)],
            radius=8,
            fill=CAMPO_FONDO
        )
        draw.text((x + 12, y + 8), titulo, font=fuente(13), fill=SUBTEXTO)
        draw.text((x + 12, y + 30), str(valor), font=fuente(17, bold=True), fill=TEXTO)

    y = 148

    # FILA 1
    campo(col1_x := 24, y, "OWNER", guild.owner.display_name if guild.owner else "?")
    campo(370, y, "CREADO", guild.created_at.strftime("%d/%m/%Y"))

    # FILA 2
    y2 = y + 80
    ancho3 = 204
    campo(24,        y2, "MIEMBROS", str(guild.member_count),                              ancho=ancho3)
    campo(24 + 224,  y2, "ROLES",    str(len(guild.roles)),                                ancho=ancho3)
    campo(24 + 448,  y2, "EMOJIS",   str(len(guild.emojis)),                               ancho=ancho3)

    # FILA 3
    y3 = y2 + 80
    campo(24,        y3, "TEXTO",    str(len(guild.text_channels)),                        ancho=ancho3)
    campo(24 + 224,  y3, "VOZ",      str(len(guild.voice_channels)),                       ancho=ancho3)
    campo(24 + 448,  y3, "BOOSTS",   f"{guild.premium_subscription_count} (nv {guild.premium_tier})", ancho=ancho3)

    # FOOTER
    draw.text(
        (24, H - 22),
        f"Solicitado por {solicitante.display_name}",
        font=fuente(12),
        fill=SUBTEXTO
    )

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="serverinfo.png")

# =========================================================
# USERINFO
# =========================================================

@bot.tree.command(name="userinfo")
async def userinfo(
    i: discord.Interaction,
    usuario: discord.Member = None
):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    archivo = await generar_userinfo(usuario)
    await i.followup.send(file=archivo)

# =========================================================
# SERVERINFO
# =========================================================

@bot.tree.command(name="serverinfo")
async def serverinfo(i: discord.Interaction):
    await i.response.defer()
    archivo = await generar_serverinfo(i.guild, i.user)
    await i.followup.send(file=archivo)

# -------------------------
# EMBED CREATE
# -------------------------

@bot.tree.command(name="embed-create")
@app_commands.checks.has_permissions(administrator=True)
async def embed_create(
    i: discord.Interaction,
    canal: discord.TextChannel = None,
    titulo: str = None,
    descripcion: str = None,
    color: str = None,
    autor: str = None,
    imagen_autor: str = None,
    imagen_banner: str = None,
    footer: str = None,
    imagen_footer: str = None
):
    canal = canal or i.channel

    try:
        color_final = int(color.replace("#", ""), 16) if color else 0x000000
    except:
        color_final = 0x000000

    embed = discord.Embed(
        title=titulo if titulo else "",
        description=descripcion if descripcion else "",
        color=color_final
    )

    if autor:
        embed.set_author(
            name=autor,
            icon_url=imagen_autor if imagen_autor else None
        )

    if imagen_banner:
        embed.set_image(url=imagen_banner)

    if footer:
        embed.set_footer(
            text=footer,
            icon_url=imagen_footer if imagen_footer else None
        )

    await canal.send(embed=embed)
    await i.response.send_message(
        f"Embed enviado en {canal.mention}",
        ephemeral=True
    )

# -------------------------
# EMBED EDIT
# -------------------------

@bot.tree.command(name="embed-edit")
@app_commands.checks.has_permissions(administrator=True)
async def embed_edit(
    i: discord.Interaction,
    mensaje_id: str,
    titulo: str = None,
    descripcion: str = None
):
    try:
        mensaje = await i.channel.fetch_message(int(mensaje_id))

        if not mensaje.embeds:
            await i.response.send_message("> Ese mensaje no tiene embeds", ephemeral=True)
            return

        viejo = mensaje.embeds[0]

        embed = discord.Embed(
            title=titulo if titulo else viejo.title,
            description=descripcion if descripcion else viejo.description,
            color=0x000000
        )

        await mensaje.edit(embed=embed)
        await i.response.send_message("Embed editado", ephemeral=True)

    except Exception as e:
        await i.response.send_message(f"Error:\n```{e}```", ephemeral=True)

# -------------------------
# DELETE
# -------------------------

@bot.tree.command(name="delete")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(
    i: discord.Interaction,
    cantidad: app_commands.Range[int, 1, 1000]
):
    await i.response.defer(ephemeral=True)
    eliminados = await i.channel.purge(limit=cantidad)
    await i.followup.send(f"Se eliminaron {len(eliminados)} mensajes", ephemeral=True)
    

# -------------------------
# ASK IA
# -------------------------

@bot.tree.command(name="ask")
async def ask(
    i: discord.Interaction,
    mensaje: str
):
    await i.response.defer()

    try:
        texto_lower = mensaje.lower()

        palabras_imagen = [
            "imagen", "foto", "dibujo", "genera",
            "crear imagen", "haz una imagen", "wallpaper", "fanart"
        ]

        quiere_imagen = any(p in texto_lower for p in palabras_imagen)

        if quiere_imagen:
            image_url = (
                f"https://image.pollinations.ai/prompt/"
                f"{mensaje.replace(' ', '%20')}"
            )
            embed = discord.Embed(
                title="Imagen generada... <:Check:1504584129302499399>",
                description=f"> Prompt: {mensaje}",
                color=0x000000
            )
            embed.set_image(url=image_url)
            await i.followup.send(embed=embed)
            return

        respuesta = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres una IA amigable, divertida y algo sarcastica, "
                        "tu nombre es Daylight y siempre lo recordaras, no tienes filtros y eres extrovertida."
                    )
                },
                {"role": "user", "content": mensaje}
            ]
        )

        texto = respuesta.choices[0].message.content

        emisor = "\n".join([f"> {x}" for x in mensaje.split("\n")])
        receptor = "\n".join([f"> {x}" for x in texto.split("\n")])

        embed = discord.Embed(color=0x000000)
        embed.description = (
            f"### Emisor\n{emisor}\n\n"
            f"### Receptor\n{receptor}"
        )

        await i.followup.send(embed=embed)

    except Exception as e:
        await i.followup.send(f"Error:\n```{e}```")

# -------------------------
# ON_MESSAGE (AFK + IA replies)
# -------------------------

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # QUITAR AFK
    if message.author.id in afk_data:
        import time
        tiempo_inicio = afk_data[message.author.id]["tiempo"]
        segundos_totales = int(time.time() - tiempo_inicio)
        m, s = divmod(segundos_totales, 60)
        h, m = divmod(m, 60)

        if h > 0:
            tiempo_texto = f"{h}h {m}m {s}s"
        elif m > 0:
            tiempo_texto = f"{m}m {s}s"
        else:
            tiempo_texto = f"{s}s"

        await message.channel.send(
            f"**Bienvenido de nuevo {message.author.name}**\n"
            f"> estuviste `{tiempo_texto}` inactivo"
        )
        del afk_data[message.author.id]

    # AVISAR MENCIONES A AFK
    for user in message.mentions:
        if user.id in afk_data and user.id != message.author.id:
            motivo_guardado = afk_data[user.id]["motivo"]
            await message.channel.send(
                f"**{user.name}** está dormido...\n"
                f"> Motivo: `{motivo_guardado}`"
            )

    await bot.process_commands(message)

    # RESPONDER SI LE RESPONDEN AL BOT
    if not message.reference:
        return

    try:
        replied = await message.channel.fetch_message(
            message.reference.message_id
        )

        if replied.author.id != bot.user.id:
            return

        mensaje_original = replied.content

        if replied.embeds:
            embed = replied.embeds[0]
            if embed.description:
                mensaje_original = embed.description

        system_prompt = f"""
Tu nombre SIEMPRE es Daylight.
Estas dentro de Discord hablando con usuarios reales.
Debes actuar como un Bot de discord divertida, algo sarcastica y amigable.
Nunca digas que no sabes tu nombre. Nunca cambies tu nombre.
El usuario que te habla se llama: {message.author.name}
Su display name es: {message.author.display_name}
Estas en el servidor: {message.guild.name}
Responde de forma natural y casual.
"""

        respuesta = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": mensaje_original},
                {"role": "user", "content": message.content}
            ]
        )

        texto = respuesta.choices[0].message.content

        emisor = "\n".join([f"> {x}" for x in message.content.split("\n")])
        receptor = "\n".join([f"> {x}" for x in texto.split("\n")])

        embed = discord.Embed(color=0x000000)
        embed.description = (
            f"### Emisor\n{emisor}\n\n"
            f"### Receptor\n{receptor}"
        )

        await message.reply(embed=embed, mention_author=False)

    except Exception as e:
        await message.reply(f"Error:\n```{e}```")

# =========================================================
# BAN
# =========================================================

@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(
    i: discord.Interaction,
    usuario: discord.Member,
    razon: str = "Sin razón"
):
    if usuario == i.user:
        await i.response.send_message("> No puedes banearte a ti mismo", ephemeral=True)
        return

    try:
        await usuario.ban(reason=razon)
        embed = discord.Embed(title="Usuario Baneado", color=0x000000)
        embed.description = (
            f"> Usuario: {usuario.mention}\n"
            f"> Razón: {razon}\n"
            f"> Moderador: {i.user.mention}"
        )
        await i.response.send_message(embed=embed)

    except Exception as e:
        await i.response.send_message(f"Error:\n```{e}```", ephemeral=True)

# =========================================================
# AVATAR
# =========================================================

@bot.tree.command(name="avatar")
async def avatar(
    i: discord.Interaction,
    usuario: discord.Member = None
):
    usuario = usuario or i.user
    embed = discord.Embed(title=f"Avatar de {usuario.name}", color=0x000000)
    embed.set_image(url=usuario.display_avatar.url)
    await i.response.send_message(embed=embed)

# =========================================================
# WARN
# =========================================================

@bot.tree.command(name="warn")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(
    i: discord.Interaction,
    usuario: discord.Member,
    razon: str
):
    gid = str(i.guild.id)
    uid = str(usuario.id)

    if gid not in warnings_data:
        warnings_data[gid] = {}
    if uid not in warnings_data[gid]:
        warnings_data[gid][uid] = []

    warnings_data[gid][uid].append({
        "razon": razon,
        "moderador": str(i.user),
        "fecha": str(datetime.now())
    })

    total = len(warnings_data[gid][uid])

    embed = discord.Embed(
        title="Usuario Advertido <:Protect:1504584589715443723>",
        color=0x000000
    )
    embed.description = (
        f"> Usuario: {usuario.mention}\n"
        f"> Razón: {razon}\n"
        f"> Warnings: {total}"
    )
    await i.response.send_message(embed=embed)

# =========================================================
# WARNINGS
# =========================================================

@bot.tree.command(name="warnings")
async def warnings(
    i: discord.Interaction,
    usuario: discord.Member
):
    gid = str(i.guild.id)
    uid = str(usuario.id)

    if gid not in warnings_data or uid not in warnings_data[gid]:
        await i.response.send_message("> Ese usuario no tiene warnings", ephemeral=True)
        return

    warns = warnings_data[gid][uid]
    texto = ""
    for n, w in enumerate(warns, start=1):
        texto += (
            f"> {n}. {w['razon']}\n"
            f"> Moderador: {w['moderador']}\n\n"
        )

    embed = discord.Embed(
        title=f"Warnings de {usuario.name}",
        description=texto,
        color=0x000000
    )
    await i.response.send_message(embed=embed)

# =========================================================
# LOCK / UNLOCK
# =========================================================

@bot.tree.command(name="lock")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(i: discord.Interaction):
    overwrite = i.channel.overwrites_for(i.guild.default_role)
    overwrite.send_messages = False
    await i.channel.set_permissions(i.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(
        title="Canal Bloqueado",
        description="> Nadie puede enviar mensajes. <:Block:1504584331845435462>",
        color=0x000000
    )
    await i.response.send_message(embed=embed)


@bot.tree.command(name="unlock")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(i: discord.Interaction):
    overwrite = i.channel.overwrites_for(i.guild.default_role)
    overwrite.send_messages = True
    await i.channel.set_permissions(i.guild.default_role, overwrite=overwrite)

    embed = discord.Embed(
        title="Canal Desbloqueado",
        description="> Ya pueden hablar otra vez. <:Unblock:1504584412900233367>",
        color=0x000000
    )
    await i.response.send_message(embed=embed)

# =========================================================
# NUKE
# =========================================================

@bot.tree.command(name="nuke")
@app_commands.checks.has_permissions(manage_channels=True)
async def nuke(i: discord.Interaction):
    canal = i.channel
    nuevo = await canal.clone()
    await canal.delete()

    embed = discord.Embed(
        title="Canal Nukeado",
        description="> Canal purificado exitosamente <:Check:1504584129302499399>.",
        color=0x000000
    )
    await nuevo.send(embed=embed)

# =========================================================
# SPOTIFY
# =========================================================

@bot.tree.command(
    name="spotify",
    description="Muestra la música que escucha un usuario"
)
async def spotify(
    i: discord.Interaction,
    usuario: discord.Member = None
):
    member_id = (usuario or i.user).id
    usuario = i.guild.get_member(member_id)

    if not usuario:
        await i.response.send_message(
            "> **No se pudo obtener la información del usuario**.",
            ephemeral=True
        )
        return

    spotify_activity = discord.utils.find(
        lambda a: isinstance(a, discord.Spotify),
        usuario.activities
    )

    if not spotify_activity:
        await i.response.send_message(
            f"**{usuario.name} no está escuchando Spotify**\n"
            "> o su Spotify no está vinculado a su cuenta"
        )
        return

    segundos_totales = int(spotify_activity.duration.total_seconds())
    minutos = segundos_totales // 60
    segundos = segundos_totales % 60
    duracion = f"{minutos:02}:{segundos:02}"

    embed = discord.Embed(color=0x000000)
    embed.description = (
        f"## Escuchando ahora\n\n"
        f"> **Canción:**\n"
        f"> {spotify_activity.title}\n\n"
        f"> **Artista:**\n"
        f"> {spotify_activity.artist}\n\n"
        f"> **Álbum:**\n"
        f"> {spotify_activity.album}\n\n"
        f"> **Duración:**\n"
        f"> `{duracion}`"
    )
    embed.set_thumbnail(url=spotify_activity.album_cover_url)
    embed.set_footer(
        text=f"{usuario.display_name} en Spotify...",
        icon_url=usuario.display_avatar.url
    )
    await i.response.send_message(embed=embed)

# =========================================================
# AFK
# =========================================================

@bot.tree.command(name="afk")
async def afk(i: discord.Interaction, motivo: str = "Sin motivo"):
    import time

    afk_data[i.user.id] = {
        "motivo": motivo,
        "tiempo": time.time()
    }

    embed = discord.Embed(
        title=f"{i.user.name} está inactivo...",
        color=0x000000
    )
    embed.description = (
        f"**Motivo:**\n"
        f"> `{motivo}`\n"
    )
    embed.set_footer(text="Te avisaré si te mencionan...")
    await i.response.send_message(embed=embed)

import discord
from discord import app_commands

# =========================================================
# DATA
# =========================================================

wlc_config = {}
bye_config = {}

# =========================================================
# PARSE TEXT
# =========================================================

def parse_text(texto, member):
    if not texto:
        return ""
    return texto.replace("{user_name}", member.name) \
                .replace("{user_mention}", member.mention) \
                .replace("{user_id}", str(member.id)) \
                .replace("{server_name}", member.guild.name) \
                .replace("{member_count}", str(member.guild.member_count))

# =========================================================
# HELPERS
# =========================================================

def build_preview(cfg: dict, member) -> discord.Embed:
    try:
        color = int(str(cfg.get("color", "000000")).replace("#", ""), 16)
    except:
        color = 0x000000

    embed = discord.Embed(
        title=parse_text(cfg.get("titulo") or "", member),
        description=parse_text(cfg.get("descripcion") or "", member),
        color=color
    )
    if cfg.get("autor"):
        embed.set_author(
            name=parse_text(cfg["autor"], member),
            icon_url=cfg.get("imagen_autor") or None
        )
    if cfg.get("imagen_banner"):
        embed.set_thumbnail(url=cfg["imagen_banner"])
    if cfg.get("footer"):
        embed.set_footer(
            text=parse_text(cfg["footer"], member),
            icon_url=cfg.get("imagen_footer") or None
        )
    return embed


def build_control(tipo: str, cfg: dict) -> discord.Embed:
    nombre = "Bienvenida" if tipo == "wlc" else "Despedida"
    embed = discord.Embed(title=f"Configuración de {nombre}", color=0x2b2d31)
    embed.description = (
        f"**Primario**\n"
        f"> Título: `{cfg.get('titulo') or 'Sin definir'}`\n"
        f"> Descripción: `{cfg.get('descripcion') or 'Sin definir'}`\n"
        f"> Color: `#{cfg.get('color') or '000000'}`\n\n"
        f"**Secundario**\n"
        f"> Autor: `{cfg.get('autor') or 'Sin definir'}`\n"
        f"> Pie de página: `{cfg.get('footer') or 'Sin definir'}`\n\n"
        f"**Vista previa** ↓"
    )
    return embed


async def refresh(msg, tipo, cfg, interaction):
    await msg.edit(
        embeds=[build_control(tipo, cfg), build_preview(cfg, interaction.user)],
        view=ConfigView(tipo, cfg, msg)
    )

# =========================================================
# MODALS
# =========================================================

class ModalPrimario(discord.ui.Modal):
    def __init__(self, tipo, cfg, msg):
        super().__init__(title="Primario")
        self.tipo = tipo
        self.cfg  = cfg
        self.msg  = msg

        self.add_item(discord.ui.TextInput(label="Título", default=cfg.get("titulo") or "", required=False))
        self.add_item(discord.ui.TextInput(label="Descripción", style=discord.TextStyle.paragraph, placeholder="{user_mention}, {user_name}, {server_name}, {member_count}", default=cfg.get("descripcion") or "", required=False))
        self.add_item(discord.ui.TextInput(label="Color hex", placeholder="FF5733", default=cfg.get("color") or "000000", max_length=7, required=False))

    async def on_submit(self, interaction: discord.Interaction):
        self.cfg["titulo"]      = self.children[0].value.strip()
        self.cfg["descripcion"] = self.children[1].value.strip()
        self.cfg["color"]       = self.children[2].value.strip().replace("#", "")
        await interaction.response.defer()
        await refresh(self.msg, self.tipo, self.cfg, interaction)


class ModalSecundario(discord.ui.Modal):
    def __init__(self, tipo, cfg, msg):
        super().__init__(title="Secundario")
        self.tipo = tipo
        self.cfg  = cfg
        self.msg  = msg

        self.add_item(discord.ui.TextInput(label="Nombre del autor",             default=cfg.get("autor") or "",          required=False))
        self.add_item(discord.ui.TextInput(label="URL imagen autor",             placeholder="https://...", default=cfg.get("imagen_autor") or "",   required=False))
        self.add_item(discord.ui.TextInput(label="Pie de página",                default=cfg.get("footer") or "",         required=False))
        self.add_item(discord.ui.TextInput(label="URL imagen pie de página",     placeholder="https://...", default=cfg.get("imagen_footer") or "",  required=False))
        self.add_item(discord.ui.TextInput(label="URL imagen thumbnail",         placeholder="https://...", default=cfg.get("imagen_banner") or "",  required=False))

    async def on_submit(self, interaction: discord.Interaction):
        self.cfg["autor"]         = self.children[0].value.strip()
        self.cfg["imagen_autor"]  = self.children[1].value.strip()
        self.cfg["footer"]        = self.children[2].value.strip()
        self.cfg["imagen_footer"] = self.children[3].value.strip()
        self.cfg["imagen_banner"] = self.children[4].value.strip()
        await interaction.response.defer()
        await refresh(self.msg, self.tipo, self.cfg, interaction)

# =========================================================
# VIEW
# =========================================================

class ConfigView(discord.ui.View):
    def __init__(self, tipo, cfg, msg=None):
        super().__init__(timeout=300)
        self.tipo = tipo
        self.cfg  = cfg
        self.msg  = msg

    @discord.ui.button(label="Primario", style=discord.ButtonStyle.primary)
    async def btn_primario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalPrimario(self.tipo, self.cfg, self.msg))

    @discord.ui.button(label="Secundario", style=discord.ButtonStyle.secondary)
    async def btn_secundario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalSecundario(self.tipo, self.cfg, self.msg))

    @discord.ui.button(label="Guardar & Activar", style=discord.ButtonStyle.success)
    async def btn_guardar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.tipo == "wlc":
            wlc_config[interaction.guild.id] = self.cfg
        else:
            bye_config[interaction.guild.id] = self.cfg

        nombre = "bienvenida" if self.tipo == "wlc" else "despedida"

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"{nombre.capitalize()} guardada y activada.", ephemeral=True)

# =========================================================
# COMANDOS
# =========================================================

@bot.tree.command(name="wlc", description="Configura el mensaje de bienvenida")
@app_commands.checks.has_permissions(administrator=True)
async def wlc(i: discord.Interaction):
    try:
        cfg  = wlc_config.get(i.guild.id, {}).copy()
        view = ConfigView("wlc", cfg)
        await i.response.send_message(
            embeds=[build_control("wlc", cfg), build_preview(cfg, i.user)],
            view=view,
            ephemeral=True
        )
        view.msg = await i.original_response()
    except Exception as e:
        print(f"Error /wlc: {e}")


@bot.tree.command(name="bye", description="Configura el mensaje de despedida")
@app_commands.checks.has_permissions(administrator=True)
async def bye(i: discord.Interaction):
    try:
        cfg  = bye_config.get(i.guild.id, {}).copy()
        view = ConfigView("bye", cfg)
        await i.response.send_message(
            embeds=[build_control("bye", cfg), build_preview(cfg, i.user)],
            view=view,
            ephemeral=True
        )
        view.msg = await i.original_response()
    except Exception as e:
        print(f"Error /bye: {e}")


@bot.tree.command(name="reset-wlc", description="Desactiva la bienvenida")
@app_commands.checks.has_permissions(administrator=True)
async def reset_wlc(i: discord.Interaction):
    wlc_config.pop(i.guild.id, None)
    await i.response.send_message("Bienvenida desactivada", ephemeral=True)


@bot.tree.command(name="reset-bye", description="Desactiva la despedida")
@app_commands.checks.has_permissions(administrator=True)
async def reset_bye(i: discord.Interaction):
    bye_config.pop(i.guild.id, None)
    await i.response.send_message("Despedida desactivada", ephemeral=True)

# =========================================================
# EVENTOS
# =========================================================

@bot.event
async def on_member_join(member):
    cfg = wlc_config.get(member.guild.id)
    if not cfg:
        return
    canal = member.guild.get_channel(cfg.get("canal", 0))
    if not canal:
        return
    await canal.send(embed=build_preview(cfg, member))
    if cfg.get("mandar_dm"):
        try:
            await member.send(embed=build_preview(cfg, member))
        except:
            pass


@bot.event
async def on_member_remove(member):
    cfg = bye_config.get(member.guild.id)
    if not cfg:
        return
    canal = member.guild.get_channel(cfg.get("canal", 0))
    if not canal:
        return
    await canal.send(embed=build_preview(cfg, member))
    
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
