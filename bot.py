import random
import re
import discord
from discord import app_commands
from discord.ext import commands
from discord import Interaction
import sys
import os
import requests
import yt_dlp
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
from googleapiclient.discovery import build
from discord.ui import Button, View


api_key = "" #Google API key https://console.cloud.google.com/projectselector2/apis/library/youtube.googleapis.com
#you can replace it with youtube-search-python

youtube = build('youtube', 'v3', developerKey=api_key)

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

bot.remove_command("help")

SPOTIPY_CLIENT_ID = '' #https://developer.spotify.com/documentation/web-api

SPOTIPY_CLIENT_SECRET = '' 

# Authentification avec Spotipy (en mode client_credentials)
client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)

sp = Spotify(client_credentials_manager=client_credentials_manager)

DISCORD_TOKEN = '' #https://discord.com/developers/applications

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await bot.tree.sync()
    
    await bot.change_presence(activity=discord. Activity(type=discord.ActivityType.listening, name='rien ...'))


@bot.command(name="disconnect")
async def disconnect(ctx):
    if ctx.author.id == 1012039502287622244:
        try:
            print("Déconnexion en cours...")
            await bot.close()
            sys.exit
        except:
            print("Erreur...")

@bot.tree.command(name="play", description="play")
async def play(interaction: Interaction, url: str):
    if "youtube.com/watch" in url or "youtu.be" in url:
        await interaction.response.defer(thinking=True)
        await playyt(interaction, url)
    elif "open.spotify.com" in url:
        await interaction.response.defer(thinking=True)
        await playspotify(interaction, url)
    elif "deezer.com" in url or "deezer.page.link" in url:
        await interaction.response.defer(thinking=True)
        await playdeezer(interaction, url)
    else:
        await interaction.response.send_message("Invalid URL. Please provide a valid YouTube or Spotify URL.", ephemeral=True)

@bot.tree.command(name="stop", description="stop")
async def stop(interaction: Interaction):
    voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_playing():
        voice.stop()
        em1 = discord.Embed(
            title="Music Stopped",
            color=interaction.user.color
        )
        await interaction.response.send_message(embed=em1,ephemeral=True)
    else:
        await interaction.response.send_message("No music is currently playing.", ephemeral=True)

@bot.tree.command(name="pause", description="pause")
async def pause(interaction: Interaction):
    voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_playing():
        voice.pause()
        em1 = discord.Embed(
            title="Music Paused",
            color=interaction.user.color
        )
        await interaction.response.send_message(embed=em1,ephemeral=True)
    else:
        await interaction.response.send_message("No music is currently playing.", ephemeral=True)

@bot.tree.command(name="resume", description="resume")
async def resume(interaction: Interaction):
    voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice and voice.is_paused():
        voice.resume()
        em1 = discord.  Embed(
            title="Music Resumed",
            color=interaction.user.color
        )
        await interaction.response.send_message(embed=em1,ephemeral=True)
    else:
        await interaction.response.send_message("No music is currently playing.", ephemeral=True)

