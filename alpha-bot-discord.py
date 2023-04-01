import discord
import os
from discord.ext import commands
import asyncio
import yt_dlp as youtube_dl

client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

voice_clients = {}
queues = {}

yt_dl_opts = {'format': 'bestaudio/best'}
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)

ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


@client.event
async def on_ready():
    print("Bot is ready!")


@client.command()
async def h(ctx):
    embed = discord.Embed(title="คำสั่งทั้งหมด", description="นี่คือคำสั่งทั้งหมดในการใช้งานบอท", color=0xCC99FF)
    embed.add_field(name="!play <ชื่อเพลง>", value="เพิ่มเพลงลงในคิวและเล่นเพลง", inline=False)
    embed.add_field(name="!pause", value="หยุดเพลงที่กำลังเล่นอยู่", inline=False)
    embed.add_field(name="!resume", value="เริ่มเล่นเพลงต่อจากที่หยุด", inline=False)
    embed.add_field(name="!stop", value="หยุดเพลงที่เล่นและคิวทั้งหมด", inline=False)
    embed.add_field(name="!skip", value="ข้ามเพลงที่กำลังเล่นและเล่นเพลงถัดไปที่อยู่ในคิว", inline=False)
    embed.add_field(name="!remove <ลำดับเพลงในรายการ>", value="ลบรายการเพลงออกจากคิว", inline=False)
    embed.add_field(name="!queue", value="แสดงเพลงที่อยู่ในคิวทั้งหมด", inline=False)
    await ctx.send(embed=embed)


@client.command(pass_context=True)
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You are not connected to a voice channel.")


@client.command(pass_context=True)
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@client.command(pass_context=True)
async def play(ctx, *args):
    try:
        voice_client = await ctx.author.voice.channel.connect()
        voice_clients[ctx.guild.id] = voice_client
    except:
        pass

    try:
        query = " ".join(args)

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False))

        song = data['entries'][0]['url']
        source = discord.FFmpegPCMAudio(song, executable="D:\\ffmpeg\\bin\\ffmpeg.exe", **ffmpeg_options)
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []
        queues[ctx.guild.id].append((source, data['entries'][0]['title']))
        duration = data['entries'][0]['duration']
        hours, minutes, seconds = int(duration // 3600), int((duration % 3600) // 60), int(duration % 60)

        # format duration into a string in "hh:mm:ss" format
        if hours > 0:
            duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        else:
            duration_str = f"{minutes:02}:{seconds:02}"
        if voice_clients[ctx.guild.id].is_playing():

            await ctx.send(f"⌛️ เพิ่มเพลง {data['entries'][0]['title']} ลงในคิวแล้ว \n⏱🔵 [{duration_str}]")
        else:

            while queues[ctx.guild.id]:
                source, title = queues[ctx.guild.id][0]
                duration = data['entries'][0]['duration']
                hours, minutes, seconds = int(duration // 3600), int((duration % 3600) // 60), int(duration % 60)

                # format duration into a string in "hh:mm:ss" format
                if hours > 0:
                    duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    duration_str = f"{minutes:02}:{seconds:02}"
                await ctx.send(f"🎶ตอนนี้กำลังเล่นเพลง {title}. \n⏱🔴 [{duration_str}]")
                voice_clients[ctx.guild.id].play(source)
                while voice_clients[ctx.guild.id].is_playing():
                    await asyncio.sleep(1)
                queues[ctx.guild.id].pop(0)

            # Disconnect if the bot is not playing any song for 30 seconds
            await asyncio.sleep(10)
            if not voice_clients[ctx.guild.id].is_playing():
                await voice_clients[ctx.guild.id].disconnect()

    except Exception as err:
        print(err)



@client.command(pass_context=True)
async def pause(ctx):
    try:
        voice_clients[ctx.guild.id].pause()
    except Exception as err:
        print(err)


@client.command(pass_context=True)
async def resume(ctx):
    try:
        voice_clients[ctx.guild.id].resume()
    except Exception as err:
        print(err)


@client.command(pass_context=True)
async def stop(ctx):
    try:
        voice_client = voice_clients[ctx.guild.id]
        if voice_client.is_playing():
            voice_client.stop()
            queues[ctx.guild.id] = []
            await asyncio.sleep(1)
            if not voice_client.is_playing():
                await voice_client.disconnect()
    except Exception as err:
        print(err)


@client.command(pass_context=True)
async def skip(ctx):
    try:
        await ctx.send("⏭️กำลังข้ามเพลง")
        voice_clients[ctx.guild.id].stop()
    except Exception as err:
        print(err)

@client.command(pass_context=True)
async def remove(ctx, index: int):
    try:
        if ctx.guild.id not in queues:
            await ctx.send("ไม่มีอะไรอยู่ในคิว")
            return

        if index < 1 or index > len(queues[ctx.guild.id]):
            await ctx.send("ไม่พบเพลงในนี้")
            return

        song = queues[ctx.guild.id][index-1][1]
        queues[ctx.guild.id].pop(index-1)
        await ctx.send(f"ลบ❌ {song} ออกจากคิว")

    except Exception as err:
        print(err)
        
@client.command(pass_context=True)
async def queue(ctx):
    if ctx.guild.id not in queues or not queues[ctx.guild.id]:
        await ctx.send("ตอนนี้ไม่มีเพลงอยู่ในคิว")
        return
    
    queue_list = "```"
    for i, song in enumerate(queues[ctx.guild.id]):
        queue_list += f"{i+1}. {song[1]}\n"
    queue_list += "```"
    await ctx.send(f"เพลงที่อยู่ในคิว:\n{queue_list}")


client.run('MTA5MTI5NDUyNjcyOTEwNTQ1OQ.GYfKhh.mCvBqsWFitdh6nngWj28OBt6ntpPHJx7CLHaHo')