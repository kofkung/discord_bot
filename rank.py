import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import random
import os
from flask import Flask
import threading

# ---------- Flask Server สำหรับ Render ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ---------- โหลด Token ----------
load_dotenv(".venv/rank.env")
TOKEN = os.getenv("DISCORD_TOKEN1")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

ROLE_NAME = "𖦹 𐙚  Customer  ♡ 彡"
CHANNEL_NAME = "｡･⊹🔮-𝗴𝗲𝘁-𝗿𝗮𝗻𝗸"

IMAGE_LIST = [
    "https://cdn.discordapp.com/attachments/1401765668491100163/1408730547865256037/file_000000002324622f979534ea5f1642e2.png"
]

@bot.event
async def on_ready():
    print(f"✅ Rank Bot logged in as {bot.user}")

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=ROLE_NAME)
    if role is None:
        print(f"⚠️ Role {ROLE_NAME} not found")
        return

    # ส่ง DM ให้สมาชิกใหม่
    await send_rank_button(member, role)

async def send_rank_button(member, role):
    button = Button(label="รับยศ", style=discord.ButtonStyle.green)

    async def button_callback(interaction):
        if interaction.user != member:
            await interaction.response.send_message("❌ ปุ่มนี้สำหรับสมาชิกใหม่เท่านั้น!", ephemeral=True)
            return
        try:
            await member.add_roles(role)
            await interaction.response.send_message(f"คุณได้รับยศ `{role.name}` เรียบร้อย!", ephemeral=True)

            # ส่งข้อความในช่องเฉพาะสมาชิกใหม่
            channel = discord.utils.get(member.guild.channels, name=CHANNEL_NAME)
            if channel:
                embed = discord.Embed(
                    title="🎉 สมาชิกได้รับยศแล้ว!",
                    description=f"{member.mention} ได้รับยศ `{role.name}`",
                    color=discord.Color.green()
                )
                if member.avatar:
                    embed.set_thumbnail(url=member.avatar.url)
                await channel.send(embed=embed)

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

    try:
        await member.send(embed=embed, view=view)
    except discord.Forbidden:
        print(f"❌ ไม่สามารถส่ง DM ให้ {member} ได้")

# ---------- Run Flask + Bot ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN1"))