import discord
from discord.ext import commands
import random
import json
import os
import time

# ================== CẤU HÌNH ==================
TOKEN = "YOUR_TOKEN"
PREFIX = ","
ADMIN_UID = [1265245644558176278]
DATA_FILE = "users.json"

GIF_GOAL = "https://drive.google.com/uc?export=view&id=1ABCDefGhIJklMNopQRstuVWxyz12345"
GIF_SAVE = "https://drive.google.com/uc?export=view&id=1ZYXwvutsRQponMLkjihGFedcba54321"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ================== DỮ LIỆU ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

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
    return data

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

# ================== GAME PENALTY ==================
@bot.command(name="sut")
async def sut(ctx, huong: str, amount: str):
    huong = huong.lower()
    if huong not in ["trái", "phải"]:
        return await ctx.send("❌ Bạn chỉ được chọn `trái` hoặc `phải`!")

    # all-in
    if amount.lower() == "all":
        amount = get_balance(ctx.author.id)
    else:
        try:
            amount = int(amount)
        except:
            return await ctx.send("❌ Số tiền không hợp lệ!")

    if amount <= 0:
        return await ctx.send("❌ Số tiền cược phải lớn hơn 0!")

    balance = get_balance(ctx.author.id)
    if balance < amount:
        return await ctx.send(f"❌ Bạn không đủ tiền! Số dư: {balance:,} xu")

    # Trừ tiền cược
    add_balance(ctx.author.id, -amount)

    data = load_data()
    uid = str(ctx.author.id)
    user = data[uid]

    # Kiểm tra chế độ luôn thắng
    if user.get("always_win", False):
        is_goal = True
    else:
        # Bịp: nếu đã thắng 6 lần liên tiếp thì ép thua 3 lần
        if user["wins"] >= 6 and user["force_lose"] < 3:
            is_goal = False
            user["force_lose"] += 1
        else:
            if user["force_lose"] >= 3:
                user["wins"] = 0
                user["force_lose"] = 0
            # Xác suất 35%
            is_goal = random.random() < 0.35

    if is_goal:
        add_balance(ctx.author.id, amount * 2)
        user["wins"] += 1
        result = f"⚽ GOOOOAL!!! {ctx.author.mention} **THẮNG** {amount*2:,} xu 🎉"
        gif = GIF_GOAL
        color = 0xffd700
    else:
        user["wins"] = 0
        result = f"🧤 Thủ môn cản phá! {ctx.author.mention} **THUA** mất {amount:,} xu 😢"
        gif = GIF_SAVE
        color = 0xff0000

    save_data(data)

    embed = discord.Embed(
        title="🏟️ KẾT QUẢ PENALTY",
        description=result,
        color=color
    )
    await ctx.send(embed=embed)
    await ctx.send(gif)

# ================== DAILY ==================
@bot.command(name="daily")
async def daily(ctx):
    uid = str(ctx.author.id)
    data = load_data()
    init_user(uid)

    now = int(time.time())
    last_daily = data[uid].get("last_daily", 0)

    if now - last_daily < 24*3600:
        remain = 24*3600 - (now - last_daily)
        hours = remain // 3600
        minutes = (remain % 3600) // 60
        return await ctx.send(f"⏳ Bạn đã nhận daily rồi! Thử lại sau {hours}h {minutes}m.")

    data[uid]["balance"] += 1000
    data[uid]["last_daily"] = now
    save_data(data)

    await ctx.send(f"🎁 {ctx.author.mention} đã nhận **1000 xu** daily!")

# ================== TIỀN TỆ ==================
@bot.command(name="sotien")
async def sotien(ctx):
    bal = get_balance(ctx.author.id)
    await ctx.send(f"💰 {ctx.author.mention} đang có **{bal:,} xu**")

@bot.command(name="balance")
async def balance(ctx):
    bal = get_balance(ctx.author.id)
    await ctx.send(f"💰 {ctx.author.mention} đang có **{bal:,} xu**")

@bot.command(name="give")
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("❌ Số tiền chuyển phải > 0!")
    if get_balance(ctx.author.id) < amount:
        return await ctx.send("❌ Bạn không đủ xu!")

    add_balance(ctx.author.id, -amount)
    add_balance(member.id, amount)
    await ctx.send(f"💸 {ctx.author.mention} đã chuyển {amount:,} xu cho {member.mention}")

@bot.command(name="top")
async def top(ctx):
    data = load_data()
    ranking = sorted(data.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:10]
    desc = "\n".join([f"#{i+1} <@{uid}> — {info['balance']:,} xu" for i,(uid,info) in enumerate(ranking)])
    embed = discord.Embed(title="🏆 BẢNG XẾP HẠNG", description=desc, color=0x00ff00)
    await ctx.send(embed=embed)

# ================== ADMIN ==================
@bot.command(name="addcash")
async def addcash(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    add_balance(member.id, amount)
    await ctx.send(f"✅ Đã cộng {amount:,} xu cho {member.mention}")

@bot.command(name="settien")
async def settien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    set_balance(member.id, amount)
    await ctx.send(f"✅ Đã đặt số dư {amount:,} xu cho {member.mention}")

@bot.command(name="bantien")
async def bantien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    add_balance(member.id, -amount)
    await ctx.send(f"✅ Đã trừ {amount:,} xu của {member.mention}")

@bot.command(name="luonthang")
async def luonthang(ctx, member: discord.Member, state: str):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    data = load_data()
    init_user(member.id)
    if state.lower() == "on":
        data[str(member.id)]["always_win"] = True
        msg = f"⚡ {member.mention} đã được bật chế độ **luôn thắng**"
    else:
        data[str(member.id)]["always_win"] = False
        msg = f"❌ {member.mention} đã tắt chế độ **luôn thắng**"
    save_data(data)
    await ctx.send(msg)

# ================== HƯỚNG DẪN ==================
@bot.command(name="cachchoi")
async def cachchoi(ctx):
    embed = discord.Embed(
        title="📖 HƯỚNG DẪN CHƠI BOT",
        description="Danh sách lệnh cơ bản",
        color=0x00ffcc
    )
    embed.add_field(
        name="⚽ Game Penalty",
        value="`,sut <trái/phải> <số tiền>`\n`,sut <trái/phải> all` → cược tất cả tiền",
        inline=False
    )
    embed.add_field(
        name="🎁 Daily & Tiền",
        value="`,daily` → Nhận 1000 xu mỗi 24h\n`,sotien` / `,balance` → Xem số dư\n`,give @user <số>` → Chuyển tiền",
        inline=False
    )
    embed.add_field(
        name="🏆 Khác",
        value="`,top` → Xem bảng xếp hạng top 10\n`,cachchoi` → Xem hướng dẫn",
        inline=False
    )
    embed.set_footer(text="🎮 Chúc bạn chơi vui vẻ!")
    await ctx.send(embed=embed)

# ================== SỰ KIỆN ==================
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")

# ================== RUN ==================
bot.run(TOKEN)
