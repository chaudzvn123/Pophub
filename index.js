import { Client, GatewayIntentBits } from "discord.js";
import dotenv from "dotenv";
dotenv.config();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

// ====== TOOL ======
function randomString(length) {
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
}

function createAccount() {
  const user = `vmos${randomString(12)}@hoang.cloud`;
  const pass = randomString(16);
  return `${user}|${pass}`;
}

// ====== PLACEHOLDER BUY ======
async function buyFreeMachine(token, username, password) {
  // ❗ CHỈ LÀ MÔ PHỎNG
  console.log("TOKEN:", token);
  console.log("BUY WITH:", username, password);

  await new Promise(r => setTimeout(r, 2000));
  return true;
}

// ====== BOT ======
client.on("ready", () => {
  console.log(`🤖 Logged in as ${client.user.tag}`);
});

client.on("messageCreate", async (msg) => {
  if (msg.author.bot) return;

  // !getvmos
  if (msg.content === "!getvmos") {
    const account = createAccount();
    msg.reply(
      `✅ **Tài khoản đã tạo:**\n\`\`\`${account}\`\`\``
    );
  }

  // !buy
  if (msg.content === "!buy") {
    msg.reply("📥 **Nhập tài khoản theo dạng:** `tk|mk`");

    const filter = m => m.author.id === msg.author.id;
    const collected = await msg.channel.awaitMessages({
      filter,
      max: 1,
      time: 30000
    });

    if (!collected.size) {
      return msg.reply("⏰ Hết thời gian nhập!");
    }

    const input = collected.first().content.trim();

    if (!input.includes("|")) {
      return msg.reply("❌ Sai định dạng! Dùng: `tk|mk`");
    }

    const [username, password] = input.split("|");

    msg.reply("⏳ Đang mua máy free 6h...");

    const fakeToken = "YOUR_TOKEN_HERE";
    const result = await buyFreeMachine(fakeToken, username, password);

    if (result) {
      msg.reply("✅ **Mua máy thành công (mock)**");
    } else {
      msg.reply("❌ **Mua máy thất bại**");
    }
  }
});

client.login(process.env.DISCORD_TOKEN);
