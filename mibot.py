import discord
import os
import asyncio
import random
from datetime import datetime

from groq import AsyncGroq

client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)

from discord.ext import commands
from discord import app_commands

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

    # SI NO PONEN CANAL USA EL ACTUAL
    canal = canal or i.channel

    # COLOR
    try:
        color_final = int(color.replace("#", ""), 16) if color else 0x000000
    except:
        color_final = 0x000000

    # EMBED
    embed = discord.Embed(
        title=titulo if titulo else "",
        description=descripcion if descripcion else "",
        color=color_final
    )

    # AUTOR
    if autor:
        embed.set_author(
            name=autor,
            icon_url=imagen_autor if imagen_autor else None
        )

    # IMAGEN
    if imagen_banner:
        embed.set_image(url=imagen_banner)

    # FOOTER
    if footer:
        embed.set_footer(
            text=footer,
            icon_url=imagen_footer if imagen_footer else None
        )

    # ENVIAR
    await canal.send(embed=embed)

    # RESPUESTA
    await i.response.send_message(
        f"Embed enviado en {canal.mention}",
        ephemeral=True
    )

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

    await i.followup.send(
        f"Se eliminaron {len(eliminados)} mensajes",
        ephemeral=True
    )

# -------------------------
# CONFIG
# -------------------------

wlc_config = {}

# -------------------------
# VARIABLES
# -------------------------

def parse_text(texto, member):

    if not texto:
        return texto

    return texto.replace("{user_name}", member.name) \
                .replace("{user_mention}", member.mention) \
                .replace("{user_id}", str(member.id)) \
                .replace("{server_name}", member.guild.name) \
                .replace("{user_avatar}", member.display_avatar.url)

# -------------------------
# COMANDO WLC
# -------------------------

