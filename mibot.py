import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. CONFIGURACIÓN PARA RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Darky Limpiador activado 💜"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. CONFIGURACIÓN DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="darky!", intents=intents)

@bot.event
async def on_ready():
    print(f'¡MimiBot listo para borrar evidencia! 💜🤣')

# --- 3. COMANDO DELETE (LIMPIAR CHAT) ---
@bot.command()
@commands.has_permissions(manage_messages=True) # Solo gente con poder puede usarlo
async def delete(ctx, cantidad: int):
    try:
        # Sumamos 1 para borrar también el mensaje del comando "darky!delete"
        await ctx.channel.purge(limit=cantidad + 1)
        
        # Mandamos un mensaje que se borra solo en 3 segundos para no ensuciar
        mensaje_exito = await ctx.send(f"✅ ¡Ija! Borré {cantidad} mensajes de un plumazo. 💜🤣")
        await mensaje_exito.delete(delay=3)
        
    except Exception as e:
        await ctx.send(f"Ija ke dice 💜🤣 No pude borrar los mensajes. ¿Tengo permisos? \nError: {e}")

# --- COMANDO EMBED (EL QUE YA TENÍAS) ---
@bot.command()
async def embed(ctx, canal: Optional[discord.TextChannel], titulo, descripcion, color, imagen=None):
    try:
        destino = canal or ctx.channel
        color_hex = int(color.replace("#", ""), 16)
        embed_final = discord.Embed(title=titulo, description=descripcion, color=color_hex)
        if imagen: embed_final.set_image(url=imagen)
        await destino.send(embed=embed_final)
        if canal: await ctx.send(f"✅ Enviado a {canal.mention}")
    except:
        await ctx.send("Ija 💜🤣 Uso: `darky!embed #canal(opcional) \"Tit\" \"Desc\" #Color` ")

# --- 4. ENCENDIDO ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: Falta el TOKEN en Render.")
