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
mensaje_count = {}

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
    # Lista de fuentes a intentar en orden
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

# =========================================================
# GENERAR TARJETA SPOTIFY
# =========================================================

async def generar_spotify(usuario: discord.Member, actividad: discord.Spotify) -> discord.File:
    W, H     = 680, 180
    FONDO    = (14, 14, 14)
    VERDE    = (29, 185, 84)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA LATERAL
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=VERDE)

    # PORTADA DEL ALBUM
    try:
        portada = await descargar_imagen(actividad.album_cover_url)
        portada = portada.resize((130, 130)).convert("RGBA")

        # MASK REDONDEADA
        mask = Image.new("L", (130, 130), 0)
        ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (130, 130)], radius=10, fill=255)
        portada_r = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
        portada_r.paste(portada, (0, 0), mask)
        img.paste(portada_r, (30, 25), portada_r)
    except:
        draw.rounded_rectangle([(30, 25), (160, 155)], radius=10, fill=GRIS)

    # BORDE PORTADA
    draw.rounded_rectangle([(29, 24), (161, 156)], radius=10, outline=VERDE, width=2)

    # USUARIO
    draw.text((182, 28), f"{usuario.display_name} está escuchando", font=fuente(13), fill=SUBTEXTO)

    # CANCION
    cancion = actividad.title[:30] + "..." if len(actividad.title) > 30 else actividad.title
    draw.text((182, 50), cancion, font=fuente(20, bold=True), fill=TEXTO)

    # ARTISTA
    draw.text((182, 78), actividad.artist, font=fuente(14), fill=VERDE)

    # ALBUM
    album = actividad.album[:35] + "..." if len(actividad.album) > 35 else actividad.album
    draw.text((182, 100), album, font=fuente(12), fill=SUBTEXTO)

    # SEPARADOR
    draw.rectangle([(182, 118), (645, 119)], fill=GRIS)

    # BARRA DE PROGRESO
    ahora     = discord.utils.utcnow()
    inicio    = actividad.start
    duracion  = actividad.duration.total_seconds()
    transcurrido = (ahora - inicio).total_seconds()
    progreso  = min(transcurrido / duracion, 1.0) if duracion > 0 else 0

    draw.rounded_rectangle([(182, 128), (645, 136)], radius=4, fill=GRIS)
    fill_w = int(182 + (463 * progreso))
    if fill_w > 182:
        draw.rounded_rectangle([(182, 128), (fill_w, 136)], radius=4, fill=VERDE)

    # TIEMPO
    t_actual = int(transcurrido)
    t_total  = int(duracion)
    fmt = lambda s: f"{s // 60}:{s % 60:02}"
    draw.text((182, 148), fmt(max(t_actual, 0)), font=fuente(11), fill=SUBTEXTO)
    draw.text((645, 148), fmt(t_total), font=fuente(11), fill=SUBTEXTO, anchor="ra")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="spotify.png")

# =========================================================
# COMANDO SPOTIFY
# =========================================================

@bot.tree.command(name="spotify", description="Muestra la música que escucha un usuario")
async def spotify(
    i: discord.Interaction,
    usuario: discord.Member = None
):
    await i.response.defer()

    member_id = (usuario or i.user).id
    usuario   = i.guild.get_member(member_id)

    if not usuario:
        await i.followup.send("> ❌ No se pudo obtener el usuario.", ephemeral=True)
        return

    actividad = discord.utils.find(
        lambda a: isinstance(a, discord.Spotify),
        usuario.activities
    )

    if not actividad:
        await i.followup.send(
            f"**{usuario.display_name} no está escuchando Spotify**\n"
            f"> o su Spotify no está vinculado a su cuenta",
            ephemeral=True
        )
        return

    archivo = await generar_spotify(usuario, actividad)
    await i.followup.send(file=archivo)

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

wlc_canal = {}
bye_canal = {}

# =========================================================
# COMANDO WLC
# =========================================================

@bot.tree.command(name="wlc", description="Activa el mensaje de bienvenida")
@app_commands.checks.has_permissions(administrator=True)
async def wlc(i: discord.Interaction, canal: discord.TextChannel):
    wlc_canal[i.guild.id] = canal.id
    await i.response.send_message(
        f"> Bienvenida activada en {canal.mention}...<:Check:1504584129302499399>",
        ephemeral=True
    )

# =========================================================
# COMANDO BYE
# =========================================================

