from ast import main
import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import random
import os
import threading
from flask import Flask

# ---------- Flask Server สำหรับเปิด port ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))  # ใช้ PORT จาก environment หรือ 5000 เป็นค่า default
    app.run(host="0.0.0.0", port=port)

# เรียก Flask server ใน thread แยก
threading.Thread(target=run_flask).start()

# ---------- โหลด Token ----------
load_dotenv(".venv/rank.env")
TOKEN = os.getenv("DISCORD_TOKEN1")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

ROLE_NAME = "Customer"
CHANNEL_NAME = "｡･⊹🔮-𝗴𝗲𝘁-𝗿𝗮𝗻𝗸"

# รูปภาพปกติ
IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/1401765668491100163/1408730547865256037/file_000000002324622f979534ea5f1642e2.png?ex=68aace0f&is=68a97c8f&hm=77fe9a219c270406fb3419c4a39656e3a75408a378710d3f2e9126398f830c66"
]

@bot.event
async def on_ready():
    print(f"✅ บอทล็อกอินแล้ว: {bot.user}")

@bot.event
async def on_member_join(member):
    guild = member.guild
    channel = discord.utils.get(guild.channels, name=CHANNEL_NAME)
    if channel is None:
        return

    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role in member.roles:
        return

    await send_rank_button(member, channel, role)

async def send_rank_button(member, channel, role):
    button = Button(label="รับยศ", style=discord.ButtonStyle.green)

    async def button_callback(interaction):
        if interaction.user != member:
            await interaction.response.send_message("❌ ปุ่มนี้สำหรับสมาชิกใหม่เท่านั้น!", ephemeral=True)
            return

        try:
            await member.add_roles(role)
            embed = discord.Embed(
                title="🎉 สมาชิกได้รับยศแล้ว!",
                description=f"{member.mention} ได้รับยศ `{role.name}`",
                color=discord.Color.green()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            await channel.send(embed=embed)
            await interaction.response.send_message("คุณได้รับยศแล้ว!", ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("❌ บอทไม่มีสิทธิ์เพิ่ม Role ให้คุณ!", ephemeral=True)

    button.callback = button_callback
    view = View()
    view.add_item(button)

    image_url = random.choice(IMAGE_LIST)

    embed = discord.Embed(
        title="✨ สมาชิกใหม่! รับยศได้ที่นี่",
        description=f"{member.mention}, คลิกปุ่มด้านล่างเพื่อรับยศ `{role.name}`",
        color=discord.Color.purple()
    )
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    embed.set_image(url=image_url)

    await member.send(embed=embed, view=view)

# ---------- รัน Bot ----------
bot.run(os.getenv("DISCORD_TOKEN1"))