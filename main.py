import discord
from discord.ext import commands
import random
import json
import os
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, request

# ================== CẤU HÌNH ==================
TOKEN = "YOUR_DISCORD_BOT_TOKEN"   # ⚠️ Thay token bot Discord thật
PREFIX = ","
ADMIN_UID = [1265245644558176278]  # ID admin
DATA_FILE = "users.json"
DAILY_CHECK_FILE = "daily_passed.json"
DAILY_LINK = "https://link4m.com/XilfNqMv"   # Link kiếm tiền
API_TOKEN = "68a9db54407b5520a7207b29"       # API token tự đặt

print(f"[API] API_TOKEN đang sử dụng: {API_TOKEN}")

# ================== HÀM LƯU / LOAD ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def init_user(uid):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 0, "last_daily": 0}
        save_data(data)
    return data

def get_balance(uid):
    data = init_user(uid)
    return int(data[str(uid)]["balance"])

def set_balance(uid, amount):
    data = init_user(uid)
    data[str(uid)]["balance"] = max(0, int(amount))
    save_data(data)

def add_balance(uid, amount):
    data = init_user(uid)
    data[str(uid)]["balance"] += int(amount)
    if data[str(uid)]["balance"] < 0:
        data[str(uid)]["balance"] = 0
    save_data(data)

