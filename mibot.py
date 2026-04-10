import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. CONFIGURACIÓN PARA RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Darky Slash Edition 💜"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        # Esto sincroniza los comandos de barra con Discord
        await self.tree.sync()
        print(f"¡Comandos slash sincronizados! 💜🤣")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'¡MimiBot ya despertó en modo Slash! 💜🤣')

# --- 3. COMANDO /EMBED ---
@bot.tree.command(name="embed", description="Crea un mensaje embed bien pro")
@app_commands.describe(
    canal="Canal donde se enviará (opcional)",
    titulo="El título del mensaje",
    descripcion="Lo que dirá el mensaje",
    color="Color en HEX (ej: #ff0000)",
    imagen="Link de la imagen (opcional)"
)
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str, color: str, canal: Optional[discord.TextChannel] = None, imagen: Optional[str] = None):
    try:
        destino = canal or interaction.channel
        color_hex = int(color.replace("#", ""), 16)
        
        embed_final = discord.Embed(title=titulo, description=descripcion, color=color_hex)
        if imagen:
            embed_final.set_image(url=imagen)

        await destino.send(embed=embed_final)
        await interaction.response.send_message(f"✅ ¡Ija! Mensaje enviado a {destino.mention}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Ija 💜🤣 Algo salió mal: {e}", ephemeral=True)

# --- 4. COMANDO /DELETE ---
@bot.tree.command(name="delete", description="Borra una cantidad de mensajes")
@app_commands.describe(cantidad="Cuántos mensajes quieres borrar")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    try:
        # En Slash commands no podemos borrar el mensaje del comando, así que borramos exactos
        await interaction.channel.purge(limit=cantidad)
        await interaction.response.send_message(f"✅ ¡Ija! Borré {cantidad} mensajes. 💜🤣", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Ija 💜🤣 No tengo permisos o algo pasó: {e}", ephemeral=True)

# --- 5. ENCENDIDO ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: Falta el TOKEN en Render.")
