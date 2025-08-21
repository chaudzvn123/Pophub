import discord
from discord.ext import commands
import json
import os
import random

# ================== CẤU HÌNH ==================
PREFIX = ","
ADMIN_UID = [1265245644558176278]  # Thay ID này bằng Discord ID của bạn
DATA_FILE = "users.json"

# ================== LOAD & SAVE DATA ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

users = load_data()

def get_balance(uid): 
    return users.get(str(uid), 0)

def set_balance(uid, amount): 
    users[str(uid)] = max(0, amount)
    save_data(users)

def add_balance(uid, amount): 
    users[str(uid)] = max(0, get_balance(uid) + amount)
    save_data(users)

# ================== BOT SETUP ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)  # ⚡ FIX help

@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    print(f"📊 Prefix: {PREFIX}")
    print(f"🎮 Bot sẵn sàng chơi tài xỉu!")

# ================== COMMANDS ==================

@bot.command(name="sotiendangco", aliases=["balance", "bal"])
async def check_balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    balance = get_balance(target.id)
    
    embed = discord.Embed(
        title="💰 Số Dư Hiện Tại",
        description=f"{target.mention} đang có **{balance:,} xu**",
        color=0x00ff00
    )
    embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
    await ctx.send(embed=embed)

@bot.command(name="addtien", aliases=["add"])
async def add_money(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
    if amount <= 0:
        return await ctx.send("❌ Số tiền phải lớn hơn 0!")
    
    add_balance(member.id, amount)
    embed = discord.Embed(
        title="✅ Thêm Tiền Thành Công",
        description=f"Đã cộng **{amount:,} xu** cho {member.mention}",
        color=0x00ff00
    )
    embed.add_field(name="Số dư mới", value=f"{get_balance(member.id):,} xu", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="settien", aliases=["set"])
async def set_money(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_UID:
        return await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
    if amount < 0:
        return await ctx.send("❌ Số tiền không thể âm!")
    
    set_balance(member.id, amount)
    embed = discord.Embed(
        title="✅ Đặt Lại Số Dư",
        description=f"Đã đặt số dư của {member.mention} thành **{amount:,} xu**",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.command(name="taixiu", aliases=["tx"])
async def tai_xiu_game(ctx, choice: str, amount: int):
    valid_choices = ["tài", "tai", "xỉu", "xiu"]
    if choice.lower() not in valid_choices:
        return await ctx.send("❌ Chỉ được chọn **tài** hoặc **xỉu**!")
    if amount <= 0:
        return await ctx.send("❌ Số tiền cược phải lớn hơn 0!")
    
    current_balance = get_balance(ctx.author.id)
    if amount > current_balance:
        return await ctx.send(f"❌ Không đủ tiền! Bạn chỉ có **{current_balance:,} xu**")
    
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "tài" if total > 10 else "xỉu"
    
    user_choice = "tài" if choice.lower().startswith("t") else "xỉu"
    is_win = user_choice == result
    
    if is_win:
        add_balance(ctx.author.id, amount)
        win_amount = amount
    else:
        add_balance(ctx.author.id, -amount)
        win_amount = -amount
    
    new_balance = get_balance(ctx.author.id)
    
    embed = discord.Embed(
        title="🎲 KẾT QUẢ TÀI XỈU",
        color=0x00ff00 if is_win else 0xff0000
    )
    embed.add_field(name="Xúc xắc", value=f"🎲 {dice[0]} - {dice[1]} - {dice[2]}", inline=True)
    embed.add_field(name="Tổng điểm", value=f"**{total}**", inline=True)
    embed.add_field(name="Kết quả", value=f"**{result.upper()}**", inline=True)
    embed.add_field(name="Lựa chọn của bạn", value=f"**{user_choice.upper()}**", inline=True)
    embed.add_field(name="Số tiền cược", value=f"{amount:,} xu", inline=True)
    embed.add_field(name="Kết quả", value=f"{'✅ THẮNG' if is_win else '❌ THUA'}", inline=True)
    embed.add_field(name="💰 Số dư mới", value=f"{new_balance:,} xu", inline=False)
    embed.set_footer(text=f"Người chơi: {ctx.author.display_name}")
    
    await ctx.send(embed=embed)

@bot.command(name="help", aliases=["h"])
async def help_command(ctx):
    embed = discord.Embed(
        title="🎮 HƯỚNG DẪN SỬ DỤNG BOT TÀI XỈU",
        description="Dưới đây là các lệnh có sẵn:",
        color=0x0099ff
    )
    embed.add_field(name="🎲 Game Tài Xỉu",
        value=f"`{PREFIX}taixiu <tài/xỉu> <số xu>`\nVí dụ: `{PREFIX}taixiu tài 1000`", inline=False)
    embed.add_field(name="💰 Kiểm tra số dư",
        value=f"`{PREFIX}sotiendangco [@người chơi]`\nVí dụ: `{PREFIX}sotiendangco` hoặc `{PREFIX}bal @user`", inline=False)
    embed.add_field(name="🎯 Luật chơi Tài Xỉu",
        value="• Tổng 3 xúc xắc từ 11-18: **TÀI**\n• Tổng 3 xúc xắc từ 3-10: **XỈU**\n• Thắng = tiền cược\n• Thua = mất tiền cược", inline=False)
    if ctx.author.id in ADMIN_UID:
        embed.add_field(name="⚙️ Lệnh Admin",
            value=f"`{PREFIX}addtien <@user> <số xu>`\n`{PREFIX}settien <@user> <số xu>`", inline=False)
    embed.set_footer(text="Chúc bạn may mắn! 🍀")
    await ctx.send(embed=embed)

@bot.command(name="top", aliases=["leaderboard"])
async def leaderboard(ctx):
    if not users:
        return await ctx.send("📊 Chưa có dữ liệu người chơi nào!")
    
    sorted_users = sorted(users.items(), key=lambda x: x[1], reverse=True)
    top_10 = sorted_users[:10]
    
    embed = discord.Embed(
        title="🏆 BẢNG XẾP HẠNG TOP 10",
        description="Những người chơi giàu nhất server:",
        color=0xffd700
    )
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    leaderboard_text = ""
    for i, (user_id, balance) in enumerate(top_10):
        try:
            user = bot.get_user(int(user_id))
            username = user.display_name if user else f"User {str(user_id)[:4]}..."
            leaderboard_text += f"{medals[i]} **{username}**: {balance:,} xu\n"
        except:
            leaderboard_text += f"{medals[i]} **Unknown User**: {balance:,} xu\n"
    embed.description = leaderboard_text
    await ctx.send(embed=embed)

# ================== ERROR HANDLER ==================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Thiếu tham số! Sử dụng `{PREFIX}help` để xem hướng dẫn.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Tham số không hợp lệ! Kiểm tra lại cú pháp.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Lệnh không tồn tại! Sử dụng `{PREFIX}help` để xem danh sách lệnh.")
    else:
        await ctx.send("⚠️ Đã xảy ra lỗi, vui lòng thử lại sau.")
        raise error

# ================== RUN BOT ==================
try:
    token = os.getenv("TOKEN") or ""
    if not token:
        raise RuntimeError("🚨 Thiếu token! Hãy thêm TOKEN vào Secrets/biến môi trường.")
    # In ra một chút info để tự kiểm tra (không lộ token)
    print(f"Starting bot... token_prefix={token[:8]}*** len={len(token)}")
    bot.run(token)

except discord.errors.LoginFailure:
    print("❌ Token không hợp lệ hoặc không phải **Bot Token**.")
    print("👉 Vào Developer Portal → Bot → Reset Token → Copy lại BOT TOKEN và đặt vào biến môi trường TOKEN.")

except discord.errors.PrivilegedIntentsRequired as e:
    print("❌ Chưa bật **Privileged Gateway Intents** cho bot.")
    print("👉 Vào Developer Portal → Bot → Bật 'MESSAGE CONTENT INTENT' (và nên bật cả 'SERVER MEMBERS INTENT').")
    print(f"Chi tiết: {e}")

except discord.HTTPException as e:
    if e.status == 429:
        print("🚫 Discord chặn kết nối do quá nhiều request (HTTP 429). Thử chạy lại sau.")
    else:
        print(f"HTTPException: Status={e.status} Text={e.text}")
        raise

except Exception as e:
    print(f"⚠️ Lỗi không xác định: {type(e).__name__}: {e}")
    raise
