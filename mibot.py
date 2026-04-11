import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
import random
import io
from PIL import Image
from flask import Flask
from threading import Thread
from typing import Optional

# --- 1. HOSTING PARA RENDER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Darky Bot Ultimate Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BASE DE DATOS DEL BANCO ---
banco_datos = {}

# --- 3. CONFIGURACIÓN DEL BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.message_content = True
        super().__init__(command_prefix="darky!", intents=intents)

    async def setup_hook(self):
        # Sincroniza todos los comandos slash con Discord
        await self.tree.sync()
        print("¡Todos los comandos sincronizados con éxito! 💜🤣")

    # SISTEMA DE PAGO POR MENSAJE ($5)
    async def on_message(self, message):
        if message.author.bot: return
        
        user_id = str(message.author.id)
        if user_id not in banco_datos:
            banco_datos[user_id] = 0
            
        banco_datos[user_id] += 5 # Pago por actividad
        
        await self.process_commands(message)

bot = MyBot()

# --- 4. COMANDOS DE BANCO ---

@bot.tree.command(name="banco", description="Mira tu saldo bancario")
@app_commands.describe(usuario="Mira el saldo de alguien más")
async def banco(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    user_id = str(target.id)
    saldo = banco_datos.get(user_id, 0)
    
    emb = discord.Embed(title=f"🏦 Banco de {target.display_name}", description=f"Saldo actual: **${saldo}**", color=0x010101)
    emb.set_thumbnail(url=target.display_avatar.url)
    emb.set_footer(text="Ganas $5 por cada mensaje que envías. 💜")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="transferir", description="Envía dinero a un amigo")
@app_commands.describe(miembro="A quién le das dinero", cantidad="Monto a enviar")
async def transferir(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    autor_id = str(interaction.user.id)
    if cantidad <= 0:
        return await interaction.response.send_message("Ija ke dice... pon una cantidad válida. 🤣", ephemeral=True)
    
    saldo_autor = banco_datos.get(autor_id, 0)
    if saldo_autor < cantidad:
        return await interaction.response.send_message("No tienes dinero suficiente, estás pobre. 💜🤣", ephemeral=True)
    
    banco_datos[autor_id] -= cantidad
    banco_datos[str(miembro.id)] = banco_datos.get(str(miembro.id), 0) + cantidad
    await interaction.response.send_message(f"✅ Transferencia exitosa: Envaste **${cantidad}** a {miembro.mention}. ¡Ok mañana!")

# --- 5. COMANDOS SOCIALES Y ENTRETENIMIENTO ---

@bot.tree.command(name="ship", description="Calcula el amor entre dos personas")
@app_commands.describe(miembro1="Primer miembro", miembro2="Segundo miembro")
async def ship(interaction: discord.Interaction, miembro1: discord.Member, miembro2: discord.Member):
    await interaction.response.defer()
    porcentaje = random.randint(1, 100)
    
    # Procesamiento de imagen
    av1 = io.BytesIO(await miembro1.display_avatar.read())
    av2 = io.BytesIO(await miembro2.display_avatar.read())
    img1 = Image.open(av1).convert("RGBA").resize((200, 200))
    img2 = Image.open(av2).convert("RGBA").resize((200, 200))
    
    lienzo = Image.new("RGBA", (500, 200), (0, 0, 0, 0))
    lienzo.paste(img1, (0, 0))
    lienzo.paste(img2, (300, 0))
    
    output = io.BytesIO()
    lienzo.save(output, format='PNG')
    output.seek(0)
    archivo = discord.File(output, filename="ship.png")
    
    emb = discord.Embed(title=f"💘 Nivel de Amor: {porcentaje}%", color=0x010101)
    emb.set_image(url="attachment://ship.png")
    await interaction.followup.send(file=archivo, embed=emb)

@bot.tree.command(name="roblox", description="Busca un perfil de Roblox")
@app_commands.describe(usuario="Nombre de usuario exacto")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario], "excludeBannedUsers": False}, headers=headers).json()
        if 'data' in r and r['data']:
            u = r['data'][0]
            uid = u['id']
            thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png", headers=headers).json()
            foto = thumb['data'][0]['imageUrl'] if 'data' in thumb else ""
            
            emb = discord.Embed(title=f"Perfil de {u['displayName']}", url=f"https://www.roblox.com/users/{uid}/profile", color=0x010101)
            emb.add_field(name="Usuario", value=f"@{u['name']}")
            emb.add_field(name="ID", value=f"`{uid}`")
            if foto: emb.set_image(url=foto)
            await interaction.followup.send(embed=emb)
        else:
            await interaction.followup.send("No encontré a ese usuario.")
    except:
        await interaction.followup.send("Error conectando con la API de Roblox.")

@bot.tree.command(name="avatar", description="Muestra el avatar de un usuario")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    emb = discord.Embed(title=f"Avatar de {target.name}", color=0x010101)
    emb.set_image(url=target.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="userinfo", description="Muestra información del miembro")
async def userinfo(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    target = usuario or interaction.user
    emb = discord.Embed(title=f"Info de {target.name}", color=0x010101)
    emb.set_thumbnail(url=target.display_avatar.url)
    emb.add_field(name="ID", value=f"`{target.id}`", inline=True)
    emb.add_field(name="Creación", value=target.created_at.strftime("%d/%m/%Y"), inline=True)
    await interaction.response.send_message(embed=emb)

# --- 6. COMANDOS DE MODERACIÓN Y UTILIDAD ---

@bot.tree.command(name="embed", description="Crea un mensaje embed personalizado")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str, color: Optional[str] = None):
    try: c = int(color.replace("#", ""), 16) if color else 0x010101
    except: c = 0x010101
    await interaction.channel.send(embed=discord.Embed(title=titulo, description=descripcion, color=c))
    await interaction.response.send_message("Mensaje enviado correctamente. 💜", ephemeral=True)

@bot.tree.command(name="delete", description="Borra una cantidad de mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"🧹 Se han borrado {cantidad} mensajes.", ephemeral=True)

# --- 7. INICIO DEL BOT ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    bot.run(token)
