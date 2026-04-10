import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# --- 1. CONFIGURACIÓN PARA RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Darky modo inteligente activado 💜"

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
    print(f'¡MimiBot ya despertó y ahora es adivino! 💜🤣')

# --- 3. COMANDO EMBED (CANAL OPCIONAL) ---
@bot.command()
async def embed(ctx, canal: discord.Optional[discord.TextChannel], titulo, descripcion, color, imagen=None):
    try:
        # Si no pusiste canal, usamos el canal donde escribiste el comando
        destino = canal or ctx.channel
        
        color_limpio = color.replace("#", "")
        color_hex = int(color_limpio, 16)

        embed_final = discord.Embed(
            title=titulo,
            description=descripcion,
            color=color_hex
        )

        if imagen:
            embed_final.set_image(url=imagen)

        await destino.send(embed=embed_final)
        
        # Solo avisamos si se envió a OTRO canal para no llenar el chat
        if canal:
            await ctx.send(f"✅ ¡Listo! Mensaje enviado a {canal.mention}")
            
    except Exception as e:
        await ctx.send(f"Ija 💜🤣 Uso: `darky!embed #canal(opcional) \"Tit\" \"Desc\" #Color` ")
        print(f"Error: {e}")

# --- 4. ENCENDIDO ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: No hay variable TOKEN en Render.")