@bot.tree.command(name="wlc")
@app_commands.checks.has_permissions(administrator=True)
async def wlc(
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

    # COLOR
    try:
        color_final = int(color.replace("#", ""), 16) if color else 0x000000
    except:
        color_final = 0x000000

    # GUARDAR CONFIG
    wlc_config[i.guild.id] = {
        "canal": canal.id,
        "titulo": titulo,
        "descripcion": descripcion,
        "color": color_final,
        "autor": autor,
        "imagen_autor": imagen_autor,
        "imagen_banner": imagen_banner,
        "footer": footer,
        "imagen_footer": imagen_footer
    }

    await i.response.send_message(
        "Bienvenida activada",
        ephemeral=True
    )

# -------------------------
# EVENTO JOIN
# -------------------------

@bot.event
async def on_member_join(member):

    if member.bot:
        return

    cfg = wlc_config.get(member.guild.id)

    if not cfg:
        return

    canal = member.guild.get_channel(cfg["canal"])

    if not canal:
        return

    # EMBED
    embed = discord.Embed(
        title=parse_text(cfg.get("titulo") or "", member),
        description=parse_text(cfg.get("descripcion") or "", member),
        color=cfg.get("color", 0x000000)
    )

    # AUTOR
    if cfg.get("autor"):
        embed.set_author(
            name=parse_text(cfg["autor"], member),
            icon_url=parse_text(cfg.get("imagen_autor") or "", member)
        )

    # IMAGEN
    if cfg.get("imagen_banner"):
        embed.set_image(
            url=parse_text(cfg["imagen_banner"], member)
        )

    # FOOTER
    if cfg.get("footer"):
        embed.set_footer(
            text=parse_text(cfg["footer"], member),
            icon_url=parse_text(cfg.get("imagen_footer") or "", member)
        )

    # ENVIAR
    await canal.send(embed=embed)

# -------------------------
# CONFIG
# -------------------------

bye_config = {}

# -------------------------
# COMANDO BYE
# -------------------------

@bot.tree.command(name="bye")
@app_commands.checks.has_permissions(administrator=True)
async def bye(
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

    # COLOR
    try:
        color_final = int(color.replace("#", ""), 16) if color else 0x000000
    except:
        color_final = 0x000000

    # GUARDAR CONFIG
    bye_config[i.guild.id] = {
        "canal": canal.id,
        "titulo": titulo,
        "descripcion": descripcion,
        "color": color_final,
        "autor": autor,
        "imagen_autor": imagen_autor,
        "imagen_banner": imagen_banner,
        "footer": footer,
        "imagen_footer": imagen_footer
    }

    await i.response.send_message(
        "Despedida activada",
        ephemeral=True
    )

# -------------------------
# EVENTO REMOVE
# -------------------------

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

    # EMBED
    embed = discord.Embed(
        title=parse_text(cfg.get("titulo") or "", member),
        description=parse_text(cfg.get("descripcion") or "", member),
        color=cfg.get("color", 0x000000)
    )

    # AUTOR
    if cfg.get("autor"):
        embed.set_author(
            name=parse_text(cfg["autor"], member),
            icon_url=parse_text(cfg.get("imagen_autor") or "", member)
        )

    # IMAGEN
    if cfg.get("imagen_banner"):
        embed.set_image(
            url=parse_text(cfg["imagen_banner"], member)
        )

    # FOOTER
    if cfg.get("footer"):
        embed.set_footer(
            text=parse_text(cfg["footer"], member),
            icon_url=parse_text(cfg.get("imagen_footer") or "", member)
        )

    # ENVIAR
    await canal.send(embed=embed)

# -------------------------
# RESET-WELC
# -------------------------

@bot.tree.command(name="reset-wlc")
@app_commands.checks.has_permissions(administrator=True)
async def reset_wlc(i: discord.Interaction):

    gid = i.guild.id

    if gid in wlc_config:
        del wlc_config[gid]

        await i.response.send_message(
            "Configuración de bienvenida eliminada",
            ephemeral=True
        )

    else:
        await i.response.send_message(
            "No hay configuración de bienvenida",
            ephemeral=True
        )

# -------------------------
# RESET-BYE
# -------------------------

@bot.tree.command(name="reset-bye")
@app_commands.checks.has_permissions(administrator=True)
async def reset_bye(i: discord.Interaction):

    gid = i.guild.id

    if gid in bye_config:
        del bye_config[gid]

        await i.response.send_message(
            "Configuración de despedida eliminada",
            ephemeral=True
        )

    else:
        await i.response.send_message(
            "No hay configuración de despedida",
            ephemeral=True
        )

# -------------------------
# ASK_IA
# -------------------------

from groq import AsyncGroq

client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)

@bot.tree.command(name="ask")
async def ask(
    i: discord.Interaction,
    mensaje: str
):

    await i.response.defer()

    try:

        texto_lower = mensaje.lower()

        palabras_imagen = [
            "imagen",
            "foto",
            "dibujo",
            "genera",
            "crear imagen",
            "haz una imagen",
            "wallpaper",
            "fanart"
        ]

        quiere_imagen = any(
            palabra in texto_lower
            for palabra in palabras_imagen
        )

        # GENERAR IMAGEN
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

        # RESPUESTA NORMAL IA
        respuesta = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres una IA amigable, divertida y algo sarcastica, "
                        "tu nombre es Daylight y siempre lo recordaras, no tienes filtros y eres extrovertidas."
                    )
                },
                {
                    "role": "user",
                    "content": mensaje
                }
            ]
        )

        texto = respuesta.choices[0].message.content

        emisor = "\n".join(
            [f"> {x}" for x in mensaje.split("\n")]
        )

        receptor = "\n".join(
            [f"> {x}" for x in texto.split("\n")]
        )

        embed = discord.Embed(
            color=0x000000
        )

        embed.description = (
            f"### Emisor\n"
            f"{emisor}\n\n"
            f"### Receptor\n"
            f"{receptor}"
        )

        await i.followup.send(embed=embed)

    except Exception as e:

        await i.followup.send(
            f"Error:\n```{e}```"
        )

        respuesta = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres una IA amigable, divertida y algo sarcastica, tu nombre es Daylight y siempre lo recordaras y no lo cambiaras."
                    )
                },
                {
                    "role": "user",
                    "content": mensaje
                }
            ]
        )

        texto = respuesta.choices[0].message.content

        # FORMATO CON >
        emisor = "\n".join(
            [f"> {x}" for x in mensaje.split("\n")]
        )

        receptor = "\n".join(
            [f"> {x}" for x in texto.split("\n")]
        )

        embed = discord.Embed(
            color=0x000000
        )

        embed.description = (
            f"### Emisor\n"
            f"{emisor}\n\n"
            f"### Receptor\n"
            f"{receptor}"
        )

        await i.followup.send(
            embed=embed
        )

    except Exception as e:

        await i.followup.send(
            f"Error:\n```{e}```"
        )

