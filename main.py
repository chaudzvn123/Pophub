import discord
from discord.ext import commands
import random
import json
import os
import time

# ================== CẤU HÌNH ==================
TOKEN = "YOUR_TOKEN"   # ⚠️ Thay bằng token thật
PREFIX = ","
ADMIN_UID = [1265245644558176278]   # ID admin (int)
DATA_FILE = "users.json"

GIF_GOAL = "https://drive.google.com/uc?export=view&id=1ABCDefGhIJklMNopQRstuVWxyz12345"
GIF_SAVE = "https://media.discordapp.net/attachments/xyz/save.gif"

# ================== LOAD & SAVE ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("[ERROR] JSON hỏng → reset lại")
            return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def init_user(uid):
    uid_str = str(uid)
    data = load_data()
    if uid_str not in data:
        data[uid_str] = {
            "balance": 0,
            "wins": 0,
            "force_lose": 0,
            "always_win": False,
            "last_daily": 0
        }
        save_data(data)
        print(f"[INIT] Tạo user mới {uid_str}")
    return data[uid_str]

def get_balance(uid):
    data = load_data()
    init_user(uid)
    return int(data[str(uid)]["balance"])

def set_balance(uid, amount):
    data = load_data()
    init_user(uid)
    data[str(uid)]["balance"] = max(0, int(amount))
    save_data(data)

def add_balance(uid, amount):
    data = load_data()
    init_user(uid)
    uid_str = str(uid)
    data[uid_str]["balance"] = max(0, int(data[uid_str]["balance"]) + int(amount))
    save_data(data)

# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# --------- DAILY ---------
@bot.command(name="daily")
async def daily(ctx):
    uid = str(ctx.author.id)
    data = load_data()
    init_user(uid)
    print(f"[DAILY] {ctx.author} ({uid}) gọi lệnh")

    now = int(time.time())
    last_daily = int(data[uid].get("last_daily", 0))

    if now - last_daily < 86400:
        remain = 86400 - (now - last_daily)
        hours = remain // 3600
        minutes = (remain % 3600) // 60
        print(f"[DAILY] chưa đủ thời gian, còn {hours}h{minutes}m")
        return await ctx.send(f"⏳ Bạn phải chờ {hours}h {minutes}m nữa để nhận quà daily!")

    reward = 1000
    add_balance(uid, reward)
    data[uid]["last_daily"] = now
    save_data(data)
    print(f"[DAILY] {ctx.author} nhận {reward} xu")
    await ctx.send(f"🎁 {ctx.author.mention} đã nhận **{reward} xu**! Số dư: **{get_balance(uid):,}**")

# --------- BAL ---------
@bot.command(name="bal", aliases=["balance"])
async def bal(ctx):
    uid = str(ctx.author.id)
    balance = get_balance(uid)
    print(f"[BAL] {ctx.author} có {balance} xu")
    await ctx.send(f"💰 Số dư của bạn: **{balance:,} xu**")

# --------- GIVE ---------
@bot.command(name="give")
async def give(ctx, member: discord.Member, amount: int):
    sender = str(ctx.author.id)
    receiver = str(member.id)
    print(f"[GIVE] {ctx.author} → {member}, số tiền: {amount}")

    if amount <= 0:
        return await ctx.send("❌ Số tiền không hợp lệ!")
    if get_balance(sender) < amount:
        return await ctx.send("❌ Bạn không đủ tiền!")

    add_balance(sender, -amount)
    add_balance(receiver, amount)
    print(f"[GIVE] Thành công: {ctx.author} -{amount} → {member} +{amount}")
    await ctx.send(f"✅ {ctx.author.mention} đã chuyển **{amount:,} xu** cho {member.mention}")

