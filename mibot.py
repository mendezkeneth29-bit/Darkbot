emb.set_thumbnail(url=t.display_avatar.url)
    emb.set_footer(text="DarkyBank S.A. | Seguridad y Confianza")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="transferir", description="Envía dinero a otro usuario")
async def transferir(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    aid = str(interaction.user.id)
    if cantidad <= 0 or banco_datos.get(aid, 0) < cantidad:
        return await interaction.response.send_message("❌ Error: Fondos insuficientes.", ephemeral=True)
    banco_datos[aid] -= cantidad
    banco_datos[str(miembro.id)] = banco_datos.get(str(miembro.id), 0) + cantidad
    
    emb = discord.Embed(title="💸 Transferencia Exitosa", color=0x388e3c)
    emb.add_field(name="Remitente", value=interaction.user.mention, inline=True)
    emb.add_field(name="Beneficiario", value=miembro.mention, inline=True)
    emb.add_field(name="Monto", value=f"`$ {cantidad:,}` USD", inline=False)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="regalar", description="Dar dinero (Solo Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def regalar(interaction: discord.Interaction, miembro: discord.Member, cantidad: int):
    mid = str(miembro.id)
    banco_datos[mid] = banco_datos.get(mid, 0) + cantidad
    emb = discord.Embed(title="💎 BONO ADMINISTRATIVO", color=0xf1c40f)
    emb.add_field(name="Usuario", value=miembro.mention, inline=True)
    emb.add_field(name="Monto", value=f"`$ {cantidad:,}` USD", inline=True)
    await interaction.response.send_message(embed=emb)

# --- 7. COMANDOS SOCIALES Y ÚTILES ---

@bot.tree.command(name="roblox", description="Muestra perfil de Roblox")
async def roblox(interaction: discord.Interaction, usuario: str):
    await interaction.response.defer()
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [usuario]}).json()
        uid = r['data'][0]['id']
        thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png").json()
        avatar_url = thumb['data'][0]['imageUrl']
        emb = discord.Embed(title=f"Perfil de {usuario}", url=f"https://www.roblox.com/users/{uid}/profile", color=0x010101)
        emb.set_image(url=avatar_url)
        await interaction.followup.send(embed=emb)
    except: await interaction.followup.send("No encontré al usuario. 🤣")

@bot.tree.command(name="ship", description="Calcula el amor entre dos")
async def ship(interaction: discord.Interaction, m1: discord.Member, m2: discord.Member):
    await interaction.response.defer(); p = random.randint(1, 100)
    av1 = io.BytesIO(await m1.display_avatar.read()); av2 = io.BytesIO(await m2.display_avatar.read())
    i1 = Image.open(av1).convert("RGBA").resize((200, 200)); i2 = Image.open(av2).convert("RGBA").resize((200, 200))
    l = Image.new("RGBA", (500, 200), (0, 0, 0, 0)); l.paste(i1, (0, 0)); l.paste(i2, (300, 0))
    o = io.BytesIO(); l.save(o, format='PNG'); o.seek(0)
    await interaction.followup.send(file=discord.File(o, filename="s.png"), embed=discord.Embed(title=f"💘 Afinidad: {p}%", color=0x010101).set_image(url="attachment://s.png"))

@bot.tree.command(name="avatar", description="Ver avatar de alguien")
async def avatar(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    emb = discord.Embed(title=f"Avatar de {t.name}", color=0x010101).set_image(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="userinfo", description="Información de usuario")
async def userinfo(interaction: discord.Interaction, usuario: Optional[discord.Member] = None):
    t = usuario or interaction.user
    emb = discord.Embed(title=f"Info: {t.name}", color=0x010101)
    emb.add_field(name="ID", value=f"`{t.id}`", inline=True)
    emb.add_field(name="Cuenta Creada", value=f"<t:{int(t.created_at.timestamp())}:D>", inline=True)
    emb.set_thumbnail(url=t.display_avatar.url)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="embed", description="Enviar mensaje embed")
async def embed(interaction: discord.Interaction, titulo: str, descripcion: str):
    await interaction.channel.send(embed=discord.Embed(title=titulo, description=descripcion, color=0x010101))
    await interaction.response.send_message("Mensaje enviado. 💜", ephemeral=True)

@bot.tree.command(name="delete", description="Limpiar mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete(interaction: discord.Interaction, cantidad: int):
    await interaction.channel.purge(limit=cantidad)
    await interaction.response.send_message(f"Borrados {cantidad}. 💜", ephemeral=True)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('TOKEN'))