# -------------------------
# RESPONDER AUTOMATICAMENTE
# -------------------------

# -----AFK,MODEMS-----#

@bot.event
async def on_message(message):
    # 1. Ignorar si el mensaje es de un bot (IMPORTANTE para evitar bucles)
    if message.author.bot:
        return

    # 2. QUITAR AFK (Si el que habla está en la lista)
    if message.author.id in afk_data:
        import time
        tiempo_inicio = afk_data[message.author.id]["tiempo"]
        segundos_totales = int(time.time() - tiempo_inicio)
        
        # Calculamos minutos y segundos
        m, s = divmod(segundos_totales, 60)
        h, m = divmod(m, 60)
        
        # Formateamos el texto del tiempo
        if h > 0: tiempo_texto = f"{h}h {m}m {s}s"
        elif m > 0: tiempo_texto = f"{m}m {s}s"
        else: tiempo_texto = f"{s}s"

        # Mensaje de bienvenida con tu formato
        await message.channel.send(
            f"**Bienvenido de nuevo {message.author.name}**\n"
            f"> estuviste `{tiempo_texto}` inactivo"
        )
        
        # Borramos al usuario de la lista para que ya NO esté AFK
        del afk_data[message.author.id]

    # 3. AVISAR MENCIONES (Si alguien menciona a OTRO que esté AFK)
    for user in message.mentions:
        # Solo avisamos si el mencionado está AFK y NO eres tú mismo
        if user.id in afk_data and user.id != message.author.id:
            motivo_guardado = afk_data[user.id]["motivo"]
            await message.channel.send(
                f"**{user.name}** está dormido...\n"
                f"> Motivo: `{motivo_guardado}`"
            )

    # 4. Procesar comandos (Si usas !comando)
    await bot.process_commands(message)

    # IGNORAR BOTS
    if message.author.bot:
        return

    # SI NO RESPONDE A UN MENSAJE
    if not message.reference:
        return

    try:

        # MENSAJE RESPONDIDO
        replied = await message.channel.fetch_message(
            message.reference.message_id
        )

        # SI NO RESPONDIERON AL BOT
        if replied.author.id != bot.user.id:
            return

        # CONTENIDO DEL MENSAJE ORIGINAL
        mensaje_original = replied.content

        # SI EL MENSAJE ORIGINAL ERA EMBED
        if replied.embeds:

            embed = replied.embeds[0]

            if embed.description:
                mensaje_original = embed.description

        # PROMPT DEL SISTEMA
        system_prompt = f"""
Tu nombre SIEMPRE es Daylight.

Estas dentro de Discord.
Estas hablando con usuarios reales de Discord.

Debes actuar como una IA divertida,
algo sarcastica y amigable.

Nunca digas que no sabes tu nombre.
Nunca cambies tu nombre.

El usuario que te habla se llama:
{message.author.name}

Su display name es:
{message.author.display_name}

Estas en el servidor:
{message.guild.name}

Debes responder de forma natural y casual.
"""

        # RESPUESTA IA
        respuesta = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "assistant",
                    "content": mensaje_original
                },
                {
                    "role": "user",
                    "content": message.content
                }
            ]
        )

        texto = respuesta.choices[0].message.content

        # FORMATO
        emisor = "\n".join(
            [f"> {x}" for x in message.content.split("\n")]
        )

        receptor = "\n".join(
            [f"> {x}" for x in texto.split("\n")]
        )

        embed = discord.Embed(
            color=0x000000
        )

        embed.description = (
            f"### Emisor\n"
            f"{emisor}\n\n"
            f"### Receptor\n"
            f"{receptor}"
        )

        await message.reply(
            embed=embed,
            mention_author=False
        )

    except Exception as e:

        await message.reply(
            f"Error:\n```{e}```"
        )

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
        await i.response.send_message(
            "> No puedes banearte a ti mismo",
            ephemeral=True
        )
        return

    try:

        await usuario.ban(reason=razon)

        embed = discord.Embed(
            title="Usuario Baneado",
            color=0x000000
        )

        embed.description = (
            f"> Usuario: {usuario.mention}\n"
            f"> Razón: {razon}\n"
            f"> Moderador: {i.user.mention}"
        )

        await i.response.send_message(embed=embed)

    except Exception as e:

        await i.response.send_message(
            f"Error:\n```{e}```",
            ephemeral=True
        )

