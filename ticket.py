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

# ---------- เก็บ DM ของผู้รับตั๋ว ----------
user_open_tickets = {}  # {user_id: [ticket_info,...]}

# ---------- Modal สำหรับกรอกข้อมูลตั๋ว ----------
class TicketModal(Modal):
    def __init__(self, member):
        super().__init__(title="กรอกข้อมูลตั๋ว")
        self.member = member
        self.skin = TextInput(label="สกิน Minecraft", placeholder="สเกลที่ต้องการ")
        self.gender = TextInput(label="เพศ", placeholder="ชาย / หญิง")
        self.reference = TextInput(label="Reference", placeholder="อธิบายเพิ่มเติมลักษณะต่างๆของสกิน")
        self.image_url = TextInput(label="แนบรูปภาพ (URL)", placeholder="วางลิงก์ไฟล์ JPG/PNG ถ้ามี", required=False)
        self.addon = TextInput(label="เอาแอดออนไหม?", placeholder="พิมพ์ ใช่ / ไม่ *หากไม่ใส่ข้อมูลจะนับว่า ไม่*", required=False)
        self.add_item(self.skin)
        self.add_item(self.gender)
        self.add_item(self.reference)
        self.add_item(self.image_url)
        self.add_item(self.addon)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
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
                f"**รูปภาพ:** {self.image_url.value if self.image_url.value else 'ไม่มี'}\n"
                f"**เอาแอดออนไหม:** {self.addon.value if self.addon.value else 'ไม่ได้เลือก'}"
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
                f"**รูปภาพ:** {self.image_url.value if self.image_url.value else 'ไม่มี'}\n"
                f"**เอาแอดออนไหม:** {self.addon.value if self.addon.value else 'ไม่ได้เลือก'}"
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
            await interaction2.response.send_message(
                f"{interaction2.user.display_name} ได้ยืนยันตั๋วเรียบร้อย ✅", ephemeral=False
            )

            ticket_room = discord.utils.get(guild.text_channels, name=TICKET_CHANNEL)
            notify_msg = None
            if ticket_room:
                embed_notify = discord.Embed(
                    title="🎟️ มีการรับตั๋ว",
                    description=f"{interaction2.user.mention} ได้รับตั๋วของ {self.member.mention} เรียบร้อย ✅",
                    color=discord.Color.purple()
                )
                if interaction2.user.avatar:
                    embed_notify.set_thumbnail(url=interaction2.user.avatar.url)
                notify_msg = await ticket_room.send(embed=embed_notify)

            # ---------- ส่ง DM ให้ผู้รับตั๋ว ----------
            try:
                dm_channel = await interaction2.user.create_dm()
                finish_view = View()

                # สร้าง embed DM
                embed_dm = discord.Embed(
                    title=f"คุณได้รับตั๋วจาก {self.member.display_name}",
                    description=(
                        f"**สกิน:** {self.skin.value}\n"
                        f"**เพศ:** {self.gender.value}\n"
                        f"**Reference:** {self.reference.value}\n"
                        f"**รูปภาพ:** {self.image_url.value if self.image_url.value else 'ไม่มี'}\n"
                        f"**เอาแอดออนไหม:** {self.addon.value if self.addon.value else 'ไม่ได้เลือก'}"
                    ),
                    color=discord.Color.blue()
                )
                if self.member.avatar:
                    embed_dm.set_thumbnail(url=self.member.avatar.url)

                # ---------- สร้างปุ่มจบงาน ----------
                btn_finish = Button(
                    label=f"จบงานตั๋วของ {self.member.display_name}",
                    style=discord.ButtonStyle.red
                )

                async def finish_callback(finish_interaction: discord.Interaction):
                    if finish_interaction.user != interaction2.user:
                        await finish_interaction.response.send_message(
                            "❌ คุณไม่สามารถกดจบงานนี้ได้!", ephemeral=True
                        )
                        return

                    await finish_interaction.response.send_message(
                        f"งานของ {ticket_info['creator'].display_name} เสร็จเรียบร้อย ✅",
                        ephemeral=True
                    )

                    # ลบ ticket / confirm channel
                    await ticket_info["ticket_channel"].delete()
                    await ticket_info["confirm_channel"].delete()

                    # ลบข้อความ notify ในห้องสั่งสินค้า
                    if ticket_info.get("notify_message_id") and ticket_room:
                        try:
                            notify_msg_to_delete = await ticket_room.fetch_message(ticket_info["notify_message_id"])
                            await notify_msg_to_delete.delete()
                        except:
                            pass

                    # ลบ DM ของผู้รับตั๋ว
                    if ticket_info.get("dm_message"):
                        try:
                            await ticket_info["dm_message"].delete()
                        except:
                            pass

                    # ส่ง DM ไปยังผู้สร้าง ticket
                    try:
                        creator_dm = await ticket_info["creator"].create_dm()
                        await creator_dm.send(
                            f"🎉 ตั๋วของคุณได้รับการดำเนินการโดย {interaction2.user.display_name} เสร็จเรียบร้อยแล้ว!"
                        )
                    except:
                        pass

                    # เอาตั๋วออกจาก list
                    if finish_interaction.user.id in user_open_tickets:
                        user_open_tickets[finish_interaction.user.id].remove(ticket_info)

                btn_finish.callback = finish_callback
                finish_view.add_item(btn_finish)

                # ส่ง DM และเก็บ message object
                dm_message = await dm_channel.send(embed=embed_dm, view=finish_view)

                # เก็บ ticket_info
                ticket_info = {
                    "ticket_channel": ticket_channel,
                    "confirm_channel": confirm_channel,
                    "creator": self.member,
                    "notify_message_id": notify_msg.id if notify_msg else None,
                    "dm_message": dm_message
                }
                user_open_tickets.setdefault(interaction2.user.id, []).append(ticket_info)

            except discord.Forbidden:
                await interaction2.followup.send(
                    "❌ ไม่สามารถส่ง DM ให้ผู้รับตั๋วได้", ephemeral=True
                )

        async def delete_callback(interaction2: discord.Interaction):
            await ticket_channel.delete()
            await confirm_channel.delete()
            # ลบข้อความ notify ถ้ามี
            if ticket_room:
                async for msg in ticket_room.history(limit=100):
                    if msg.author == bot.user and "🎟️ มีการรับตั๋ว" in (msg.embeds[0].title if msg.embeds else ""):
                        await msg.delete()
                        break
            await interaction2.response.send_message("ลบตั๋วเรียบร้อย ✅", ephemeral=False)

        btn_accept.callback = accept_callback
        btn_delete.callback = delete_callback
        view.add_item(btn_accept)
        view.add_item(btn_delete)

        await confirm_channel.send(embed=embed_confirm, view=view)
        await interaction.response.send_message(
            f"ตั๋วของคุณถูกสร้างแล้ว {ticket_channel.mention}", ephemeral=True
        )

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