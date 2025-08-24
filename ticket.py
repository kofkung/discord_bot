import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from dotenv import load_dotenv
import os
import threading
from flask import Flask 

# ---------- Flask Server สำหรับ Render ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Ticket Bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ---------- โหลด Token ----------
load_dotenv(".venv/ticket.env")
TOKEN = os.getenv("DISCORD_TOKEN2")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TICKET_CHANNEL = "❃🪬･˚⁺สั่งสินค้า"
STAFF_ROLES = ["Employee", "Admin"]

# ---------- Modal สำหรับกรอกข้อมูลตั๋ว ----------
class TicketModal(Modal):
    def __init__(self, member):
        super().__init__(title="กรอกข้อมูลตั๋ว")
        self.member = member
        self.skin = TextInput(label="สกิน Minecraft", placeholder="สเกลที่ต้องการ")
        self.gender = TextInput(label="เพศ", placeholder="ชาย / หญิง")
        self.reference = TextInput(label="Reference", placeholder="อธิบายเพิ่มเติมลักษณะต่างๆของสกิน")
        self.image_url = TextInput(label="แนบรูปภาพ (URL)", placeholder="วางลิงก์ไฟล์ JPG/PNG ถ้ามี", required=False)
        self.add_item(self.skin)
        self.add_item(self.gender)
        self.add_item(self.reference)
        self.add_item(self.image_url)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        # สร้าง category ถ้าไม่มี
        category = discord.utils.get(guild.categories, name="Tickets")
        if category is None:
            category = await guild.create_category("Tickets")
        
        # ---------- สร้าง ticket channel ----------
        ticket_name = f"ticket-{self.member.name}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.member: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for role_name in STAFF_ROLES:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, manage_messages=True, manage_channels=True
                )
        ticket_channel = await guild.create_text_channel(ticket_name, category=category, overwrites=overwrites)

        embed_ticket = discord.Embed(
            title=f"ตั๋วของ {self.member.display_name}",
            description=(
                f"**สกิน:** {self.skin.value}\n"
                f"**เพศ:** {self.gender.value}\n"
                f"**Reference:** {self.reference.value}\n"
                f"**รูปภาพ:** {self.image_url.value if self.image_url.value else 'ไม่มี'}"
            ),
            color=discord.Color.blue()
        )
        if self.member.avatar:
            embed_ticket.set_thumbnail(url=self.member.avatar.url)
        await ticket_channel.send(content=f"{self.member.mention} ได้สร้างตั๋ว", embed=embed_ticket)

        # ---------- สร้าง confirm channel ----------
        confirm_name = f"confirm-tick-{self.member.name}"
        confirm_overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
        for role_name in STAFF_ROLES:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                confirm_overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        confirm_channel = await guild.create_text_channel(confirm_name, category=category, overwrites=confirm_overwrites)

        embed_confirm = discord.Embed(
            title=f"ตั๋วยืนยันของ {self.member.display_name}",
            description=(
                f"**สกิน:** {self.skin.value}\n"
                f"**เพศ:** {self.gender.value}\n"
                f"**Reference:** {self.reference.value}\n"
                f"**รูปภาพ:** {self.image_url.value if self.image_url.value else 'ไม่มี'}"
            ),
            color=discord.Color.green()
        )
        if self.member.avatar:
            embed_confirm.set_thumbnail(url=self.member.avatar.url)

        # ---------- ปุ่ม confirm ----------
        view = View()
        btn_accept = Button(label="รับตั๋ว", style=discord.ButtonStyle.green)
        btn_delete = Button(label="ลบตั๋ว", style=discord.ButtonStyle.red)

        async def accept_callback(interaction2: discord.Interaction):
            await interaction2.response.send_message(f"{interaction2.user.display_name} ได้ยืนยันตั๋วเรียบร้อย ✅", ephemeral=False)

            ticket_room = discord.utils.get(guild.text_channels, name=TICKET_CHANNEL)
            if ticket_room:
                embed_notify = discord.Embed(
                    title="🎟️ มีการรับตั๋ว",
                    description=f"{interaction2.user.mention} ได้รับตั๋วของ {self.member.mention} เรียบร้อย ✅",
                    color=discord.Color.purple()
                )
                if interaction2.user.avatar:
                    embed_notify.set_thumbnail(url=interaction2.user.avatar.url)
                await ticket_room.send(embed=embed_notify)

            # ส่ง DM ให้ผู้รับตั๋วเพื่อจบงาน
            try:
                dm_channel = await interaction2.user.create_dm()

                # ลบข้อความ DM เก่าของ bot
                async for msg in dm_channel.history(limit=None):
                    if msg.author == bot.user:
                        try:
                            await msg.delete()
                        except:
                            pass

                finish_view = View()
                btn_finish = Button(label="จบงาน", style=discord.ButtonStyle.red)

                async def finish_callback(finish_interaction: discord.Interaction):
                    if finish_interaction.user != interaction2.user:
                        await finish_interaction.response.send_message("❌ คุณไม่สามารถกดจบงานนี้ได้!", ephemeral=True)
                        return

                    await finish_interaction.response.send_message("งานเสร็จเรียบร้อย ✅", ephemeral=True)

                    # ลบ ticket และ confirm channel
                    await ticket_channel.delete()
                    await confirm_channel.delete()

                    # ลบข้อความใน TICKET_CHANNEL ยกเว้นปุ่มเปิดตั๋ว
                    if ticket_room:
                        async for msg in ticket_room.history(limit=None):
                            keep = False
                            if msg.components:
                                for row in msg.components:
                                    for item in row.children:
                                        if getattr(item, "custom_id", None) == "open_ticket":
                                            keep = True
                            if not keep:
                                try:
                                    await msg.delete()
                                except:
                                    pass

                    # ส่ง DM ไปยังผู้สร้าง ticket
                    try:
                        creator_dm = await self.member.create_dm()
                        await creator_dm.send(f"🎉 ตั๋วของคุณได้รับการดำเนินการโดย {interaction2.user.display_name} เสร็จเรียบร้อยแล้ว!")
                    except:
                        pass

                btn_finish.callback = finish_callback
                finish_view.add_item(btn_finish)
                await dm_channel.send("กดปุ่มด้านล่างเพื่อจบงาน 🏁", view=finish_view)

            except discord.Forbidden:
                await interaction2.followup.send("❌ ไม่สามารถส่ง DM ให้ผู้รับตั๋วได้", ephemeral=True)

        async def delete_callback(interaction2: discord.Interaction):
            await ticket_channel.delete()
            await confirm_channel.delete()
            await interaction2.response.send_message("ลบตั๋วเรียบร้อย ✅", ephemeral=False)

        btn_accept.callback = accept_callback
        btn_delete.callback = delete_callback
        view.add_item(btn_accept)
        view.add_item(btn_delete)

        await confirm_channel.send(embed=embed_confirm, view=view)
        await interaction.response.send_message(f"ตั๋วของคุณถูกสร้างแล้ว {ticket_channel.mention}", ephemeral=True)

# ---------- ปุ่มเปิดตั๋ว ----------
class OpenTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="เปิดตั๋ว", style=discord.ButtonStyle.green, custom_id="open_ticket"))

# ---------- คำสั่ง !ticket ----------
@bot.command()
async def ticket(ctx):
    if ctx.channel.name != TICKET_CHANNEL:
        await ctx.send(f"ใช้คำสั่งนี้ในช่อง {TICKET_CHANNEL} เท่านั้น")
        return
    view = OpenTicketView()
    await ctx.send("กดปุ่มด้านล่างเพื่อเปิดตั๋ว 🎟️", view=view)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] == "open_ticket":
            modal = TicketModal(interaction.user)
            await interaction.response.send_modal(modal)

# ---------- Run Flask + Bot ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN2"))