# ================== DAILY CHECK ==================
def load_passed():
    if not os.path.exists(DAILY_CHECK_FILE):
        return {"reset_time": int(time.time()), "users": {}}
    with open(DAILY_CHECK_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {"reset_time": int(time.time()), "users": {}}

def save_passed(data):
    with open(DAILY_CHECK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def has_passed(uid):
    return str(uid) in load_passed().get("users", {})

def mark_passed(uid):
    data = load_passed()
    data["users"][str(uid)] = True
    save_passed(data)

def reset_all_passed():
    save_passed({"reset_time": int(time.time()), "users": {}})

def check_need_reset():
    data = load_passed()
    now = int(time.time())
    if now - data.get("reset_time", 0) >= 86400:
        reset_all_passed()

# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Trạng thái game
state = {
    "win_streak": {},   # uid: số trận thắng liên tiếp
    "forced_lose": {},  # uid: số trận bị ép thua
    "always_win": set(),
    "banned": {}        # uid: timestamp hết hạn cấm
}

def is_banned(uid):
    now = time.time()
    if str(uid) in state["banned"]:
        if state["banned"][str(uid)] > now:
            return True
        else:
            del state["banned"][str(uid)]
    return False

# --------- DAILY ---------
@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    if is_banned(uid): return await ctx.send("🚫 Bạn đang bị cấm chơi!")

    data = init_user(uid)
    now = int(time.time())
    last_daily = data[uid].get("last_daily", 0)

    check_need_reset()
    if now - last_daily < 86400:
        remain = 86400 - (now - last_daily)
        return await ctx.send(f"⏳ Hãy chờ {remain//3600}h{(remain%3600)//60}m nữa!")

    if not has_passed(uid):
        return await ctx.send(f"🔗 Vượt link để nhận daily:\n{DAILY_LINK}?uid={uid}&apitoken={API_TOKEN}")

    reward = 1000
    add_balance(uid, reward)
    data[uid]["last_daily"] = now
    save_data(data)
    await ctx.send(f"🎁 {ctx.author.mention} nhận **{reward} xu**. Số dư: {get_balance(uid):,}")

# --------- BALANCE ---------
@bot.command(aliases=["balance"])
async def bal(ctx):
    uid = str(ctx.author.id)
    if is_banned(uid): return await ctx.send("🚫 Bạn đang bị cấm chơi!")
    await ctx.send(f"💰 Số dư: **{get_balance(uid):,} xu**")

# --------- PENALTY GAME ---------
@bot.command()
async def sut(ctx, huong: str, bet: int):
    uid = str(ctx.author.id)
    if is_banned(uid): return await ctx.send("🚫 Bạn đang bị cấm chơi!")

    huong = huong.lower()
    if huong not in ["trai", "phai"]:
        return await ctx.send("❌ Chọn hướng: trái / phải")

    balance = get_balance(uid)
    if bet <= 0 or bet > balance:
        return await ctx.send("❌ Số tiền cược không hợp lệ!")

    # Nếu bị admin ép luôn thắng
    if uid in state["always_win"]:
        result = "win"
    else:
        # Check ép thua
        if state["forced_lose"].get(uid, 0) > 0:
            result = "lose"
            state["forced_lose"][uid] -= 1
        else:
            chance = random.random()
            result = "win" if chance < 0.35 else "lose"

    # Xử lý kết quả
    if result == "win":
        add_balance(uid, bet)
        state["win_streak"][uid] = state["win_streak"].get(uid, 0) + 1
        if state["win_streak"][uid] >= 6:
            state["forced_lose"][uid] = 3
            state["win_streak"][uid] = 0
        msg = f"⚽ Bạn sút {huong.upper()} → 🥅 Thủ môn bay ngược hướng → ✅ THẮNG! +{bet} xu"
    else:
        set_balance(uid, balance - bet)
        state["win_streak"][uid] = 0
        msg = f"⚽ Bạn sút {huong.upper()} → 🥅 Thủ môn bắt được → ❌ THUA! -{bet} xu"

    await ctx.send(msg + f"\n💰 Số dư: {get_balance(uid):,} xu")

# --------- PLAYER COMMANDS ---------
@bot.command()
async def chuyentien(ctx, member: discord.Member, amount: int):
    uid = str(ctx.author.id)
    tid = str(member.id)
    if is_banned(uid): return await ctx.send("🚫 Bạn đang bị cấm chơi!")
    if amount <= 0: return await ctx.send("❌ Số tiền không hợp lệ!")
    if get_balance(uid) < amount: return await ctx.send("❌ Không đủ tiền!")

    set_balance(uid, get_balance(uid) - amount)
    add_balance(tid, amount)
    await ctx.send(f"💸 {ctx.author.mention} đã chuyển {amount} xu cho {member.mention}")

@bot.command()
async def top(ctx):
    data = load_data()
    top_players = sorted(data.items(), key=lambda x: x[1]["balance"], reverse=True)[:5]
    msg = "**🏆 Top giàu nhất:**\n"
    for i, (uid, info) in enumerate(top_players, 1):
        user = await bot.fetch_user(int(uid))
        msg += f"{i}. {user.name}: {info['balance']:,} xu\n"
    await ctx.send(msg)

@bot.command()
async def xemtien(ctx, member: discord.Member):
    await ctx.send(f"💰 {member.mention} có {get_balance(member.id):,} xu")

# --------- ADMIN COMMANDS ---------
@bot.command()
async def themtien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID: return
    add_balance(member.id, amount)
    await ctx.send(f"✅ Thêm {amount} xu cho {member.mention}")

@bot.command()
async def trutien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID: return
    set_balance(member.id, get_balance(member.id) - amount)
    await ctx.send(f"✅ Trừ {amount} xu của {member.mention}")

@bot.command()
async def dattien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID: return
    set_balance(member.id, amount)
    await ctx.send(f"✅ Đặt số dư {member.mention} = {amount} xu")

@bot.command()
async def luonthang(ctx, member: discord.Member, status: str):
    if ctx.author.id not in ADMIN_UID: return
    uid = str(member.id)
    if status.lower() == "on":
        state["always_win"].add(uid)
        await ctx.send(f"✅ {member.mention} sẽ luôn thắng")
    else:
        state["always_win"].discard(uid)
        await ctx.send(f"✅ {member.mention} trở lại bình thường")

@bot.command()
async def cam(ctx, member: discord.Member, duration: str):
    if ctx.author.id not in ADMIN_UID: return
    uid = str(member.id)
    unit = duration[-1]
    num = int(duration[:-1])
    sec = num * 86400 if unit=="d" else num * 3600 if unit=="h" else num*60
    state["banned"][uid] = time.time() + sec
    await ctx.send(f"🚫 {member.mention} bị cấm {duration}")

# --------- HELP ---------
@bot.command()
async def cachchoi(ctx):
    text = (
        "**📜 Lệnh người chơi:**\n"
        f"{PREFIX}daily → Nhận xu hàng ngày (cần vượt link)\n"
        f"{PREFIX}bal → Xem số dư\n"
        f"{PREFIX}sut <trái/phải> <tiền> → Sút penalty\n"
        f"{PREFIX}chuyentien @user <tiền> → Chuyển tiền\n"
        f"{PREFIX}top → Xem top giàu nhất\n"
        f"{PREFIX}xemtien @user → Xem tiền người khác\n\n"
        "**⚙️ Lệnh admin:**\n"
        f"{PREFIX}themtien @user <số> → Thêm tiền\n"
        f"{PREFIX}trutien @user <số> → Trừ tiền\n"
        f"{PREFIX}dattien @user <số> → Đặt lại số dư\n"
        f"{PREFIX}luonthang @user on/off → Bật tắt luôn thắng\n"
        f"{PREFIX}cam @user <1d/2h/30m> → Cấm chơi"
    )
    await ctx.send(text)

# ================== FLASK API ==================
app = Flask(__name__)

@app.route("/verify")
def verify():
    uid = request.args.get("uid")
    token = request.args.get("apitoken")
    if not uid: return "❌ Thiếu UID!"
    if token != API_TOKEN: return "❌ Sai API token!"
    mark_passed(uid)
    return f"✅ UID {uid} xác nhận vượt link thành công!"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
