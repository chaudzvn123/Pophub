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

function random(len) {
  const c = "abcdefghijklmnopqrstuvwxyz0123456789";
  return [...Array(len)].map(() => c[Math.floor(Math.random() * c.length)]).join("");
}

function createVMOSAccount() {
  const tk = `vmos${random(12)}@hoang.cloud`;
  const mk = random(16);
  return `${tk}|${mk}`;
}

// ❌ CHỖ DUY NHẤT BẠN TỰ GẮN API
async function buyVmosFree6h(username, password) {
  console.log("LOGIN:", username, password);
  await new Promise(r => setTimeout(r, 1500));
  return true; // mock
}

client.on("ready", () => {
  console.log("🤖 Bot ready");
});

client.on("messageCreate", async (msg) => {
  if (msg.author.bot) return;

  // Tạo tài khoản
  if (msg.content === "!getvmos") {
    return msg.reply(`\`\`\`${createVMOSAccount()}\`\`\``);
  }

  // Mua VMOS
  if (msg.content === "!buyvmos") {
    await msg.reply("📥 Nhập tài khoản theo dạng: `tk|mk`");

    const collected = await msg.channel.awaitMessages({
      filter: m => m.author.id === msg.author.id,
      max: 1,
      time: 30000
    });

    if (!collected.size) return msg.reply("⏰ Hết thời gian.");

    const input = collected.first().content.trim();
    if (!input.includes("|")) return msg.reply("❌ Sai định dạng `tk|mk`");

    const [tk, mk] = input.split("|");

    try {
      await msg.reply("⏳ Đang mua máy VMOS free 6h...");
      const ok = await buyVmosFree6h(tk, mk);
      msg.reply(ok ? "✅ Mua máy thành công" : "❌ Mua máy thất bại");
    } catch (e) {
      msg.reply("⚠️ Chưa triển khai API VMOS");
    }
  }
});

client.login(process.env.DISCORD_TOKEN);
