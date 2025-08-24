import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
# ใส่ Token ของคุณตรงนี้เลย
load_dotenv(".venv/well.env")
TOKEN = os.getenv("DISCORD_TOKEN3")

# ตั้งค่า intents
intents = discord.Intents.default()
intents.members = True  # ต้องเปิด Server Members Intent

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ บอทล็อกอินแล้ว: {bot.user}")

WELCOME_MESSAGES = [
    "🎉 ยินดีต้อนรับ {member} สู่ Ayxora Shop!",
    "💖 ขอบคุณที่เข้ามานย้าา {member}!",
    "👋 ดีจ้าา {member}! Thx to join my shop!"
]

WELCOME_GIFS = [
    "https://cdn.discordapp.com/attachments/1401765668491100163/1408730547865256037/file_000000002324622f979534ea5f1642e2.png?ex=68aace0f&is=68a97c8f&hm=77fe9a219c270406fb3419c4a39656e3a75408a378710d3f2e9126398f830c66"
]

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is None:
        channel = discord.utils.get(member.guild.channels, name="welcome")
    if channel is None:
        print(f"⚠️ ไม่มีช่องต้อนรับในเซิร์ฟเวอร์ {member.guild.name}")
        return

    msg = random.choice(WELCOME_MESSAGES).format(member=member.mention)
    gif = random.choice(WELCOME_GIFS)

    embed = discord.Embed(
        title="✨ สมาชิกใหม่!",
        description=msg,
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else discord.Embed.Empty)
    embed.set_image(url=gif)
    embed.set_footer(text="เราดีใจที่คุณมาร่วมสนุกกับเรา!")

    await channel.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN3"))