@bot.tree.command(name="bye", description="Activa el mensaje de despedida")
@app_commands.checks.has_permissions(administrator=True)
async def bye(i: discord.Interaction, canal: discord.TextChannel):
    bye_canal[i.guild.id] = canal.id
    await i.response.send_message(
        f"> Despedida activada en {canal.mention}...<:Check:1504584129302499399>",
        ephemeral=True
    )

# =========================================================
# RESET
# =========================================================

@bot.tree.command(name="reset-wlc", description="Desactiva la bienvenida")
@app_commands.checks.has_permissions(administrator=True)
async def reset_wlc(i: discord.Interaction):
    wlc_canal.pop(i.guild.id, None)
    await i.response.send_message("> Bienvenida desactivada...<:Check:1504584129302499399>", ephemeral=True)


@bot.tree.command(name="reset-bye", description="Desactiva la despedida")
@app_commands.checks.has_permissions(administrator=True)
async def reset_bye(i: discord.Interaction):
    bye_canal.pop(i.guild.id, None)
    await i.response.send_message("> Despedida desactivada...<:Check:1504584129302499399>", ephemeral=True)

# =========================================================
# EVENTO JOIN
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
            f"12 edad _Mínima_ ♱ 18 edad _Maxima_ ∘ ˙ (🦢)\n\n"
            f"[Book](https://0.com) | [Lobby](https://0.com) | [General](https://0.com)    ⌗"
        ),
        color=0xFFFFFF
    )
    embed.set_author(
        name=member.display_name,
        icon_url=member.display_avatar.url
    )

    await canal.send(embed=embed)

# =========================================================
# EVENTO REMOVE
# =========================================================

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
            f"12 edad _Mínima_ ♱ 18 edad _Maxima_ ∘ ˙ (🦢)\n\n"
            f"[Book](https://0.com) | [Lobby](https://0.com) | [General](https://0.com)    ⌗"
        ),
        color=0xFFFFFF
    )
    embed.set_footer(
        text=member.display_name,
        icon_url=member.display_avatar.url
    )

    await canal.send(embed=embed)

# =========================================================
# NIVELES - DATA
# =========================================================

import time
xp_data = {}
nivel_canal = {}
xp_cooldown = {}

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

# =========================================================
# GENERAR TARJETA
# =========================================================

async def generar_nivel(usuario: discord.Member, nivel: int, xp: int, xp_needed: int) -> discord.File:
    W, H = 680, 180
    FONDO       = (14, 14, 14)
    ACENTO      = (245, 240, 232)   # crema
    TEXTO       = (255, 255, 255)
    SUBTEXTO    = (170, 170, 170)
    GRIS        = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA LATERAL
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ACENTO)

    # AVATAR
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 100)
        img.paste(av, (38, 40), av)
    except:
        draw.ellipse([(38, 40), (138, 140)], fill=GRIS, outline=ACENTO, width=2)

    # BORDE AVATAR
    draw.ellipse([(36, 38), (140, 142)], outline=ACENTO, width=2)

    # NOMBRE
    draw.text((162, 28), usuario.display_name, font=fuente(21, bold=True), fill=TEXTO)

    # BADGE NIVEL
    draw.rounded_rectangle([(162, 62), (242, 84)], radius=11, fill=ACENTO)
    draw.text((202, 68), f"Nivel {nivel}", font=fuente(12, bold=True), fill=FONDO, anchor="mt")

    # XP TEXTO
    draw.text((162, 105), f"{xp} / {xp_needed} XP", font=fuente(12), fill=SUBTEXTO)

    # BARRA XP FONDO
    draw.rounded_rectangle([(162, 118), (630, 130)], radius=6, fill=GRIS)

    # BARRA XP RELLENO
    progreso = min(xp / xp_needed, 1.0)
    fill_w   = int(162 + (468 * progreso))
    if fill_w > 162:
        draw.rounded_rectangle([(162, 118), (fill_w, 130)], radius=6, fill=ACENTO)

    # MENSAJE
    draw.text((162, 152), f"Subiste al nivel {nivel} — sigue así!", font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="nivel.png")

# =========================================================
# COMANDO: setear canal de niveles
# =========================================================

@bot.tree.command(name="set-niveles", description="Elige el canal donde se anuncian los niveles")
@app_commands.checks.has_permissions(administrator=True)
async def set_niveles(i: discord.Interaction, canal: discord.TextChannel):
    nivel_canal[i.guild.id] = canal.id
    await i.response.send_message(f"> Canal de niveles seteado en {canal.mention}", ephemeral=True)

