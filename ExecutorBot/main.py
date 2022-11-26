import os
import discord
import asyncio
import youtube_dl
from discord import app_commands
from datetime import datetime

TOKEN_FILE = open(os.getenv("APPDATA") + "\\ExecutorBot\\token.txt", "r")
TOKEN = TOKEN_FILE.read()
TOKEN_FILE.close()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

yt_dl_opts = {'format': 'bestaudio/best'}
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)

ffmpeg_options = {'options': "-vn"}

prisoners = {}
prisoners_torture = {}


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=696351285032517642))
    print(f"Logged in as {client.user}")
    load_prisoners()
    prison_torture_channel = client.get_channel(1041718989572817007)
    voice_client = await prison_torture_channel.connect()
    loop = asyncio.get_event_loop()
    playlist = await loop.run_in_executor(None, lambda: ytdl.extract_info("https://www.youtube.com/playlist?list=PLJwRPKP3cjL4bQE03Br2rVLdLLLolBPnk", download=False))
    await play_next_song(voice_client, loop, playlist, 0)


@tree.command(name="begnadigen", description="Lasse einen Bürger aus dem Gefängnis frei",
              guild=discord.Object(id=696351285032517642))
async def on_release_command(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.top_role.id != 800983854118469682:
        await interaction.response.send_message(f"Dieser Command kann nur vom Surpreme Court ausgeführt werden!")
        return
    if user.id in prisoners:
        await interaction.response.send_message(f"{user.name} wurde aus dem Gefängnis entlassen")
        del prisoners[user.id]
        save_prisoners()
    else:
        await interaction.response.send_message(f"{user.name} wurde aus dem Folterkeller entlassen")
        del prisoners_torture[user.id]
        save_prisoners()


@tree.command(name="prison", description="Schicke einen Bürger ins Gefängnis",
              guild=discord.Object(id=696351285032517642))
async def on_prison_command(interaction: discord.Interaction, user: discord.Member, reason: str, release_date: str,
                            release_time: str):
    if interaction.user.top_role.id != 800983854118469682:
        await interaction.response.send_message(f"Dieser Command kann nur vom Surpreme Court ausgeführt werden!")
        return
    await interaction.response.send_message(f"{user.name} wurde zu einer Gefängnisstrafe verurteilt! \nGrund: {reason}")
    date_time = datetime.strptime(release_date + " " + release_time, "%d.%m.%Y %H:%M")
    prisoners[user.id] = date_time
    save_prisoners()
    if user.voice is not None:
        prison_channel = client.get_channel(1041423507634000002)
        await user.move_to(prison_channel)


@tree.command(name="folterkeller", description="Schicke einen Bürger in den Folterkeller",
              guild=discord.Object(id=696351285032517642))
async def on_torture_command(interaction: discord.Interaction, user: discord.Member, reason: str, release_date: str,
                             release_time: str):
    if interaction.user.top_role.id != 800983854118469682:
        await interaction.response.send_message(f"Dieser Command kann nur von der Oberrichterin ausgeführt werden!")
        return
    await interaction.response.send_message(f"{user.name} wurde in den Folterkeller geschickt! \nGrund: {reason}")
    date_time = datetime.strptime(release_date + " " + release_time, "%d.%m.%Y %H:%M")
    prisoners_torture[user.id] = date_time
    save_prisoners()
    if user.voice is not None:
        prison_torture_channel = client.get_channel(1041718989572817007)
        await user.move_to(prison_torture_channel)


@client.event
async def on_voice_state_update(user: discord.Member, before, after):
    if user.id in prisoners:
        if datetime.now() >= prisoners[user.id]:
            del prisoners[user.id]
            save_prisoners()
            return
        prison_channel = client.get_channel(1041423507634000002)
        if after.channel is not None and after.channel.id is not prison_channel.id:
            await user.move_to(prison_channel)
            release_date: datetime = prisoners[user.id]
            await user.send("Deine Gefängnisstrafe endet am " + release_date.date().strftime(
                "%d.%m.%Y") + " um " + release_date.time().strftime("%H:%M") + " Uhr!")
    elif user.id in prisoners_torture:
        if datetime.now() >= prisoners_torture[user.id]:
            del prisoners_torture[user.id]
            save_prisoners()
            return
        prison_torture_channel = client.get_channel(1041718989572817007)
        if after.channel is not None and after.channel.id is not prison_torture_channel.id:
            await user.move_to(prison_torture_channel)
            release_date: datetime = prisoners_torture[user.id]
            await user.send("Deine Strafe im Folterkeller endet am " + release_date.date().strftime(
                "%d.%m.%Y") + " um " + release_date.time().strftime("%H:%M") + " Uhr!")


async def play_next_song(voice_client, loop, playlist, playlist_index):
    if playlist_index > (len(playlist['entries']) - 1):
        playlist_index = 0
    song = playlist['entries'][playlist_index]['formats'][0]['url']
    player = discord.FFmpegPCMAudio(song, **ffmpeg_options, executable="C:\\ffmpeg\\bin\\ffmpeg.exe")
    voice_client.play(player, after=lambda ex: loop.create_task(play_next_song(voice_client, loop, playlist, playlist_index + 1)))


def save_prisoners():
    f_prisoners = open(os.getenv("APPDATA") + "\\ExecutorBot\\prison.txt", "w")
    f_prisoners_torture = open(os.getenv("APPDATA") + "\\ExecutorBot\\prison_torture.txt", "w")
    f_prisoners.close()
    f_prisoners_torture.close()
    f_prisoners = open(os.getenv("APPDATA") + "\\ExecutorBot\\prison.txt", "a")
    f_prisoners_torture = open(os.getenv("APPDATA") + "\\ExecutorBot\\prison_torture.txt", "a")
    for prisoner in prisoners:
        print(prisoner)
        release_date = prisoners[prisoner].strftime("%d.%m.%Y %H:%M")
        f_prisoners.write(f"{prisoner}|{release_date}\n")
    for prisoner_torture in prisoners_torture:
        release_date = prisoners_torture[prisoner_torture].strftime("%d.%m.%Y %H:%M")
        f_prisoners_torture.write(f"{prisoner_torture} | {release_date}\n")
    f_prisoners.close()
    f_prisoners_torture.close()


def load_prisoners():
    f_prison = open(os.getenv("APPDATA") + "\\ExecutorBot\\prison.txt", "r")
    for line in f_prison:
        split_line = line.split("|")
        user = split_line[0]
        date_time = datetime.strptime(split_line[1].strip(), "%d.%m.%Y %H:%M")
        prisoners[int(user)] = date_time
    f_prison.close()
    f_prison_torture = open(os.getenv("APPDATA") + "\\ExecutorBot\\prison_torture.txt", "r")
    for line in f_prison_torture:
        split_line = line.split("|")
        user = split_line[0]
        date_time = datetime.strptime(split_line[1].strip(), "%d.%m.%Y %H:%M")
        prisoners_torture[int(user)] = date_time
    f_prison_torture.close()


client.run(TOKEN)