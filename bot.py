import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from invoice import generate_invoice

TOKEN = "8512648461:AAHR3PdIKmQT0Ewui3D3rxPjz0iqf9uY0EM"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# -------------------------
# MENU BUTTONS
# -------------------------
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Create Invoice")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# -------------------------
# USER STATE STORAGE
# States:
#   None           → idle
#   "client"       → waiting for client name
#   "item_name"    → waiting for item name (or "/" to finish)
#   "item_qty"     → waiting for quantity
#   "item_price"   → waiting for unit price
# -------------------------
user_data = {}
user_state = {}
invoice_counter = 1


# -------------------------
# START COMMAND
# -------------------------
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = None
    user_data[user_id] = {}
    await message.answer(
        "👋 Welcome to Invoice Bot!\n\nChoose an option below 👇",
        reply_markup=main_menu
    )


# -------------------------
# MAIN MESSAGE HANDLER
# -------------------------
@dp.message()
async def handle_messages(message: types.Message):
    global invoice_counter

    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in user_state:
        user_state[user_id] = None
        user_data[user_id] = {}

    current_state = user_state[user_id]

    # -----------------------------------------------
    # IDLE
    # -----------------------------------------------
    if current_state is None:
        if text == "➕ Create Invoice":
            user_data[user_id] = {"client": "", "items": []}
            user_state[user_id] = "client"
            await message.answer("🧾 Enter client name:")

        elif text == "📄 My Invoices":
            await message.answer("📁 Feature coming next: invoice history database.")

        elif text == "⚙️ Settings":
            await message.answer("⚙️ Settings coming next (currency, TVA, branding).")

        else:
            await message.answer("👇 Please choose an option:", reply_markup=main_menu)
        return

    # -----------------------------------------------
    # STEP 1 — Client name
    # -----------------------------------------------
    if current_state == "client":
        user_data[user_id]["client"] = text
        user_state[user_id] = "item_name"
        await message.answer(
            "📦 Now enter your items one by one.\n\n"
            "Send */* when you're done with all items.",
            parse_mode="Markdown"
        )
        await message.answer("📝 Item name (or / to finish):")
        return

    # -----------------------------------------------
    # STEP 2 — Item name (or "/" to finish)
    # -----------------------------------------------
    if current_state == "item_name":
        if text == "/":
            items = user_data[user_id].get("items", [])
            if not items:
                await message.answer("⚠️ You haven't added any items yet!\n\n📝 Item name:")
                return

            total = sum(item["qty"] * item["unit_price"] for item in items)

            summary = "\n".join(
                f"  • {item['name']} x{item['qty']} × {item['unit_price']:,.0f} DA = {item['qty'] * item['unit_price']:,.0f} DA"
                for item in items
            )

            await message.answer(
                f"🧾 *Invoice Summary*\n\n"
                f"👤 Client: {user_data[user_id]['client']}\n\n"
                f"📦 Items:\n{summary}\n\n"
                f"💰 *Total: {total:,.0f} DA*\n\n"
                f"⏳ Generating your invoice...",
                parse_mode="Markdown"
            )

            try:
                file_path = generate_invoice(
                    invoice_id=invoice_counter,
                    client=user_data[user_id]["client"],
                    items=items,
                    total=total
                )
                await message.answer_document(
                    types.FSInputFile(file_path),
                    caption="✅ Your invoice is ready!"
                )
                invoice_counter += 1

            except Exception as e:
                await message.answer(f"⚠️ Error generating invoice: {str(e)}")

            user_state[user_id] = None
            user_data[user_id] = {}
            await message.answer("What would you like to do next?", reply_markup=main_menu)
            return

        user_data[user_id]["_current_item_name"] = text
        user_state[user_id] = "item_qty"
        await message.answer(f"🔢 Quantity for *{text}*:", parse_mode="Markdown")
        return

    # -----------------------------------------------
    # STEP 3 — Quantity
    # -----------------------------------------------
    if current_state == "item_qty":
        try:
            qty = int(text)
            if qty <= 0:
                raise ValueError
        except ValueError:
            await message.answer("⚠️ Please enter a valid whole number for quantity (e.g. 2):")
            return

        user_data[user_id]["_current_item_qty"] = qty
        user_state[user_id] = "item_price"
        item_name = user_data[user_id]["_current_item_name"]
        await message.answer(f"💰 Unit price for *{item_name}* (DA):", parse_mode="Markdown")
        return

    # -----------------------------------------------
    # STEP 4 — Unit price → save item
    # -----------------------------------------------
    if current_state == "item_price":
        try:
            unit_price = float(text.replace(",", "."))
            if unit_price < 0:
                raise ValueError
        except ValueError:
            await message.answer("⚠️ Please enter a valid number for the price:")
            return

        item_name = user_data[user_id].pop("_current_item_name")
        item_qty  = user_data[user_id].pop("_current_item_qty")
        subtotal  = item_qty * unit_price

        user_data[user_id]["items"].append({
            "name":       item_name,
            "qty":        item_qty,
            "unit_price": unit_price,
        })

        count = len(user_data[user_id]["items"])
        await message.answer(
            f"✅ Added: *{item_name}* x{item_qty} × {unit_price:,.0f} DA = *{subtotal:,.0f} DA*\n\n"
            f"📦 Items so far: {count}\n\n"
            f"📝 Next item name (or / to finish):",
            parse_mode="Markdown"
        )
        user_state[user_id] = "item_name"
        return


# -------------------------
# RUN BOT
# -------------------------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())