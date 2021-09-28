#!/usr/bin/python3.9
import discord
from discord.ext.commands import Bot
from discord.ext import tasks
from requests import get
from youtube_dl import YoutubeDL

bot = Bot(command_prefix='.')
global song_dictionary
song_dictionary = {}
global current_voice_client
current_voice_client = None
global current_url_request
current_url_request = None
global current_ctx
current_ctx = None


async def search(arg):
    YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True'}
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            get(arg)
        except:
            video = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        else:
            video = ydl.extract_info(arg, download=False)

    return video

@bot.command(aliases=['p'])
async def play(ctx, *, args, voice_ctx_based_play=None):
    global song_dictionary
    global current_url_request
    global current_voice_client
    global current_ctx
    YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    temp_args = args
    args = ''
    print(temp_args)
    for arg in temp_args:
        args += arg


    video_dict = await search(args)
    url = video_dict.get('webpage_url')

    try:
        if ctx is None:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                I_URL = info['formats'][0]['url']
                source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
                voice_ctx_based_play.play(source)
        else:
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)


        if voice is None:
            current_ctx = ctx
            current_url_request = url
            current_voice_client = voice

            voice_client = ctx.author.voice.channel
            await voice_client.connect()

            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                I_URL = info['formats'][0]['url']
                source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
                voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
                voice.play(source)

        elif voice.is_playing() and voice.channel == ctx.author.voice.channel:
            current_ctx = ctx
            current_url_request = url
            current_voice_client = voice

        elif not voice.is_playing() and voice.channel == ctx.author.voice.channel:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                I_URL = info['formats'][0]['url']
                source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
                voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
                voice.play(source)
        else:
            ctx.send('get outta here!')
    except Exception as e:
        pass


@bot.command(aliases=['n'])
async def next(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice.stop()

@bot.command(aliases=['s'])
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if song_dictionary.get(ctx.author.voice.channel.id) is not None:
        new_queue = song_dictionary.get(ctx.author.voice.channel.id).clear()
        song_dictionary[ctx.author.voice.channel.id] = new_queue
    voice.stop()

@tasks.loop(seconds=0.05)
async def queue_each():
    global current_url_request
    global current_ctx
    global current_voice_client

    if current_voice_client is None:
        pass
    elif current_voice_client.is_playing() and current_url_request is not None:
        if song_dictionary.get(current_ctx.author.voice.channel.id) is None:
            init_queue = [current_url_request]
            song_dictionary[current_ctx.author.voice.channel.id] = init_queue
        elif song_dictionary.get(current_ctx.author.voice.channel.id) is not None:
            new_queue = song_dictionary.get(current_ctx.author.voice.channel.id)
            new_queue.append(current_url_request)
            song_dictionary[current_ctx.author.voice.channel.id] = new_queue
        else:
            pass

        current_url_request = None

@tasks.loop(seconds=0.5)
async def check_bots_playing():
    global song_dictionary
    for channel_id in song_dictionary:
        voice = discord.utils.get(bot.voice_clients, channel=bot.get_channel(channel_id))
        if voice is None:
            pass
        elif not voice.is_playing() and song_dictionary.get(voice.channel.id) is not None \
                and len(song_dictionary.get(voice.channel.id)) != 0:
            await play(ctx=None, voice_ctx_based_play=voice,args=song_dictionary.get(voice.channel.id).pop(0))


check_bots_playing.start()
queue_each.start()

token = ''
with open('token.txt') as file:
    token = file.readline()
    file.close()
bot.run(token)
