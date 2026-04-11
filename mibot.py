import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
import google.generativeai as genai
from flask import Flask
from threading import Thread

# --- 1. HOSTING (RENDER) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. CONFIGURACIÓN IA ---
# Usando tu nueva key directamente
genai.configure(api_key="AIzaSyCbgKH1WXr52AumroH7jZK_Le7fa32XOFY")

def generar_ia(texto):
    # Intentamos con varios modelos por si uno falla
    for modelo_nombre in ['gemini-1.5-flash', 'gemini-pro']:
        try:
            model = genai.GenerativeModel(modelo_nombre)
            response = model.generate_content(f"Responde corto: {texto}")
            return response.text
        except:
            continue
    return "No pude pensar la respuesta, ija. Intenta de nuevo."

# --- 3. BOT CORE ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        # Sincroniza los comandos de "/" para que aparezcan
        await self.tree.sync()
        print("Comandos slash listos.")

bot = MyBot()

# --- 4. COMANDOS ---

@bot.tree.command(name="sayme", description="Habla con la IA")
async def sayme(interaction: discord.Interaction, pregunta: str):
    await interaction.response.defer()
    respuesta = generar_ia(pregunta)
    emb = discord.Embed(description=f"**Tú:** {pregunta}\n**Darky:** {respuesta}", color=0x010101)
    await interaction.followup.send(embed=emb)

@bot.tree.command(name="delete", description="Borra mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Borrados {cantidad} mensajes.", ephemeral=True)

@bot.tree.command(name="roblox", description="Busca usuario")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    # Buscador básico funcional
    r = requests.get(f"https://users.roblox.com/v1/users/search?keyword={usuario}&limit=1").json()
    if 'data' in r and r['data']:
        u = r['data'][0]
        emb = discord.Embed(title=f"Perfil de {u['displayName']}", url=f"https://www.roblox.com/users/{u['id']}/profile", color=0x010101)
        await interaction.followup.send(embed=emb)
    else:
        await interaction.followup.send("No lo hallé.")

@bot.tree.command(name="embed", description="Crea un embed")
async def embed(interaction: discord.Interaction, titulo: str, desc: str, color: str = "010101"):
    try: c = int(color.replace("#",""), 16)
    except: c = 0x010101
    emb = discord.Embed(title=titulo, description=desc, color=c)
    await interaction.channel.send(embed=emb)
    await interaction.response.send_message("Hecho", ephemeral=True)

# --- 5. IGNICIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    bot.run(token)