# =========================================================
# COMANDO: ver nivel
# =========================================================

@bot.tree.command(name="nivel", description="Ve tu nivel actual")
async def nivel_cmd(i: discord.Interaction, usuario: discord.Member = None):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    data     = get_xp(i.guild.id, usuario.id)

    archivo = await generar_nivel(
        usuario,
        data["level"],
        data["xp"],
        xp_para_nivel(data["level"])
    )
    await i.followup.send(file=archivo)

# =========================================================
# EVENTO: dar XP por mensaje (cooldown 2 min)
# =========================================================

@bot.listen("on_message")
async def dar_xp(message):

    # MONEDAS CADA 5 MENSAJES
    uid = str(message.author.id)
    if uid not in mensaje_count:
        mensaje_count[uid] = 0
    mensaje_count[uid] += 1

    if mensaje_count[uid] >= 5:
        mensaje_count[uid] = 0
        data = get_user_eco(str(message.guild.id), message.author.id)
        data["coins"] += random.randint(2, 4)
        
    if message.author.bot or not message.guild:
        return

    uid = message.author.id
    ahora = time.time()

    # COOLDOWN 2 MINUTOS
    if ahora - xp_cooldown.get(uid, 0) < 120:
        return
    xp_cooldown[uid] = ahora

    data       = get_xp(message.guild.id, uid)
    data["xp"] += random.randint(10, 20)

    xp_needed = xp_para_nivel(data["level"])

    if data["xp"] >= xp_needed:
        data["xp"]    -= xp_needed
        data["level"] += 1

        canal_id = nivel_canal.get(message.guild.id)
        canal    = message.guild.get_channel(canal_id) if canal_id else message.channel

        try:
            archivo = await generar_nivel(
                message.author,
                data["level"],
                data["xp"],
                xp_para_nivel(data["level"])
            )
            await canal.send(
                content=message.author.mention,
                file=archivo
            )
        except Exception as e:
            print(f"Error nivel: {e}")

# =========================================================
# ECONOMIA - DATA
# =========================================================

economia_data = {}
daily_cooldown = {}

def get_user_eco(guild_id, user_id):
    gid = str(guild_id)
    uid = str(user_id)
    if gid not in economia_data:
        economia_data[gid] = {}
    if uid not in economia_data[gid]:
        economia_data[gid][uid] = {"coins": 0, "last_daily": 0}
    return economia_data[gid][uid]

# =========================================================
# GENERAR TARJETA BALANCE
# =========================================================

async def generar_balance(usuario: discord.Member, coins: int, last_daily: float) -> discord.File:
    W, H     = 680, 170
    FONDO    = (14, 14, 14)
    ACENTO   = (245, 240, 232)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA LATERAL
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ACENTO)

    # AVATAR
    try:
        av = await descargar_imagen(str(usuario.display_avatar.url))
        av = avatar_circular(av, 96)
        img.paste(av, (37, 37), av)
    except:
        draw.ellipse([(37, 37), (133, 133)], fill=GRIS)

    # BORDE AVATAR
    draw.ellipse([(35, 35), (135, 135)], outline=ACENTO, width=2)

    # NOMBRE
    draw.text((158, 26), usuario.display_name, font=fuente(20, bold=True), fill=TEXTO)

    # BADGE
    draw.rounded_rectangle([(158, 54), (278, 78)], radius=11, fill=ACENTO)
    draw.text((218, 56), "Cuenta bancaria", font=fuente(13, bold=True), fill=FONDO)
    # SEPARADOR
    draw.rectangle([(158, 90), (640, 91)], fill=GRIS)

    # MONEDAS
    draw.text((158, 106), f"$ {coins:,} monedas", font=fuente(22, bold=True), fill=ACENTO)

    # ULTIMO DAILY
    if last_daily == 0:
        daily_texto = "> Nunca reclamaste tu daily"
    else:
        hace = int(time.time() - last_daily)
        if hace < 3600:
            daily_texto = f"> Último daily: hace {hace // 60} minutos"
        elif hace < 86400:
            daily_texto = f"> Último daily: hace {hace // 3600} horas"
        else:
            daily_texto = f"> Último daily: hace {hace // 86400} días"

    draw.text((158, 148), daily_texto, font=fuente(12), fill=SUBTEXTO)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="balance.png")

