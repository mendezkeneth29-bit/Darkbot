# --- AFK ---
afk_users = {}

@bot.tree.command(name="afk")
async def afk(i, motivo:str="Ausente"):
    afk_users[str(i.user.id)] = motivo
    e = discord.Embed(title="MODO AFK ACTIVADO", color=COLOR)
    e.description = f"{i.user.mention} ahora está AFK\nMotivo: {motivo}"
    await i.response.send_message(embed=e)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if str(message.author.id) in afk_users:
        del afk_users[str(message.author.id)]
        await message.channel.send(f"{message.author.mention} ya no está AFK")

    for user in message.mentions:
        if str(user.id) in afk_users:
            await message.channel.send(f"{user.name} está AFK: {afk_users[str(user.id)]}")

    await bot.process_commands(message)

# --- CLIMA (BÁSICO) ---
@bot.tree.command(name="clima")
async def clima(i, ciudad:str):
    try:
        r = requests.get(f"https://wttr.in/{ciudad}?format=3").text
        e = discord.Embed(title="CLIMA", description=r, color=COLOR)
        await i.response.send_message(embed=e)
    except:
        await i.response.send_message("Error")

# --- GOOGLE ---
@bot.tree.command(name="google")
async def google(i, busqueda:str):
    link = f"https://www.google.com/search?q={busqueda.replace(' ','+')}"
    e = discord.Embed(title="BÚSQUEDA GOOGLE", color=COLOR)
    e.description = f"[Resultados aquí]({link})"
    await i.response.send_message(embed=e)

# --- YOUTUBE ---
@bot.tree.command(name="youtube")
async def youtube(i, busqueda:str):
    link = f"https://www.youtube.com/results?search_query={busqueda.replace(' ','+')}"
    e = discord.Embed(title="YOUTUBE", color=COLOR)
    e.description = f"[Ver resultados]({link})"
    await i.response.send_message(embed=e)

# --- CALCULADORA ---
@bot.tree.command(name="calc")
async def calc(i, operacion:str):
    try:
        resultado = eval(operacion)
        e = discord.Embed(title="CALCULADORA", color=COLOR)
        e.description = f"{operacion} = {resultado}"
        await i.response.send_message(embed=e)
    except:
        await i.response.send_message("Error en cálculo")

# --- ENCRIPTAR ---
@bot.tree.command(name="encrypt")
async def encrypt(i, texto:str):
    encriptado = texto[::-1]
    await i.response.send_message(embed=discord.Embed(title="ENCRIPTADO", description=encriptado, color=COLOR))

# --- DESENCRIPTAR ---
@bot.tree.command(name="decrypt")
async def decrypt(i, texto:str):
    desencriptado = texto[::-1]
    await i.response.send_message(embed=discord.Embed(title="DESENCRIPTADO", description=desencriptado, color=COLOR))

# --- DADO AVANZADO ---
@bot.tree.command(name="dados")
async def dados(i, cantidad:int):
    resultados = [random.randint(1,6) for _ in range(cantidad)]
    await i.response.send_message(embed=discord.Embed(title="DADOS", description=str(resultados), color=COLOR))

# --- PASSWORD ---
@bot.tree.command(name="password")
async def password(i):
    chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789"
    pw="".join(random.choice(chars) for _ in range(12))
    await i.response.send_message(embed=discord.Embed(title="PASSWORD", description=pw, color=COLOR))

# --- COLOR RANDOM ---
@bot.tree.command(name="color")
async def color(i):
    col=random.randint(0,0xffffff)
    e=discord.Embed(title="COLOR RANDOM", color=col)
    e.description=f"Hex: #{col:06x}"
    await i.response.send_message(embed=e)

# --- FRASE ---
@bot.tree.command(name="frase")
async def frase(i):
    frases=["Sigue intentando","No te rindas","Modo pro activado"]
    await i.response.send_message(embed=discord.Embed(title="FRASE",description=random.choice(frases),color=COLOR))

# --- GATO ---
@bot.tree.command(name="gato")
async def gato(i):
    r=requests.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"]
    e=discord.Embed(title="GATO",color=COLOR)
    e.set_image(url=r)
    await i.response.send_message(embed=e)

# --- PERRO ---
@bot.tree.command(name="perro")
async def perro(i):
    r=requests.get("https://dog.ceo/api/breeds/image/random").json()["message"]
    e=discord.Embed(title="PERRO",color=COLOR)
    e.set_image(url=r)
    await i.response.send_message(embed=e)

# --- CHUCK NORRIS ---
@bot.tree.command(name="chuck")
async def chuck(i):
    r=requests.get("https://api.chucknorris.io/jokes/random").json()["value"]
    await i.response.send_message(embed=discord.Embed(title="CHISTE",description=r,color=COLOR))

# --- TOP DINERO ---
@bot.tree.command(name="top")
async def top(i):
    top_users=sorted(cartera.items(),key=lambda x:x[1],reverse=True)[:5]
    texto="\n".join([f"<@{u}> - ${m}" for u,m in top_users])
    await i.response.send_message(embed=discord.Embed(title="TOP DINERO",description=texto,color=COLOR))

# --- SUGERENCIA ---
@bot.tree.command(name="sugerencia")
async def sugerencia(i,texto:str):
    e=discord.Embed(title="SUGERENCIA",description=texto,color=COLOR)
    e.set_footer(text=f"Por {i.user}")
    await i.response.send_message(embed=e)

# --- ENCUESTA ---
class PollView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.si=0
        self.no=0

    @discord.ui.button(label="Sí", style=discord.ButtonStyle.green)
    async def si_btn(self, interaction, button):
        self.si+=1
        await interaction.response.send_message("Votaste Sí",ephemeral=True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_btn(self, interaction, button):
        self.no+=1
        await interaction.response.send_message("Votaste No",ephemeral=True)

@bot.tree.command(name="encuesta")
async def encuesta(i,pregunta:str):
    await i.response.send_message(embed=discord.Embed(title="ENCUESTA",description=pregunta,color=COLOR),view=PollView())

# --- RECORDATORIO ---
@bot.tree.command(name="recordatorio")
async def recordatorio(i,seg:int,mensaje:str):
    await i.response.send_message("Recordatorio creado")
    await discord.utils.sleep_until(discord.utils.utcnow()+discord.timedelta(seconds=seg))
    await i.user.send(mensaje)

# --- RANDOM USER ---
@bot.tree.command(name="randomuser")
async def randomuser(i):
    user=random.choice(i.guild.members)
    await i.response.send_message(embed=discord.Embed(title="USUARIO RANDOM",description=user.mention,color=COLOR))
