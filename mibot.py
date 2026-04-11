import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import io
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING (RENDER) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bank Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BASE DE DATOS TEMPORAL ---
# Nota: Si Render se reinicia, el banco se vacía. 
# En el futuro podrías usar un archivo JSON o base de datos.
banco_datos = {}

# --- 3. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Sistema bancario sincronizado!")

    # --- SISTEMA DE PAGO POR MENSAJE ---
    async def on_message(self, message):
        if message.author.bot: return # No pagarle a otros bots
        
        user_id = str(message.author.id)
        if user_id not in banco_datos:
            banco_datos[user_id] = 0
            
        banco_datos[user_id] += 5 # ¡Aquí están tus 5 dólares!
        
        await self.process_commands(message)

bot = MyBot()

# --- 4. COMANDOS SLASH ---

@bot.tree.command(name="banco", description="Gestiona tu cuenta bancaria de DarkyBot")
@app_commands.describe(usuario="Mira el banco de otro (opcional)")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    user_id = str(target.id)
    
    # Si el usuario no existe en el banco, lo creamos
    if user_id not in banco_datos:
        banco_datos[user_id] = 0
        
    saldo = banco_datos[user_id]
    
    emb = discord.Embed(
        title=f"🏦 Banco Central de {target.display_name}",
        description=f"Actualmente tienes: **${saldo}** dólares",
        color=0x010101
    )
    emb.set_thumbnail(url=target.display_avatar.url)
    emb.set_footer(text="Cada mensaje te da $5. ¡Ok mañana! 💜🤣")
    
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="transferir", description="Pásale dinero a un amigo")
@app_commands.describe(miembro="A quién le das dinero", cantidad="Cuánto dinero enviar")
async def transferir(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    autor_id = str(interaction.user.id)
    destino_id = str(miembro.id)
    
    if cantidad <= 0:
        return await interaction.response.send_message("No puedes enviar aire, ija. 🤣", ephemeral=True)
    
    saldo_autor = banco_datos.get(autor_id, 0)
    
    if saldo_autor < cantidad:
        return await interaction.response.send_message("Estás pobre, no tienes suficiente dinero. 💜🤣", ephemeral=True)
    
    # Proceso de transferencia
    banco_datos[autor_id] -= cantidad
    banco_datos[destino_id] = banco_datos.get(destino_id, 0) + cantidad
    
    await interaction.response.send_message(f"✅ Has transferido **${cantidad}** a {miembro.mention}. ¡YIPIEEE!")

@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        url_user = "https://users.roblox.com/v1/usernames/users"
        res_user = requests.post(url_user, json={"usernames": [usuario], "excludeBannedUsers": False}, headers=headers).json()
        if 'data' in res_user and res_user['data']:
            u = res_user['data'][0]
            uid = u['id']
            res_thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png", headers=headers).json()
            foto = res_thumb['data'][0]['imageUrl'] if 'data' in res_thumb else ""
            emb = discord.Embed(title=f"Perfil de {u['displayName']}", url=f"https://www.roblox.com/users/{uid}/profile", color=0x010101)
            if foto: emb.set_image(url=foto)
            await interaction.followup.send(embed=emb)
        else:
            await interaction.followup.send(f"❌ No encontré a `{usuario}`.")
    except:
        await interaction.followup.send("❌ Error de Roblox.")

# --- 5. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