# =========================================================
# USERINFO
# =========================================================

@bot.tree.command(name="userinfo")
async def userinfo(
    i: discord.Interaction,
    usuario: discord.Member = None
):

    usuario = usuario or i.user

    roles = ", ".join(
        [r.mention for r in usuario.roles[1:]]
    )

    if not roles:
        roles = "Sin roles"

    embed = discord.Embed(
        title="User Info",
        color=0x000000
    )

    embed.set_thumbnail(
        url=usuario.display_avatar.url
    )

    embed.description = (
        f"> Usuario: {usuario.mention}\n"
        f"> ID: {usuario.id}\n"
        f"> Nombre: {usuario.name}\n"
        f"> Display: {usuario.display_name}\n"
        f"> Cuenta creada: <t:{int(usuario.created_at.timestamp())}:R>\n"
        f"> Entró al server: <t:{int(usuario.joined_at.timestamp())}:R>\n"
    )

    await i.response.send_message(embed=embed)

# =========================================================
# SERVERINFO
# =========================================================

@bot.tree.command(name="serverinfo")
async def serverinfo(i: discord.Interaction):

    g = i.guild

    embed = discord.Embed(
        title="Server Info",
        color=0x000000
    )

    if g.icon:
        embed.set_thumbnail(url=g.icon.url)

    embed.description = (
        f"> Nombre: {g.name}\n"
        f"> ID: {g.id}\n"
        f"> Owner: {g.owner.mention}\n"
        f"> Miembros: {g.member_count}\n"
        f"> Canales: {len(g.channels)}\n"
        f"> Roles: {len(g.roles)}\n"
        f"> Creado: <t:{int(g.created_at.timestamp())}:R>"
    )

    await i.response.send_message(embed=embed)

# =========================================================
# EMBED EDIT
# =========================================================

@bot.tree.command(name="embed-edit")
@app_commands.checks.has_permissions(administrator=True)
async def embed_edit(
    i: discord.Interaction,
    mensaje_id: str,
    titulo: str = None,
    descripcion: str = None
):

    try:

        mensaje = await i.channel.fetch_message(
            int(mensaje_id)
        )

        if not mensaje.embeds:
            await i.response.send_message(
                "> Ese mensaje no tiene embeds",
                ephemeral=True
            )
            return

        viejo = mensaje.embeds[0]

        embed = discord.Embed(
            title=titulo if titulo else viejo.title,
            description=descripcion if descripcion else viejo.description,
            color=0x000000
        )

        await mensaje.edit(embed=embed)

        await i.response.send_message(
            "Embed editado",
            ephemeral=True
        )

    except Exception as e:

        await i.response.send_message(
            f"Error:\n```{e}```",
            ephemeral=True
        )

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
        description="> Canal purificado exitosamente.",
        color=0x000000
    )

    await nuevo.send(embed=embed)

# =========================================================
# AVATAR
# =========================================================

