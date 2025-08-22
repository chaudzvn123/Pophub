import discord
from discord.ext import commands
import random
import json
import os
import time

# ================== CẤU HÌNH ==================
TOKEN = "YOUR_TOKEN"   # Thay bằng token bot của bạn
PREFIX = ","
ADMIN_UID = [1265245644558176278]   # Thay ID admin của bạn
DATA_FILE = "users.json"

GIF_GOAL = "https://drive.google.com/uc?export=view&id=1ABCDefGhIJklMNopQRstuVWxyz12345"
GIF_SAVE = "https://media.discordapp.net/attachments/xyz/save.gif"

# ================== LOAD & SAVE ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def init_user(uid):
    data = load_data()
    if str(uid) not in data:
        data[str(uid)] = {
            "balance": 0,
            "wins": 0,
            "force_lose": 0,
            "always_win": False,
            "last_daily": 0
        }
        save_data(data)
        print(f"[INIT] Khởi tạo user {uid}")
    return data[str(uid)]

def get_balance(uid):
    data = load_data()
    init_user(uid)
    return data[str(uid)]["balance"]

def set_balance(uid, amount):
    data = load_data()
    init_user(uid)
    data[str(uid)]["balance"] = max(0, amount)
    save_data(data)

def add_balance(uid, amount):
    data = load_data()
    init_user(uid)
    data[str(uid)]["balance"] = max(0, data[str(uid)]["balance"] + amount)
    save_data(data)

# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# --------- DAILY ---------
@bot.command(name="daily")
async def daily(ctx):
    uid = str(ctx.author.id)
    data = load_data()
    init_user(uid)

    now = int(time.time())
    last_daily = data[uid].get("last_daily", 0)

    if now - last_daily < 86400:  # 24h = 86400s
        remain = 86400 - (now - last_daily)
        hours = remain // 3600
        minutes = (remain % 3600) // 60
        await ctx.send(f"⏳ Bạn phải chờ {hours}h {minutes}m nữa để nhận quà daily!")
        return

    reward = 1000
    add_balance(uid, reward)
    data[uid]["last_daily"] = now
    save_data(data)

    await ctx.send(f"🎁 Bạn đã nhận **{reward} xu** daily! Số dư: {get_balance(uid)}")

# --------- BAL ---------
@bot.command(name="bal")
async def bal(ctx):
    uid = str(ctx.author.id)
    balance = get_balance(uid)
    await ctx.send(f"💰 Số dư của bạn: **{balance} xu**")

# --------- GIVE ---------
@bot.command(name="give")
async def give(ctx, member: discord.Member, amount: int):
    sender = str(ctx.author.id)
    receiver = str(member.id)

    if amount <= 0:
        return await ctx.send("❌ Số tiền không hợp lệ!")

    if get_balance(sender) < amount:
        return await ctx.send("❌ Bạn không đủ tiền!")

    add_balance(sender, -amount)
    add_balance(receiver, amount)

    await ctx.send(f"✅ {ctx.author.mention} đã chuyển **{amount} xu** cho {member.mention}")

# --------- ADMIN ---------
@bot.command(name="addcash")
async def addcash(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    add_balance(str(member.id), amount)
    await ctx.send(f"✅ Đã cộng {amount} xu cho {member.mention}")

@bot.command(name="settien")
async def settien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    set_balance(str(member.id), amount)
    await ctx.send(f"✅ Đã đặt lại số dư {member.mention} thành {amount}")

@bot.command(name="bantien")
async def bantien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    add_balance(str(member.id), -amount)
    await ctx.send(f"✅ Đã trừ {amount} xu từ {member.mention}")

@bot.command(name="luonthang")
async def luonthang(ctx, member: discord.Member, mode: str):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")

    data = load_data()
    init_user(str(member.id))
    if mode.lower() == "on":
        data[str(member.id)]["always_win"] = True
        save_data(data)
        await ctx.send(f"⚡ {member.mention} đã bật chế độ luôn thắng!")
    elif mode.lower() == "off":
        data[str(member.id)]["always_win"] = False
        save_data(data)
        await ctx.send(f"⚡ {member.mention} đã tắt chế độ luôn thắng!")
    else:
        await ctx.send("❌ Sai cú pháp! Dùng: `,luonthang @user on/off`")

# --------- GAME SÚT ---------
@bot.command(name="sut")
async def sut(ctx, huong: str, tien: str):
    uid = str(ctx.author.id)
    data = load_data()
    user = init_user(uid)

    # Xử lý số tiền
    if tien.lower() == "all":
        bet = get_balance(uid)
    else:
        if not tien.isdigit():
            return await ctx.send("❌ Số tiền không hợp lệ!")
        bet = int(tien)

    if bet <= 0:
        return await ctx.send("❌ Số tiền không hợp lệ!")

    if get_balance(uid) < bet:
        return await ctx.send("❌ Bạn không đủ tiền!")

    if huong.lower() not in ["trái", "phải"]:
        return await ctx.send("⚠️ Bạn phải chọn `trái` hoặc `phải`!")

    # Tính kết quả
    if user.get("always_win", False):
        goal = huong.lower()
    else:
        goal = random.choice(["trái", "phải"])

    if huong.lower() == goal:
        add_balance(uid, bet)
        result = f"🎉 {ctx.author.mention} SÚT VÀO!!! Bạn thắng **{bet} xu**"
        gif = GIF_GOAL
    else:
        add_balance(uid, -bet)
        result = f"💔 {ctx.author.mention} sút trượt! Bạn thua **{bet} xu**"
        gif = GIF_SAVE

    embed = discord.Embed(title="⚽ Kết quả sút", description=result, color=0x00ff00)
    embed.set_image(url=gif)
    await ctx.send(embed=embed)

# --------- CÁCH CHƠI ---------
@bot.command(name="cachchoi")
async def cachchoi(ctx):
    embed = discord.Embed(
        title="📖 HƯỚNG DẪN & DANH SÁCH LỆNH",
        description="Dưới đây là tất cả các lệnh bạn có thể dùng:",
        color=0x00ffcc
    )

    embed.add_field(
        name="⚽ Game Penalty",
        value="`,sut [trái/phải] [số tiền | all]` → Ví dụ: `,sut trái 500` hoặc `,sut phải all`",
        inline=False
    )

    embed.add_field(
        name="🎁 Daily",
        value="`,daily` → Nhận 1000 xu miễn phí mỗi 24h",
        inline=False
    )

    embed.add_field(
        name="💸 Tiền tệ",
        value="`,give @user [số tiền]`\n`,bal` → Xem số dư",
        inline=False
    )

    embed.add_field(
        name="⚡ Admin",
        value="`,addcash @user [số tiền]`\n`,settien @user [số tiền]`\n`,bantien @user [số tiền]`\n`,luonthang @user [on/off]`",
        inline=False
    )

    embed.set_footer(text="Chúc bạn chơi vui vẻ ⚽")
    await ctx.send(embed=embed)

# ================== RUN ==================
bot.run(TOKEN)
