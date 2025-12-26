import os
import random
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from faker import Faker
from schwifty import IBAN

# ================= CONFIG =================

TOKEN = os.getenv("8267761544:AAEjUCwfvYo_dIpSbeNQf4mhbJGpNbAH5ks")  # Railway ENV variable

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
fake = Faker()

# ================= HELPERS =================

def parse_bin(text):
    digits = "".join(c for c in text if c.isdigit())
    return digits[:6] if len(digits) >= 6 else None

def masked_card(bin_code):
    last4 = "".join(str(random.randint(0, 9)) for _ in range(4))
    return f"{bin_code}******{last4}"

def random_date():
    mm = str(random.randint(1, 12)).zfill(2)
    yy = str(random.randint(2026, 2035))
    return mm, yy

async def get_bin_info(bin_code):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://lookup.binlist.net/{bin_code}", timeout=10
            ) as r:
                if r.status != 200:
                    return None
                d = await r.json()
    except Exception:
        return None

    return {
        "scheme": (d.get("scheme") or "N/A").upper(),
        "type": (d.get("type") or "N/A").upper(),
        "bank": d.get("bank", {}).get("name", "N/A"),
        "country": d.get("country", {}).get("name", "N/A"),
        "emoji": d.get("country", {}).get("emoji", "")
    }

# ================= COMMANDS =================

@dp.message_handler(commands=["gen"])
async def gen_cmd(msg: types.Message):
    bin_code = parse_bin(msg.text)
    if not bin_code:
        await msg.reply("❌ Please send a valid 6-digit BIN")
        return

    cards = []
    for _ in range(10):
        mm, yy = random_date()
        cards.append(f"{masked_card(bin_code)}|{mm}|{yy}|***")

    info = await get_bin_info(bin_code)

    text = (
        f"𝗕𝗜𝗡 ⇾ {bin_code}\n"
        f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ 10\n\n"
        + "\n".join(cards)
    )

    if info:
        text += (
            f"\n\n𝗜𝗻𝗳𝗼: {info['scheme']} - {info['type']}\n"
            f"𝗕𝗮𝗻𝗸: {info['bank']}\n"
            f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {info['country']} {info['emoji']}"
        )

    await msg.reply(text)

@dp.message_handler(commands=["mass"])
async def mass_cmd(msg: types.Message):
    args = msg.text.split()
    if len(args) < 3:
        await msg.reply("Usage: /mass BIN AMOUNT")
        return

    bin_code = parse_bin(args[1])
    if not bin_code:
        await msg.reply("Invalid BIN")
        return

    try:
        amount = min(int(args[2]), 50)
    except ValueError:
        await msg.reply("Invalid amount")
        return

    cards = []
    for _ in range(amount):
        mm, yy = random_date()
        cards.append(f"{masked_card(bin_code)}|{mm}|{yy}|***")

    await msg.reply("\n".join(cards))

@dp.message_handler(commands=["bin"])
async def bin_cmd(msg: types.Message):
    bin_code = parse_bin(msg.text)
    if not bin_code:
        await msg.reply("Usage: /bin 412236")
        return

    info = await get_bin_info(bin_code)
    if not info:
        await msg.reply("BIN info not found.")
        return

    await msg.reply(
        f"𝗕𝗜𝗡 ⇾ {bin_code}\n"
        f"𝗜𝗻𝗳𝗼: {info['scheme']} - {info['type']}\n"
        f"𝗕𝗮𝗻𝗸: {info['bank']}\n"
        f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {info['country']} {info['emoji']}"
    )

@dp.message_handler(commands=["iban"])
async def iban_cmd(msg: types.Message):
    args = msg.text.split()
    if len(args) < 2:
        await msg.reply("Usage: /iban DE")
        return

    country = args[1].upper()
    try:
        iban = IBAN.random(country_code=country)
    except Exception:
        await msg.reply("Invalid country code")
        return

    await msg.reply(f"🏦 IBAN ({country})\n\n{iban}")

@dp.message_handler(commands=["fake"])
async def fake_cmd(msg: types.Message):
    country = msg.text.split()[1] if len(msg.text.split()) > 1 else "US"

    fake_addr = (
        f"📍 Fake Address ({country.upper()})\n\n"
        f"{fake.name()}\n"
        f"{fake.street_address()}\n"
        f"{fake.city()}, {fake.state()} {fake.postcode()}\n"
        f"{fake.country()}"
    )
    await msg.reply(fake_addr)

@dp.message_handler(commands=["me"])
async def me_cmd(msg: types.Message):
    u = msg.from_user
    await msg.reply(
        f"👤 Profile Info\n\n"
        f"ID: {u.id}\n"
        f"Username: @{u.username}\n"
        f"Name: {u.full_name}"
    )

@dp.message_handler(commands=["menu"])
async def menu_cmd(msg: types.Message):
    await msg.reply(
        "📜 BOT COMMANDS MENU\n\n"
        "💳 BIN Info\n"
        "├ /bin {6-digit}\n\n"
        "🔐 CC Generator (masked)\n"
        "├ /gen BIN\n"
        "├ /mass BIN AMOUNT\n\n"
        "ℹ️ IBAN Generator\n"
        "├ /iban COUNTRY_CODE\n\n"
        "📍 Fake Address\n"
        "├ /fake COUNTRY_CODE\n\n"
        "👤 Profile Info\n"
        "└ /me"
    )

# ================= START =================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)