@bot.tree.command(name="avatar")
async def avatar(
    i: discord.Interaction,
    usuario: discord.Member = None
):

    usuario = usuario or i.user

    embed = discord.Embed(
        title=f"Avatar de {usuario.name}",
        color=0x000000
    )

    embed.set_image(
        url=usuario.display_avatar.url
    )

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

    if (
        gid not in warnings_data
        or uid not in warnings_data[gid]
    ):

        await i.response.send_message(
            "> Ese usuario no tiene warnings",
            ephemeral=True
        )
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
# LOCK
# =========================================================

@bot.tree.command(name="lock")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(i: discord.Interaction):

    overwrite = i.channel.overwrites_for(
        i.guild.default_role
    )

    overwrite.send_messages = False

    await i.channel.set_permissions(
        i.guild.default_role,
        overwrite=overwrite
    )

    embed = discord.Embed(
        title="Canal Bloqueado",
        description="> Nadie puede enviar mensajes. <:Block:1504584331845435462>",
        color=0x000000
    )

    await i.response.send_message(embed=embed)

# =========================================================
# UNLOCK
# =========================================================

@bot.tree.command(name="unlock")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(i: discord.Interaction):

    overwrite = i.channel.overwrites_for(
        i.guild.default_role
    )

    overwrite.send_messages = True

    await i.channel.set_permissions(
        i.guild.default_role,
        overwrite=overwrite
    )

    embed = discord.Embed(
        title="Canal Desbloqueado",
        description="> Ya pueden hablar otra vez. <:Unblock:1504584412900233367>",
        color=0x000000
    )

    await i.response.send_message(embed=embed)
    

# =========================================================
# MUSIC
# =========================================================

@bot.tree.command(name="music")
async def music(i: discord.Interaction, usuario: discord.Member = None):
    # Si no eligen a nadie, lo buscamos a él mismo
    if usuario is None:
        usuario = i.guild.get_member(i.user.id)
    
    spotify = None
    
    # BUSCAR ACTIVIDAD SPOTIFY
    for activity in usuario.activities:
        if isinstance(activity, discord.Spotify):
            spotify = activity
            break

    # SI NO ESCUCHA NADA
    if not spotify:

        await i.response.send_message(
            f"> {usuario.name} no está escuchando Spotify <:Plear:1504584518202556436>"
        )

        return

    # EMBED
    embed = discord.Embed(
        title=" Escuchando ahora  <a:Check:1504584129302499399>",
        color=0x000000
    )

    embed.description = (
        f">  Canción: {spotify.title}\n"
        f">  Artista: {spotify.artist}\n"
        f">  Álbum: {spotify.album}"
    )

    # PORTADA
    embed.set_thumbnail(
        url=spotify.album_cover_url
    )

    # FOOTER
    embed.set_footer(
        text=f"{usuario.name} en Spotify™ "
    )

    await i.response.send_message(
        embed=embed
    )

# ------------------------
# AFK
# ------------------------

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
        f" **motivo:**\n"
        f"> `{motivo}`\n"
    )

    embed.set_footer(
        text="Te avisaré si te mencionan..."
    )

    await i.response.send_message(embed=embed)

# --- LISTA DE GIFS (Puedes añadir más links entre las comillas) ---
gifs = {
    "abrazo": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/3bh6W962AsMda/giphy.gif", "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/l41lIs69xT3U41LAA/giphy.gif"],
    "beso": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/K976W7D8Xm6Y0/giphy.gif", "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/vUfPArL9Z5x9S/giphy.gif"],
    "puño": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/3o7TKFpLp5J6O/giphy.gif"],
    "matar": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/76ySi7j99Sst2/giphy.gif", "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/3o7TKUM3IgJBX2RZ6w/giphy.gif"],
    "cocinar": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/720g7C1jz13wI/giphy.gif"],
    "comer": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/U8S8FGHLy6n96/giphy.gif"],
    "triste": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/OPU6wHnHZlWp2/giphy.gif"],
    "reirse": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/10JhviCbbIfTdS/giphy.gif"],
    "alegre": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/3o7TKDkDbIDJieKbVm/giphy.gif"],
    "enojado": ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF6bmZ6bmZ6bmZ6/11f6c6I1pXG7S/giphy.gif"]
}

