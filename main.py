# ================== CÀI THƯ VIỆN (chỉ cần chạy 1 lần) ==================
# Nếu chạy trong CodePad thì cần dòng này để cài discord.py
# Nếu bạn đã cài rồi thì có thể bỏ qua
try:
    import discord
    from discord.ext import commands
except ImportError:
    import os
    os.system("pip install discord.py")
    import discord
    from discord.ext import commands

import json
import random
import os

# ================== CẤU HÌNH ==================
TOKEN = "NHẬP_TOKEN_BOT_VÀO_ĐÂY"
PREFIX = ","
ADMIN_UID = [1265245644558176278]  # Thay UID admin Discord

DATA_FILE = "users.json"

# ================== LOAD & SAVE TIỀN ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

users = load_data()

def get_balance(uid):
    return users.get(str(uid), 0)

def set_balance(uid, amount):
    users[str(uid)] = max(0, amount)  # không cho âm tiền
    save_data(users)

def add_balance(uid, amount):
    users[str(uid)] = max(0, get_balance(uid) + amount)
    save_data(users)

# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ================== LỆNH ADMIN ==================
@bot.command()
async def addtien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền dùng lệnh này.")
    if amount <= 0:
        return await ctx.send("❌ Số tiền phải lớn hơn 0.")
    add_balance(member.id, amount)
    await ctx.send(f"✅ Đã cộng {amount} xu cho {member.mention}. Số dư mới: {get_balance(member.id)}")

@bot.command()
async def settien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền dùng lệnh này.")
    if amount < 0:
        return await ctx.send("❌ Số tiền không hợp lệ.")
    set_balance(member.id, amount)
    await ctx.send(f"✅ Đã đặt lại số dư của {member.mention} thành {amount}")

# ================== LỆNH XEM SỐ DƯ ==================
@bot.command(name="sotiendangco")
async def sotiendangco(ctx, member: discord.Member = None):
    target = member or ctx.author
    bal = get_balance(target.id)
    if member:
        await ctx.send(f"💰 Số tiền hiện có của {target.mention}: {bal} xu")
    else:
        await ctx.send(f"💰 Số tiền hiện có của bạn: {bal} xu")

# ================== LỆNH CHƠI TÀI XỈU ==================
@bot.command()
async def taixiu(ctx, choice: str = None, amount: int = None):
    if choice is None or amount is None:
        return await ctx.send("❌ Cú pháp đúng: `,taixiu <tài/xỉu> <số tiền>`")

    choice = choice.lower()
    if choice not in ["tài", "tai", "xỉu", "xiu"]:
        return await ctx.send("❌ Vui lòng chọn 'tài' hoặc 'xỉu'")

    balance = get_balance(ctx.author.id)
    if amount <= 0:
        return await ctx.send("❌ Số tiền cược phải lớn hơn 0")
    if amount > balance:
        return await ctx.send(f"❌ Bạn không đủ tiền! Số dư hiện tại: {balance}")

    # Tung 3 xúc xắc
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)

    # Luật tài xỉu: <=10 là xỉu, >10 là tài
    result = "tài" if total > 10 else "xỉu"

    win = False
    if (choice.startswith("t") and result == "tài") or (choice.startswith("x") and result == "xỉu"):
        win = True

    if win:
        add_balance(ctx.author.id, amount)
        await ctx.send(
            f"🎲 Kết quả: {dice} = {total} → **{result.upper()}**\n"
            f"✅ Bạn thắng {amount} xu!\n💰 Số tiền hiện có: {get_balance(ctx.author.id)}"
        )
    else:
        add_balance(ctx.author.id, -amount)
        await ctx.send(
            f"🎲 Kết quả: {dice} = {total} → **{result.upper()}**\n"
            f"❌ Bạn thua {amount} xu!\n💰 Số tiền hiện có: {get_balance(ctx.author.id)}"
        )

# ================== CHẠY BOT ==================
bot.run(TOKEN)
