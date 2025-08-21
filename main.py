import discord
from discord.ext import commands
import json, os, random

TOKEN = "NHẬP_TOKEN_BOT_VÀO_ĐÂY"
PREFIX = ","
ADMIN_UID = [1265245644558176278]
DATA_FILE = "users.json"

# ================== LOAD & SAVE ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

users = load_data()

def get_balance(uid): return users.get(str(uid), 0)
def set_balance(uid, amount): users[str(uid)] = max(0, amount); save_data(users)
def add_balance(uid, amount): users[str(uid)] = max(0, get_balance(uid) + amount); save_data(users)

# ================== BOT ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")

# ================== LỆNH ==================
@bot.command()
async def sotiendangco(ctx, member: discord.Member=None):
    target = member or ctx.author
    await ctx.send(f"💰 {target.mention} đang có {get_balance(target.id)} xu")

@bot.command()
async def addtien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID: return await ctx.send("❌ Không có quyền")
    add_balance(member.id, amount)
    await ctx.send(f"✅ Cộng {amount} xu cho {member.mention}")

@bot.command()
async def settien(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID: return await ctx.send("❌ Không có quyền")
    set_balance(member.id, amount)
    await ctx.send(f"✅ Đặt lại số dư {member.mention} thành {amount}")

@bot.command()
async def taixiu(ctx, choice: str, amount: int):
    if choice not in ["tài","tai","xỉu","xiu"]: return await ctx.send("❌ Chỉ chọn tài hoặc xỉu")
    bal = get_balance(ctx.author.id)
    if amount > bal: return await ctx.send("❌ Không đủ tiền")
    dice = [random.randint(1,6) for _ in range(3)]
    total = sum(dice)
    result = "tài" if total>10 else "xỉu"
    if (choice.startswith("t") and result=="tài") or (choice.startswith("x") and result=="xỉu"):
        add_balance(ctx.author.id, amount)
        msg = f"🎲 {dice} = {total} → {result.upper()}\n✅ Bạn thắng {amount} xu!"
    else:
        add_balance(ctx.author.id, -amount)
        msg = f"🎲 {dice} = {total} → {result.upper()}\n❌ Bạn thua {amount} xu!"
    await ctx.send(msg + f"\n💰 Số dư mới: {get_balance(ctx.author.id)}")

bot.run(TOKEN)