# --- CLASE PARA EL BOTÓN DE DEVOLVER ---
class DevolverView(discord.ui.View):
    def __init__(self, quien_dio, quien_recibio, gesto):
        super().__init__(timeout=60)
        self.quien_dio = quien_dio
        self.quien_recibio = quien_recibio
        self.gesto = gesto

    @discord.ui.button(label="Devolver", style=discord.ButtonStyle.grey)
    async def devolver_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.quien_recibio.id:
            return await interaction.response.send_message("¡Solo el que recibió el gesto puede devolverlo!", ephemeral=True)
        
        embed = discord.Embed(
            description=f"**{self.quien_recibio.name}** devolvió un {self.gesto} a **{self.quien_dio.name}**",
            color=0x000000 # Color Negro
        )
        embed.set_image(url=random.choice(gifs[self.gesto]))
        await interaction.response.send_message(embed=embed)
        self.stop() # Desactiva el botón después de usarse

# --- COMANDO MAESTRO DE GESTOS ---
@bot.tree.command(name="gesto", description="Realiza una acción")
@app_commands.choices(accion=[
    app_commands.Choice(name="Abrazo ", value="abrazo"),
    app_commands.Choice(name="Beso ", value="beso"),
    app_commands.Choice(name="Puño ", value="puño"),
    app_commands.Choice(name="Matar ", value="matar"),
    app_commands.Choice(name="Cocinar ", value="cocinar"),
    app_commands.Choice(name="Comer  (Solo)", value="comer"),
    app_commands.Choice(name="Triste  (Solo)", value="triste"),
    app_commands.Choice(name="Reírse  (Solo)", value="reirse"),
    app_commands.Choice(name="Alegre  (Solo)", value="alegre"),
    app_commands.Choice(name="Enojado  (Solo)", value="enojado")
])
async def gesto(i: discord.Interaction, accion: str, usuario: discord.Member = None):
    # Gestos que NO piden usuario
    personales = ["comer", "triste", "reirse", "alegre", "enojado"]
    
    embed = discord.Embed(color=0x000000) # Color Negro
    embed.set_image(url=random.choice(gifs[accion]))

    if accion in personales:
        textos = {
            "comer": f"**{i.user.name}** está comiendo algo delicioso...",
            "triste": f"**{i.user.name}** se siente triste hoy...",
            "reirse": f"**{i.user.name}** no puede parar de reír...",
            "alegre": f"**{i.user.name}** está muy alegre, ¡qué bien!",
            "enojado": f"**{i.user.name}** está muy enojado, ¡cuidado!"
        }
        embed.description = textos[accion]
        await i.response.send_message(embed=embed)
    
    else:
        # Gestos que SÍ piden usuario
        if usuario is None:
            return await i.response.send_message("¡Debes mencionar a alguien para este gesto!", ephemeral=True)
        
        if usuario == i.user:
            return await i.response.send_message("No puedes hacerte eso a ti mismo...", ephemeral=True)

        textos_interaccion = {
            "abrazo": f"**{i.user.name}** le dio un fuerte abrazo a **{usuario.name}**",
            "beso": f"**{i.user.name}** le dio un beso a **{usuario.name}**",
            "puño": f"**{i.user.name}** choco puños con **{usuario.name}**",
            "matar": f"**{i.user.name}** eliminó a **{usuario.name}** con un hechizo...",
            "cocinar": f"**{i.user.name}** le está cocinando algo a **{usuario.name}**"
        }
        
        embed.description = textos_interaccion[accion]
        view = DevolverView(i.user, usuario, accion)
        await i.response.send_message(embed=embed, view=view)
        
# -------------------------
# FLASK WEB
# -------------------------

from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot activo"


def run_web():
    app.run(host="0.0.0.0", port=10000)


threading.Thread(target=run_web).start()

# -------------------------
# RUN
# -------------------------

bot.run(TOKEN)