# --------- ADMIN ---------
@bot.command(name="addcash")
async def addcash(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    print(f"[ADMIN:addcash] {ctx.author} +{amount} cho {member}")
    add_balance(member.id, amount)
    await ctx.send(f"✅ Đã cộng **{amount:,} xu** cho {member.mention}")

@bot.command(name="settien")
async def settien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    print(f"[ADMIN:settien] {ctx.author} đặt {member} = {amount}")
    set_balance(member.id, amount)
    await ctx.send(f"✅ Đã đặt số dư của {member.mention} = **{amount:,} xu**")

@bot.command(name="bantien")
async def bantien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    if amount <= 0:
        return await ctx.send("⚠️ Số tiền phải > 0.")
    print(f"[ADMIN:bantien] {ctx.author} -{amount} của {member}")
    add_balance(member.id, -amount)
    await ctx.send(f"✅ Đã trừ **{amount:,} xu** của {member.mention}")

@bot.command(name="luonthang")
async def luonthang(ctx, member: discord.Member, mode: str):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    data = load_data()
    uid = str(member.id)
    init_user(uid)

    m = mode.lower()
    if m == "on":
        data[uid]["always_win"] = True
    elif m == "off":
        data[uid]["always_win"] = False
    else:
        return await ctx.send("❌ Sai cú pháp! Dùng: `,luonthang @user on/off`")
    save_data(data)
    print(f"[ADMIN:luonthang] {ctx.author} set {member} always_win={data[uid]['always_win']}")
    await ctx.send(f"⚡ {member.mention} đã {'bật' if m=='on' else 'tắt'} chế độ **luôn thắng**")

# --------- GAME SÚT ---------
@bot.command(name="sut")
async def sut(ctx, huong: str, tien: str):
    uid = str(ctx.author.id)
    user = init_user(uid)
    print(f"[SUT] {ctx.author} chọn {huong} với {tien}")

    # Xử lý số tiền
    if tien.lower() == "all":
        bet = get_balance(uid)
    else:
        try:
            bet = int(tien)
        except ValueError:
            return await ctx.send("❌ Số tiền không hợp lệ! VD: `,sut trái 500`")

    if bet <= 0:
        return await ctx.send("❌ Số tiền phải > 0!")
    if get_balance(uid) < bet:
        return await ctx.send(f"❌ Bạn không đủ tiền! Số dư hiện tại: **{get_balance(uid):,} xu**")

    choice = huong.lower()
    if choice not in ["trái", "phải"]:
        return await ctx.send("⚠️ Bạn phải chọn `trái` hoặc `phải`!")

    # Kết quả
    if user.get("always_win", False):
        goal = choice
    else:
        goal = random.choice(["trái", "phải"])

    if choice == goal:
        add_balance(uid, bet)
        result = f"🎉 {ctx.author.mention} SÚT VÀO!!! Bạn thắng **{bet:,} xu**"
        gif = GIF_GOAL
        color = 0x00ff00
    else:
        add_balance(uid, -bet)
        result = f"💔 {ctx.author.mention} sút trượt! Bạn thua **{bet:,} xu**"
        gif = GIF_SAVE
        color = 0xff0000

    print(f"[SUT] {ctx.author} chọn {choice}, goal={goal}, kết quả: {result}")
    embed = discord.Embed(title="⚽ KẾT QUẢ SÚT", description=result, color=color)
    embed.set_image(url=gif)
    await ctx.send(embed=embed)

# --------- CÁCH CHƠI ---------
@bot.command(name="cachchoi")
async def cachchoi(ctx):
    embed = discord.Embed(
        title="📖 HƯỚNG DẪN & DANH SÁCH LỆNH",
        description="Tất cả lệnh hiện có trong bot:",
        color=0x00ffcc
    )
    embed.add_field(
        name="⚽ Game Penalty",
        value="`,sut [trái/phải] [số tiền | all]`\nVD: `,sut trái 500` hoặc `,sut phải all`",
        inline=False
    )
    embed.add_field(name="🎁 Daily", value="`,daily` → Nhận 1000 xu mỗi 24h", inline=False)
    embed.add_field(name="💸 Tiền tệ", value="`,give @user [số tiền]`\n`,bal` hoặc `,balance` → Xem số dư", inline=False)
    embed.add_field(
        name="⚡ Admin",
        value="`,addcash @user [số tiền]`\n`,settien @user [số tiền]`\n`,bantien @user [số tiền]`\n`,luonthang @user [on/off]`",
        inline=False
    )
    embed.set_footer(text="Chúc bạn chơi vui vẻ ⚽")
    await ctx.send(embed=embed)

# --------- BẮT LỖI ---------
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send("⚠️ Thiếu tham số! Dùng `,cachchoi` để xem hướng dẫn.")
    if isinstance(error, commands.BadArgument):
        return await ctx.send("⚠️ Sai kiểu tham số! Dùng `,cachchoi` để xem hướng dẫn.")
    if isinstance(error, commands.CommandNotFound):
        return await ctx.send("❓ Lệnh không tồn tại. Thử `,cachchoi` nhé.")
    print("[ERROR]", repr(error))

# ================== RUN ==================
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user} (prefix: {PREFIX})")

bot.run(TOKEN)
