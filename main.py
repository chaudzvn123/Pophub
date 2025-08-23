import discord
from discord.ext import commands, tasks
import random
import json
import os
import time
import threading
from flask import Flask, request

# ================== CẤU HÌNH ==================
TOKEN = "YOUR_TOKEN"   # ⚠️ Thay token thật
PREFIX = ","
ADMIN_UID = [1265245644558176278]   # ID admin
DATA_FILE = "users.json"
DAILY_CHECK_FILE = "daily_passed.json"
DAILY_LINK = "https://link4m.com/SOolau4E"   # Link kiếm tiền

# ================== HÀM LƯU / LOAD ==================
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
    if uid_str not in data or not isinstance(data[uid_str], dict):
        data[uid_str] = {
            "balance": 0,
            "last_daily": 0
        }
        save_data(data)
        print(f"[INIT] Khởi tạo user {uid_str}")
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
    uid_str = str(uid)
    data[uid_str]["balance"] = max(0, int(data[uid_str]["balance"]) + int(amount))
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
    data = load_passed()
    return str(uid) in data.get("users", {})

def mark_passed(uid):
    data = load_passed()
    data["users"][str(uid)] = True
    save_passed(data)

def reset_all_passed():
    new_data = {"reset_time": int(time.time()), "users": {}}
    save_passed(new_data)
    print("🔄 [RESET] Daily link đã reset toàn bộ")

def check_need_reset():
    data = load_passed()
    now = int(time.time())
    if now - data.get("reset_time", 0) >= 86400:  # 24h
        reset_all_passed()
        return True
    return False

# ================== DISCORD BOT ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# --------- DAILY ---------
@bot.command(name="daily")
async def daily(ctx):
    uid = str(ctx.author.id)
    data = init_user(uid)
    now = int(time.time())
    last_daily = int(data[uid].get("last_daily", 0))

    # Kiểm tra nếu đến thời gian reset → reset luôn
    check_need_reset()

    # Cooldown 24h cho mỗi user
    if now - last_daily < 86400:
        remain = 86400 - (now - last_daily)
        hours = remain // 3600
        minutes = (remain % 3600) // 60
        return await ctx.send(f"⏳ Bạn phải chờ {hours}h {minutes}m nữa!")

    # Nếu user chưa vượt link trong vòng reset mới
    if not has_passed(uid):
        return await ctx.send(
            f"🔗 Hết thời gian! Vui lòng vượt lại link để nhận daily:\n{DAILY_LINK}?uid={uid}"
        )

    # Nếu đã vượt → thưởng
    reward = 1000
    add_balance(uid, reward)
    data[uid]["last_daily"] = now
    save_data(data)

    await ctx.send(f"🎁 {ctx.author.mention} nhận **{reward} xu**! Số dư: **{get_balance(uid):,}**")

# --------- BAL ---------
@bot.command(name="bal", aliases=["balance"])
async def bal(ctx):
    uid = str(ctx.author.id)
    balance = get_balance(uid)
    await ctx.send(f"💰 Số dư của bạn: **{balance:,} xu**")

# ================== FLASK API ==================
app = Flask(__name__)

@app.route("/verify")
def verify():
    uid = request.args.get("uid")
    if not uid:
        return "❌ Thiếu tham số UID!"
    mark_passed(uid)
    return f"✅ UID {uid} đã xác nhận vượt link thành công! Hãy quay lại Discord và gõ ,daily để nhận thưởng."

# ================== RUN BOT + API SONG SONG ==================
def run_flask():
    app.run(host="0.0.0.0", port=5000)

@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user} (prefix: {PREFIX})")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