async def playyt(interaction: Interaction, url: str):
    # Vérifiez si une chanson est déjà en cours de lecture
    voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    
    # Si une chanson est déjà en cours, arrêtez-la
    if voice and voice.is_playing():
        voice.stop()

    em6 = discord.Embed(
        title="Downloading Youtube Music",
        description=f'{url}\n\nPlease wait for paimon to setup the music you provide.\nMusic provided by {interaction.user.mention}',
        color=interaction.user.color
    )
    await interaction.edit_original_response(embed=em6)

    ydl_opts = {
        'format': 'bestaudio/best',
        'username': 'oauth2',
        'password': '',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '196',
        }],
        # 'download_archive': 'downloaded_songs.txt'  # Pour ne pas télécharger deux fois la même chanson
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, "song.mp3")

    # Obtenez le canal vocal de l'utilisateur qui a exécuté la commande
    user_voice_channel = interaction.user.voice.channel if interaction.user.voice else None

    if user_voice_channel:
        voice_channel = user_voice_channel
    else:
        # Si l'utilisateur n'est pas dans un canal vocal, essayez de rejoindre un canal vocal occupé
        occupied_voice_channels = [channel for channel in interaction.guild.voice_channels if channel.members]
        if occupied_voice_channels:
            voice_channel = random.choice(occupied_voice_channels)
        else:
            # Sinon, rejoignez un canal vocal aléatoire
            voice_channel = random.choice(interaction.guild.voice_channels)

    # Connectez-vous au canal vocal
    if not voice:
        voice_channel = await voice_channel.connect()
    else:
        await voice.move_to(voice_channel)

    # Jouez la musique
    voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    
    def after_playing(error):
        # Vérifiez si le bot doit se déconnecter
        if error:
            print(f"Error occurred: {error}")
        
        # Déconnecte le bot si personne n'est dans le canal
        asyncio.run_coroutine_threadsafe(interaction.delete_original_response(), bot.loop)
        asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord. Activity(type=discord.ActivityType.listening, name='rien ...')), bot.loop)
        if len(voice.channel.members) == 1:  # Le bot lui-même
            asyncio.run_coroutine_threadsafe(voice.disconnect(), bot.loop)
    source = discord.FFmpegPCMAudio("song.mp3")
    volume = discord.PCMVolumeTransformer(source, volume=0.75)
    voice.play(volume, after=after_playing)

    em1 = discord.Embed(
        title="Now Listening Youtube Music",
        description=f'{url}\n\nMusic provided by {interaction.user.mention} ',
        color=interaction.user.color
    )
    
    videoID = re.search(r'(?:v=|\/|^)([0-9A-Za-z_-]{11})(?:\?|&|$)', url).group(1) #normalement ca marche
    em1.set_thumbnail(url=f'https://img.youtube.com/vi/{videoID}/default.jpg')
    await interaction.edit_original_response(embed=em1,view=PlayView(interaction))
    await bot.change_presence(activity=discord. Activity(type=discord.ActivityType.listening, name=f'Youtube video'))
    track = {
        'url': url,
        'youtube': True,
        'image': f'https://img.youtube.com/vi/{videoID}/default.jpg'
        }
    
async def playspotify(interaction: Interaction, url: str):
    # Vérifiez si une chanson est déjà en cours de lecture
    voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    
    # Si une chanson est déjà en cours, arrêtez-la
    if voice and voice.is_playing():
        voice.stop()
    
    em6 = discord.Embed(
        title="Seaching Youtube Music",
        description=f'{url}\n\nPlease wait for paimon to setup the music you provide.\nMusic provided by {interaction.user.mention}',
        color=interaction.user.color
    )
    await interaction.edit_original_response(embed=em6)
    
    track = sp.track(url)
    track_name = track['name']
    artist_name = track['artists'][0]['name']
    
    url = get_video_url(track_name+" "+artist_name)
    
    if url == None:
        await interaction.edit_original_response(content="Video introuvable... :cry:",embed=None)
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        asyncio.wait(1)
    
    
    em6 = discord.Embed(
        title="Downloading Youtube Music",
        description=f'{url}\n\nPlease wait for paimon to setup the music you provide.\nMusic provided by {interaction.user.mention}',
        color=interaction.user.color
    )
    await interaction.edit_original_response(embed=em6)

    ydl_opts = {
        'format': 'bestaudio/best',
        'username': 'oauth2',
        'password': '',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '196',
        }],
        # 'download_archive': 'downloaded_songs.txt'  # Pour ne pas télécharger deux fois la même chanson
    }
    
    await asyncio.get_event_loop().run_in_executor(None, yt_dlp.YoutubeDL(ydl_opts).download, [url])

    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, "song.mp3")

    # Obtenez le canal vocal de l'utilisateur qui a exécuté la commande
    user_voice_channel = interaction.user.voice.channel if interaction.user.voice else None

    if user_voice_channel:
        voice_channel = user_voice_channel
    else:
        # Si l'utilisateur n'est pas dans un canal vocal, essayez de rejoindre un canal vocal occupé
        occupied_voice_channels = [channel for channel in interaction.guild.voice_channels if channel.members]
        if occupied_voice_channels:
            voice_channel = random.choice(occupied_voice_channels)
        else:
            # Sinon, rejoignez un canal vocal aléatoire
            voice_channel = random.choice(interaction.guild.voice_channels)

    # Connectez-vous au canal vocal
    if not voice:
        voice_channel = await voice_channel.connect()
    else:
        await voice.move_to(voice_channel)

    # Jouez la musique
    voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    
    def after_playing(error):
        # Vérifiez si le bot doit se déconnecter
        if error:
            print(f"Error occurred: {error}")
        
        # Déconnecte le bot si personne n'est dans le canal
        asyncio.run_coroutine_threadsafe(interaction.delete_original_response(), bot.loop)
        asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord. Activity(type=discord.ActivityType.listening, name='rien ...')), bot.loop)
        if len(voice.channel.members) == 1:  # Le bot lui-même
            asyncio.run_coroutine_threadsafe(voice.disconnect(), bot.loop)
    source = discord.FFmpegPCMAudio("song.mp3")
    volume = discord.PCMVolumeTransformer(source, volume=0.75)
    voice.play(volume, after=after_playing)

    spotify_track_url = track['external_urls']['spotify']
    em1 = discord.Embed(
        title="Now Listening Spotify Music",
        description=f'{spotify_track_url}\n\nMusic provided by {interaction.user.mention}',
        color=interaction.user.color
    )
    em1.set_thumbnail(url=track['album']['images'][2]['url']) #[2] pour l'image 64x64
    await interaction.edit_original_response(embed=em1,view=PlayView(interaction))
    await bot.change_presence(activity=discord. Activity(type=discord.ActivityType.listening, name=f'{track_name} - {artist_name}'))

