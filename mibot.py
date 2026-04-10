import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# --- 1. CONFIGURACIÓN PARA RENDER (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Darky está vivo 💜"

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
    print(f'¡MimiBot ya despertó! 💜')

@bot.command()
async def embed(ctx, titulo, descripcion, color, imagen=None):
    try:
        color_limpio = color.replace("#", "")
        color_hex = int(color_limpio, 16)
        embed_final = discord.Embed(title=titulo, description=descripcion, color=color_hex)
        if imagen:
            embed_final.set_image(url=imagen)
        await ctx.send(embed=embed_final)
    except Exception as e:
        await ctx.send(f"Ija ke dice 💜🤣 error: {e}")

# --- 3. ENCENDIDO ---
if __name__ == "__main__":
    keep_alive()
    token_secreto = os.getenv('TOKEN')
    if token_secreto:
        bot.run(token_secreto)
    else:
        print("❌ ERROR: Falta la variable TOKEN en Render.")