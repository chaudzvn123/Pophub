import discord
from discord.ext import commands, tasks
import asyncio
import random
import json
import os

# ================== CẤU HÌNH ==================
TOKEN = "YOUR_TOKEN"   # Thay token bot của bạn
PREFIX = ","
ADMIN_UID = [1265245644558176278]  # Thay bằng Discord ID admin
DATA_FILE = "users.json"

ROUND_TIME = 40   # 40s 1 vòng
LOCK_TIME = 35    # Sau 35s thì cấm cược

# Link ảnh Google Drive (chỉ cần đổi ID)
GIF_WIN = "https://drive.google.com/uc?export=view&id=1ABCDefGhIJklMNopQRstuVWxyz12345"
GIF_LOSE = "https://drive.google.com/uc?export=view&id=1ZYXwvutsRQponMLkjihGFedcba54321"

# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ================== DỮ LIỆU NGƯỜI DÙNG ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_balance(uid):
    data = load_data()
    return data.get(str(uid), 0)

def add_balance(uid, amount):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = 0
    data[uid] += amount
    if data[uid] < 0:
        data[uid] = 0
    save_data(data)

# ================== GAME STATE ==================
current_bets = {}
bet_open = True
history = []  # lưu kết quả tài/xỉu 10 vòng gần nhất
win_streak = {}
force_lose_rounds = {}
game_channel = None  # Kênh chơi (set bằng lệnh ,setchannel)

# ================== LỆNH ==================
@bot.command(name="setchannel")
async def setchannel(ctx):
    global game_channel
    game_channel = ctx.channel
    await ctx.send(f"✅ Đã đặt kênh chơi TÀI XỈU là: {ctx.channel.mention}")

@bot.command(name="datcuoc", aliases=["bet"])
async def dat_cuoc(ctx, choice: str, amount: int):
    global bet_open, current_bets

    valid_choices = ["tài", "tai", "xỉu", "xiu"]
    if not bet_open:
        return await ctx.send("❌ Hiện đã khóa cược, vui lòng chờ vòng sau!")

    if choice.lower() not in valid_choices:
        return await ctx.send("❌ Chỉ được chọn **tài** hoặc **xỉu**!")
    if amount <= 0:
        return await ctx.send("❌ Số tiền cược phải lớn hơn 0!")

    balance = get_balance(ctx.author.id)
    if balance < amount:
        return await ctx.send(f"❌ Bạn không đủ tiền! Số dư: {balance:,} xu")

    if ctx.author.id in current_bets:
        return await ctx.send("❌ Bạn đã đặt cược rồi, không thể đặt thêm!")

    # Trừ tiền tạm
    add_balance(ctx.author.id, -amount)
    user_choice = "tài" if choice.lower().startswith("t") else "xỉu"
    current_bets[ctx.author.id] = {"choice": user_choice, "amount": amount}

    await ctx.send(f"✅ {ctx.author.mention} đã đặt **{amount:,} xu** vào **{user_choice.upper()}**")