async def playdeezer(interaction: Interaction, url: str):
    # Vérifiez si une chanson est déjà en cours de lecture
    voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    
    # Si une chanson est déjà en cours, arrêtez-la
    if voice and voice.is_playing():
        voice.stop()

    em6 = discord.Embed(
        title="Seaching Youtube Music",
        description=f'{url}\n\nPlease wait for paimon to setup the music you provide.\nMusic provided by {interaction.user.mention}',
        color=interaction.user.color
    )
    await interaction.edit_original_response(embed=em6)
    
    # Resolve short URL if necessary
    if "deezer.page.link" in url:
        response = requests.get(url, allow_redirects=False)
        if 'Location' in response.headers:
            url = response.headers['Location']

    track_id = url.split('/')[-1]
    track = requests.get(f"https://api.deezer.com/track/{track_id}").json()
    track_name = track['title']
    artist_name = track['artist']['name']
    
    url = get_video_url(track_name+" "+artist_name)
    
    if url == None:
        await interaction.edit_original_response(content="Video introuvable... :cry:",embed=None)
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        asyncio.wait(1)
    
    
    em6 = discord.Embed(
        title="Downloading Youtube Music",
        description=f'{url}\n\nPlease wait for paimon to setup the music you provide.\nMusic provided by {interaction.user.mention}',
        color=interaction.user.color
    )
    await interaction.edit_original_response(embed=em6)

    ydl_opts = {
        'format': 'bestaudio/best',
        'username': 'oauth2',
        'password': '',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '196',
        }],
        # 'download_archive': 'downloaded_songs.txt'  # Pour ne pas télécharger deux fois la même chanson
    }
    
    await asyncio.get_event_loop().run_in_executor(None, yt_dlp.YoutubeDL(ydl_opts).download, [url])

    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, "song.mp3")

    # Obtenez le canal vocal de l'utilisateur qui a exécuté la commande
    user_voice_channel = interaction.user.voice.channel if interaction.user.voice else None

    if user_voice_channel:
        voice_channel = user_voice_channel
    else:
        # Si l'utilisateur n'est pas dans un canal vocal, essayez de rejoindre un canal vocal occupé
        occupied_voice_channels = [channel for channel in interaction.guild.voice_channels if channel.members]
        if occupied_voice_channels:
            voice_channel = random.choice(occupied_voice_channels)
        else:
            # Sinon, rejoignez un canal vocal aléatoire
            voice_channel = random.choice(interaction.guild.voice_channels)

    # Connectez-vous au canal vocal
    if not voice:
        voice_channel = await voice_channel.connect()
    else:
        await voice.move_to(voice_channel)

    # Jouez la musique
    voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    
    def after_playing(error):
        # Vérifiez si le bot doit se déconnecter
        if error:
            print(f"Error occurred: {error}")
        
        # Déconnecte le bot si personne n'est dans le canal
        asyncio.run_coroutine_threadsafe(interaction.delete_original_response(), bot.loop)
        asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord. Activity(type=discord.ActivityType.listening, name='rien ...')), bot.loop)
        if len(voice.channel.members) == 1:  # Le bot lui-même
            asyncio.run_coroutine_threadsafe(voice.disconnect(), bot.loop)
    source = discord.FFmpegPCMAudio("song.mp3")
    volume = discord.PCMVolumeTransformer(source, volume=0.75)
    voice.play(volume, after=after_playing)

    deezer_track_url = track['link']
    em1 = discord.Embed(
        title="Now Listening Deezer Music",
        description=f'{deezer_track_url}\n\nMusic provided by {interaction.user.mention}',
        color=interaction.user.color
    )
    em1.set_thumbnail(url=track['album']['cover_small'])
    await interaction.edit_original_response(embed=em1,view=PlayView(interaction))
    await bot.change_presence(activity=discord. Activity(type=discord.ActivityType.listening, name=f'{track_name} - {artist_name}'))
    

