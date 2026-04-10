import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# --- 1. CONFIGURACIÓN PARA RENDER (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Darky está vivo y dominando el mundo 💜"

def run():
    # Render usa el puerto 8080 por defecto
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. CONFIGURACIÓN DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True # Importante para que lea tus comandos

bot = commands.Bot(command_prefix="darky!", intents=intents)

@bot.event
async def on_ready():
    print(f'¡MimiBot ya despertó! 💜🤣')

# --- 3. COMANDO EMBED CON SELECCIÓN DE CANAL ---
@bot.command()
async def embed(ctx, canal: discord.TextChannel, titulo, descripcion, color, imagen=None):
    try:
        # Limpiamos el color por si ponen el #
        color_limpio = color.replace("#", "")
        color_hex = int(color_limpio, 16)

        embed_final = discord.Embed(
            title=titulo,
            description=descripcion,
            color=color_hex
        )

        if imagen and imagen.startswith("http"):
            embed_final.set_image(url=imagen)

        # Enviamos el embed al canal mencionado
        await canal.send(embed=embed_final)
        # Confirmamos en el canal donde se envió el comando
        await ctx.send(f"✅ Ija, ya envié el mensaje a {canal.mention} 💜")
        
    except Exception as e:
        await ctx.send(f"Ija ke dice 💜🤣 Algo falló. \nUso: `darky!embed #canal \"Titulo\" \"Desc\" #Color`")
        print(f"Error: {e}")

# --- 4. ENCENDIDO FINAL ---
if __name__ == "__main__":
    keep_alive() # Mantiene la web activa
    
    # Saca el token de la pestaña Environment de Render
    token_secreto = os.getenv('TOKEN')
    
    if token_secreto:
        bot.run(token_secreto)
    else:
        print("❌ ERROR: No hay variable TOKEN en el panel de Render.")
