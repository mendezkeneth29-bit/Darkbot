import discord
import os

from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("TOKEN")

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

@bot.tree.command(name="ask")
async def ask(
    i: discord.Interaction,
    mensaje: str
):

    await i.response.defer()

    try:

        respuesta = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres una IA amigable, divertida y algo sarcastica."
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
        emisor = "\n".join([f"> {x}" for x in mensaje.split("\n")])
        receptor = "\n".join([f"> {x}" for x in texto.split("\n")])

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