@bot.command(name="addcash")
async def addcash(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    add_balance(member.id, amount)
    await ctx.send(f"✅ Đã cộng **{amount:,} xu** cho {member.mention}")

@bot.command(name="give")
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("❌ Số tiền phải lớn hơn 0!")
    if get_balance(ctx.author.id) < amount:
        return await ctx.send("❌ Bạn không đủ tiền!")
    add_balance(ctx.author.id, -amount)
    add_balance(member.id, amount)
    await ctx.send(f"✅ {ctx.author.mention} đã chuyển **{amount:,} xu** cho {member.mention}")

@bot.command(name="cachchoi")
async def cachchoi(ctx):
    text = """
🎲 **CÁCH CHƠI TÀI XỈU**
- Lệnh chính:
  • `,setchannel` → Đặt kênh chơi
  • `,open` → Admin mở game
  • `,stop` → Admin dừng game
  • `,datcuoc <tài/xỉu> <xu>` → Đặt cược
  • `,give <@người chơi> <xu>` → Chuyển tiền
  • `,addcash <@người chơi> <xu>` → Admin cho tiền
  • `,soicau` → Admin soi cầu
  • `,cachchoi` → Xem hướng dẫn

- 1 ván kéo dài **40 giây**:
  • 35 giây đầu: mở cược
  • 5 giây cuối: khoá cược & lắc xúc xắc

- Thắng: nhận lại **gấp đôi số xu cược**
- Thua: mất số xu đã cược
"""
    await ctx.send(text)

@bot.command(name="soicau")
async def soicau(ctx):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    if len(history) < 3:
        return await ctx.send("📊 Chưa có đủ dữ liệu để soi cầu (cần ít nhất 3 kết quả).")
    text = " → ".join([h.upper() for h in history])
    last3 = history[-3:]
    prediction = None
    if last3[0] == last3[1] == last3[2]:
        prediction = "XỈU" if last3[-1] == "TÀI" else "TÀI"
    elif last3[0] != last3[1] and last3[1] != last3[2]:
        prediction = last3[0].upper()
    else:
        prediction = random.choice(["TÀI", "XỈU"])
    embed = discord.Embed(
        title="🔮 SOI CẦU TÀI XỈU",
        description=f"10 kết quả gần nhất:\n{text}\n\n👉 Dự đoán lần tiếp theo: **{prediction}**",
        color=0x00ffcc
    )
    await ctx.send(embed=embed)

# ================== VÒNG TỰ ĐỘNG ==================
@tasks.loop(seconds=ROUND_TIME)
async def tai_xiu_auto():
    global current_bets, bet_open, history

    if not game_channel:
        return

    # Bắt đầu vòng mới
    current_bets = {}
    bet_open = True
    await game_channel.send("🎲 Vòng **TÀI XỈU** mới bắt đầu! Bạn có 35s để đặt cược.\nDùng lệnh: `,datcuoc <tài/xỉu> <số xu>`")

    await asyncio.sleep(LOCK_TIME)
    bet_open = False
    await game_channel.send("⏳ Đã hết thời gian cược! Còn 5s nữa sẽ lắc xúc xắc...")

    await asyncio.sleep(ROUND_TIME - LOCK_TIME)
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "tài" if total > 10 else "xỉu"
    history.append(result)
    if len(history) > 10:
        history.pop(0)

    winners, losers = [], []
    for uid, bet in current_bets.items():
        if force_lose_rounds.get(uid, 0) > 0:
            force_lose_rounds[uid] -= 1
            losers.append((uid, bet["amount"]))
            win_streak[uid] = 0
            continue

        if bet["choice"] == result:
            add_balance(uid, bet["amount"] * 2)
            winners.append((uid, bet["amount"]))
            win_streak[uid] = win_streak.get(uid, 0) + 1
            if win_streak[uid] >= 4:
                force_lose_rounds[uid] = 2
                win_streak[uid] = 0
        else:
            losers.append((uid, bet["amount"]))
            win_streak[uid] = 0

    embed = discord.Embed(
        title="🎲 KẾT QUẢ TÀI XỈU",
        color=0x00ff00
    )
    embed.add_field(name="Xúc xắc", value=f"🎲 {dice[0]} - {dice[1]} - {dice[2]}", inline=True)
    embed.add_field(name="Tổng điểm", value=f"**{total}**", inline=True)
    embed.add_field(name="Kết quả", value=f"**{result.upper()}**", inline=True)

    if winners:
        text = "\n".join([f"<@{uid}> thắng {amt:,} xu" for uid, amt in winners])
        embed.add_field(name="🏆 Người thắng", value=text, inline=False)
    if losers:
        text = "\n".join([f"<@{uid}> thua {amt:,} xu" for uid, amt in losers])
        embed.add_field(name="💀 Người thua", value=text, inline=False)

    await game_channel.send(embed=embed)

    # 🎉 Hiệu ứng GIF ăn mừng/thua
    if winners:
        await game_channel.send("🎉 ĂN MỪNG!!! 🎉\n" + GIF_WIN)
    elif losers:
        await game_channel.send("😢 Thua rồi...\n" + GIF_LOSE)

# ================== LỆNH QUẢN LÝ ==================
@bot.command(name="open")
async def open_game(ctx):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    if not tai_xiu_auto.is_running():
        tai_xiu_auto.start()
        await ctx.send("✅ Đã bắt đầu game TÀI XỈU tự động!")

@bot.command(name="stop")
async def stop_game(ctx):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền!")
    if tai_xiu_auto.is_running():
        tai_xiu_auto.stop()
        await ctx.send("🛑 Đã dừng game TÀI XỈU!")

# ================== SỰ KIỆN ==================
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")

# ================== CHẠY BOT ==================
bot.run(TOKEN)