# =========================================================
# GENERAR TARJETA RANKING
# =========================================================

async def generar_ranking(guild: discord.Guild, top: list) -> discord.File:
    filas = len(top)
    W     = 680
    H     = 130 + (filas * 46)
    FONDO    = (14, 14, 14)
    ACENTO   = (245, 240, 232)
    TEXTO    = (255, 255, 255)
    SUBTEXTO = (136, 136, 136)
    GRIS     = (42, 42, 42)
    OSCURO   = (21, 21, 21)

    img  = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    # BARRA LATERAL
    draw.rounded_rectangle([(0, 0), (6, H)], radius=3, fill=ACENTO)

    # TITULO
    draw.text((34, 30), "Ranking", font=fuente(18, bold=True), fill=TEXTO)
    draw.text((34, 58), "Top usuarios con más monedas", font=fuente(11), fill=SUBTEXTO)

    # SEPARADOR
    draw.rectangle([(34, 72), (646, 73)], fill=GRIS)

    medallas = ["🥇", "🥈", "🥉"]

    for n, (uid, data) in enumerate(top):
        member = guild.get_member(int(uid))
        nombre = member.display_name if member else f"Usuario {uid}"
        nombre = nombre[:20] + "..." if len(nombre) > 20 else nombre

        y = 82 + (n * 46)

        # FONDO FILA
        color_fila = (26, 26, 26) if n == 0 else OSCURO
        draw.rounded_rectangle([(34, y), (646, y + 36)], radius=8, fill=color_fila)

        # MEDALLA O NUMERO
        medalla = medallas[n] if n < 3 else f"#{n+1}"
        draw.text((54, y + 8), medalla, font=fuente(14, bold=True), fill=ACENTO if n == 0 else SUBTEXTO)

        # NOMBRE
        draw.text((90, y + 10), nombre, font=fuente(13, bold=n == 0), fill=TEXTO)

        # MONEDAS
        coins_texto = f"🪙 {data['coins']:,}"
        draw.text((620, y + 10), coins_texto, font=fuente(13), fill=ACENTO if n == 0 else SUBTEXTO, anchor="ra")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="ranking.png")

# =========================================================
# COMANDO BALANCE
# =========================================================

@bot.tree.command(name="balance", description="Ve tu cuenta bancaria")
async def balance(
    i: discord.Interaction,
    usuario: discord.Member = None
):
    await i.response.defer()
    usuario = i.guild.get_member((usuario or i.user).id)
    data    = get_user_eco(i.guild.id, usuario.id)

    archivo = await generar_balance(
        usuario,
        data["coins"],
        data["last_daily"]
    )
    await i.followup.send(file=archivo)

# =========================================================
# COMANDO DAILY
# =========================================================

@bot.tree.command(name="daily", description="Reclama tus monedas diarias")
async def daily(i: discord.Interaction):
    await i.response.defer()
    data  = get_user_eco(i.guild.id, i.user.id)
    ahora = time.time()

    if ahora - data["last_daily"] < 86400:
        restante  = int(86400 - (ahora - data["last_daily"]))
        horas     = restante // 3600
        minutos   = (restante % 3600) // 60
        segundos  = restante % 60

        embed = discord.Embed(color=0x0e0e0e)
        embed.description = (
            f"**Ya reclamaste tu daily**\n\n"
            f"> Vuelve en `{horas:02}:{minutos:02}:{segundos:02}`"
        )
        await i.followup.send(embed=embed, ephemeral=True)
        return

    recompensa          = random.randint(100, 500)
    data["coins"]      += recompensa
    data["last_daily"]  = ahora

    archivo = await generar_balance(
        i.guild.get_member(i.user.id),
        data["coins"],
        data["last_daily"]
    )

    await i.followup.send(
        content=f"> Recibiste **{recompensa}** monedas!",
        file=archivo
    )

# =========================================================
# COMANDO RANKING
# =========================================================

@bot.tree.command(name="ranking", description="Top de usuarios con más monedas")
async def ranking(i: discord.Interaction):
    await i.response.defer()

    gid = str(i.guild.id)
    if gid not in economia_data or not economia_data[gid]:
        await i.followup.send("> Nadie tiene monedas todavía.", ephemeral=True)
        return

    top = sorted(
        economia_data[gid].items(),
        key=lambda x: x[1]["coins"],
        reverse=True
    )[:10]

    archivo = await generar_ranking(i.guild, top)
    await i.followup.send(file=archivo)
    
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
