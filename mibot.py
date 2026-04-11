emb.add_field(name="💰 Total", value=f"**${(c+b):,}**", inline=False)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="work", description="Trabaja duro")
async def work(interaction: discord.Interaction):
    pago = random.randint(800, 2500)
    uid = str(interaction.user.id)
    cartera_datos[uid] = cartera_datos.get(uid, 0) + pago
    trabajos = ["Programador de Virus", "Dueño de Casino", "Mercenario", "Político Corrupto"]
    await interaction.response.send_message(f"💼 Trabajaste de **{random.choice(trabajos)}** y ganaste **${pago:,}**.")

@bot.tree.command(name="crime", description="Comete un crimen (Riesgoso)")
async def crime(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if random.random() > 0.4:
        ganancia = random.randint(3000, 7000)
        cartera_datos[uid] = cartera_datos.get(uid, 0) + ganancia
        await interaction.response.send_message(f"🔫 ¡Éxito! Robaste un banco y ganaste **${ganancia:,}**.")
    else:
        multa = random.randint(1000, 3000)
        cartera_datos[uid] = max(0, cartera_datos.get(uid, 0) - multa)
        await interaction.response.send_message(f"👮 ¡La policía te atrapó! Pagaste una multa de **${multa:,}**.")

@bot.tree.command(name="deposito", description="Mueve dinero al banco")
async def deposito(interaction: discord.Interaction, cantidad: int):
    uid = str(interaction.user.id)
    if cantidad <= 0 or cartera_datos.get(uid, 0) < cantidad:
        return await interaction.response.send_message("❌ Cantidad inválida.", ephemeral=True)
    cartera_datos[uid] -= cantidad
    banco_datos[uid] = banco_datos.get(uid, 0) + cantidad
    await interaction.response.send_message(f"✅ Guardaste **${cantidad:,}** en el banco.")

@bot.tree.command(name="retirar", description="Saca dinero del banco")
async def retirar(interaction: discord.Interaction, cantidad: int):
    uid = str(interaction.user.id)
    if cantidad <= 0 or banco_datos.get(uid, 0) < cantidad:
        return await interaction.response.send_message("❌ No tienes esa cantidad.", ephemeral=True)
    banco_datos[uid] -= cantidad
    cartera_datos[uid] = cartera_datos.get(uid, 0) + cantidad
    await interaction.response.send_message(f"✅ Sacaste **${cantidad:,}** del banco.")

@bot.tree.command(name="rob", description="Roba a otro usuario")
async def rob(interaction: discord.Interaction, victima: discord.Member):
    uid, vid = str(interaction.user.id), str(victima.id)
    v_cartera = cartera_datos.get(vid, 0)
    if v_cartera < 500: return await interaction.response.send_message("❌ Esa persona es muy pobre.")
    
    if random.random() > 0.5:
        robo = random.randint(100, v_cartera // 2)
        cartera_datos[vid] -= robo
        cartera_datos[uid] = cartera_datos.get(uid, 0) + robo
        await interaction.response.send_message(f"😈 ¡Le robaste **${robo:,}** a {victima.mention}!")
    else:
        await interaction.response.send_message(f"🤡 Intentaste robar a {victima.mention} pero te dio una paliza.")

# --- 6. COMANDOS DE INTERACCIÓN SOCIAL (ACCIONES) ---

@bot.tree.command(name="kiss", description="Dale un beso a alguien")
async def kiss(interaction: discord.Interaction, usuario: discord.Member):
    emb = discord.Embed(description=f"💋 **{interaction.user.name}** besó a **{usuario.name}**", color=COLOR_BOT)
    emb.set_image(url="https://i.waifu.pics/o~F_V_D.gif") # Placeholder GIF
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="hug", description="Dale un abrazo a alguien")
async def hug(interaction: discord.Interaction, usuario: discord.Member):
    emb = discord.Embed(description=f"🫂 **{interaction.user.name}** abrazó a **{usuario.name}**", color=COLOR_BOT)
    emb.set_image(url="https://i.waifu.pics/YpE~PjI.gif")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="slap", description="Dale una bofetada a alguien")
async def slap(interaction: discord.Interaction, usuario: discord.Member):
    emb = discord.Embed(description=f"🖐️ **{interaction.user.name}** abofeteó a **{usuario.name}**", color=COLOR_BOT)
    await interaction.response.send_message(embed=emb)

# --- 7. COMANDOS DE DIVERSIÓN Y UTILIDAD ---

@bot.tree.command(name="8ball", description="Pregúntale al bot")
async def eightball(interaction: discord.Interaction, pregunta: str):
    respuestas = ["Sí", "No", "Tal vez", "Definitivamente", "Ni lo sueñes", "Pregunta luego"]
    await interaction.response.send_message(f"🎱 **Pregunta:** {pregunta}\n**Respuesta:** {random.choice(respuestas)}")

@bot.tree.command(name="avatar", description="Muestra el avatar de alguien")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    emb = discord.Embed(title=f"Avatar de {t.name}", color=COLOR_BOT)
    emb.set_image(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="server", description="Info del servidor")
async def server(interaction: discord.Interaction):
    g = interaction.guild
    emb = discord.Embed(title=f"🏰 {g.name}", color=COLOR_BOT)
    emb.add_field(name="Miembros", value=g.member_count)
    emb.add_field(name="ID", value=g.id)
    emb.set_thumbnail(url=g.icon.url if g.icon else None)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="clear", description="Limpiar mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"✅ Se han borrado {cantidad} mensajes.", ephemeral=True)

# --- 8. EJECUCIÓN ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: TOKEN NO ENCONTRADO.")