async def playspotifydemo(interaction: Interaction, url: str):
    
    # Get track information
    track_info = sp.track(url)
    track_name = track_info['name']
    artist_name = track_info['artists'][0]['name']
    audio_preview_url = track_info['preview_url']  # This is a 30-second preview URL

    if audio_preview_url:
        # Prepare to play the audio preview
        user_voice_channel = interaction.user.voice.channel if interaction.user.voice else None

        if user_voice_channel:
            voice_channel = user_voice_channel
        else:
            occupied_voice_channels = [channel for channel in interaction.guild.voice_channels if channel.members]
            if occupied_voice_channels:
                voice_channel = random.choice(occupied_voice_channels)
            else:
                voice_channel = interaction.guild.voice_channels[0]

        voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        if not voice:
            voice_channel = await voice_channel.connect()
        else:
            await voice.move_to(voice_channel)

        voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)

        # Play the audio preview
        def after_playing(error):
            if error:
                print(f"Error occurred: {error}")
            if len(voice.channel.members) == 1:  # Only the bot is in the channel
                asyncio.run_coroutine_threadsafe(voice.disconnect(), bot.loop)
        
        source = discord.FFmpegPCMAudio(audio_preview_url)
        volume = discord.PCMVolumeTransformer(source, volume=0.8)
        voice.play(volume, after=after_playing)

        em1 = discord.Embed(
            title="Now Playing on Spotify",
            description=f'{track_name} by {artist_name}\n\nMusic provided by {interaction.user.mention}',
            color=interaction.user.color
        )
        await interaction.edit_original_response(embed=em1)
    else:
        await interaction.edit_original_response(content="No preview available for this track.")

class PlayView(View):
    def __init__(self,Interaction):
        super().__init__(timeout=None)  # View sans timeout
        self.interaction  = Interaction

    # Bouton Pause
    @discord.ui.button(label='Pause', style=discord.ButtonStyle.primary, emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.interaction.edit_original_response(view=PauseView(self.interaction))
        discord.utils.get(bot.voice_clients, guild=self.interaction.guild).pause()
        await interaction.response.send_message(":white_check_mark:",ephemeral=True,delete_after=0)

    # Bouton Stop
    @discord.ui.button(label='Stop', style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        discord.utils.get(bot.voice_clients, guild=self.interaction.guild).stop()
        await interaction.response.send_message(":white_check_mark:",ephemeral=True,delete_after=0)

class PauseView(View):
    def __init__(self,Interaction):
        super().__init__(timeout=None)  # View sans timeout
        self.interaction  = Interaction

    # Bouton Pause
    @discord.ui.button(label='Play', style=discord.ButtonStyle.primary, emoji="▶️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.interaction.edit_original_response(view=PlayView(self.interaction))
        discord.utils.get(bot.voice_clients, guild=self.interaction.guild).resume()
        await interaction.response.send_message(":white_check_mark:",ephemeral=True,delete_after=0)

    # Bouton Stop
    @discord.ui.button(label='Stop', style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        discord.utils.get(bot.voice_clients, guild=self.interaction.guild).stop()
        await interaction.response.send_message(":white_check_mark:",ephemeral=True,delete_after=0)
        

def get_video_url(video_name):
    

    request = youtube.search().list(
        q=video_name,
        type='video',
        part='id',
        maxResults=1
    )
    response = request.execute()

    if 'items' in response:
        video_id = response['items'][0]['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return video_url
    else:
        return None

bot.run(DISCORD_TOKEN)
