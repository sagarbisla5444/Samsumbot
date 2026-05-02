from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
import re
import os

# =========================
# CONFIG
# =========================
ROWS = ["fd", "gd", "gli", "ds"]
COLS = ["neeraj","gulab","tangar","ak","kath","bkp","mohit","ludo","shis","lalit","bkaam","bunty","foldar","poli"]

# =========================
# STORAGE (ROW → COLUMN)
# =========================
data = {row: {col: [] for col in COLS} for row in ROWS}
user_context = {}
user_state = {}

# =========================
# HELP
# =========================
def command_help():
    return (
        "\n\n📌 Commands:\n"
        "\n"
        "/new → select row (lock)\n"
        "\n"
        "/start → select column\n"
        "\n"
        "/sum tangar fd → sum of one cell\n"
        "/sum tangar → sum of column\n"
        "/sumall fd → sum of row\n"
        "/view tangar fd → view entries\n"
        "/remove 12 10 → remove one entry\n"
        "/removeall 12 10 → remove all entries\n"
        "/reset → clear all data\n"
    )

# =========================
# PARSER
# =========================
def parse_input(text):
    pairs = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        val_match = re.search(r"(?:=|\(|/)(\d+)\)?", line)
        if not val_match:
            continue

        val = int(val_match.group(1))
        left = line.split(val_match.group(0))[0]

        nums = re.findall(r"\d{1,2}", left)

        for n in nums:
            pairs.append((n.zfill(2), val))

    return pairs

# =========================
# BUTTONS
# =========================
def column_buttons():
    keyboard = []
    row = []
    for i, col in enumerate(COLS, 1):
        row.append(InlineKeyboardButton(col, callback_data=f"col|{col}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def row_buttons():
    keyboard = [[InlineKeyboardButton(r, callback_data=f"row|{r}") for r in ROWS]]
    return InlineKeyboardMarkup(keyboard)

# =========================
# /NEW → SELECT ROW
# =========================
async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = "select_row"

    await update.message.reply_text(
        "📊 Select Row 👇",
        reply_markup=row_buttons()
    )

# =========================
# /START → SELECT COLUMN
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_context or "row" not in user_context[user_id]:
        await update.message.reply_text("❌ First select row using /new")
        return

    user_state[user_id] = "select_col"

    await update.message.reply_text(
        f"📊 Row: {user_context[user_id]['row']}\n\nSelect Column 👇",
        reply_markup=column_buttons()
    )

# =========================
# BUTTON HANDLER
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()
    data_btn = query.data.split("|")

    # ROW SELECT
    if data_btn[0] == "row":
        row = data_btn[1]

        if user_id not in user_context:
            user_context[user_id] = {}

        user_context[user_id]["row"] = row
        user_state[user_id] = "row_selected"

        await query.edit_message_text(
            f"✅ Row locked: {row}\n\nNow use /start to select column"
        )

    # COLUMN SELECT
    elif data_btn[0] == "col":
        if user_id not in user_context or "row" not in user_context[user_id]:
            await query.answer("Use /new first ❗", show_alert=True)
            return

        col = data_btn[1]
        user_context[user_id]["col"] = col
        user_state[user_id] = "input"

        row = user_context[user_id]["row"]

        await query.edit_message_text(
            f"✅ Selected: {row} → {col}\n\nNow send numbers + value"
        )

# =========================
# HANDLE INPUT
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_state.get(user_id) != "input":
        await update.message.reply_text("❌ Use /start to select column first")
        return

    ctx = user_context[user_id]
    row = ctx["row"]
    col = ctx["col"]

    pairs = parse_input(text)

    if not pairs:
        await update.message.reply_text("❌ Invalid format" + command_help())
        return

    data[row][col].extend(pairs)

    total = sum(v for _, v in pairs)
    msg = "\n".join([f"{n} → {v}" for n, v in pairs])

    await update.message.reply_text(
        msg + f"\n\n💰 INPUT TOTAL: {total}" + command_help()
    )

# =========================
# SUM
# =========================
async def sum_cell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) not in [1, 2]:
        await update.message.reply_text("Usage:\n/sum tangar fd\n/sum tangar")
        return

    col = context.args[0]

    if col not in COLS:
        await update.message.reply_text("Invalid column")
        return

    totals = {}
    grand_total = 0

    if len(context.args) == 2:
        row = context.args[1]

        if row not in ROWS:
            await update.message.reply_text("Invalid row")
            return

        for n, v in data[row][col]:
            totals[n] = totals.get(n, 0) + v
            grand_total += v

    else:
        for row in ROWS:
            for n, v in data[row][col]:
                totals[n] = totals.get(n, 0) + v
                grand_total += v

    sorted_data = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    msg = "\n".join([f"{n} → {v}" for n, v in sorted_data])

    await update.message.reply_text(
        (msg or "No data") + f"\n\n💰 TOTAL: {grand_total}" + command_help()
    )

# =========================
# SUM ALL ROW
# =========================
async def sum_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /sumall fd")
        return

    row = context.args[0]

    if row not in ROWS:
        await update.message.reply_text("Invalid row")
        return

    totals = {}
    grand_total = 0

    ak_totals = {}
    ak_total = 0

    for col in COLS:
        for n, v in data[row][col]:
            # MAIN TOTAL
            totals[n] = totals.get(n, 0) + v
            grand_total += v

            # AK SEPARATE
            if col == "ak":
                ak_totals[n] = ak_totals.get(n, 0) + v
                ak_total += v

    # SORT
    sorted_data = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    sorted_ak = sorted(ak_totals.items(), key=lambda x: x[1], reverse=True)

    # FORMAT
    main_msg = "\n".join([f"{n} → {v}" for n, v in sorted_data])
    ak_msg = "\n".join([f"{n} → {v}" for n, v in sorted_ak])

    final_msg = (
        (main_msg or "No data") +
        f"\n\n💰 TOTAL ({row}): {grand_total}\n\n"
        "───── ****AK ONLY**** ─────\n" +
        (ak_msg or "No AK data") +
        f"\n\n💰 AK TOTAL: {ak_total}" +
        command_help()
    )

    await update.message.reply_text(final_msg)

# =========================
# VIEW
# =========================
async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /view tangar fd")
        return

    col, row = context.args

    if col not in COLS or row not in ROWS:
        await update.message.reply_text("Invalid input")
        return

    pairs = data[row][col]
    msg = "\n".join([f"{n} → {v}" for n, v in pairs])

    await update.message.reply_text((msg or "No data") + command_help())

# =========================
# REMOVE
# =========================
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_context:
        await update.message.reply_text("❌ Set row & column first")
        return

    ctx = user_context[user_id]

    if "row" not in ctx or "col" not in ctx:
        await update.message.reply_text("❌ Use /new and /start first")
        return

    row = ctx["row"]
    col = ctx["col"]

    # Get full message text after /remove
    text = update.message.text.replace("/remove", "").strip()

    if not text:
        await update.message.reply_text(
            "Usage:\n/remove\n12.13.14=100\n45.46=50"
        )
        return

    # 🔥 Use SAME parser as input
    pairs_to_remove = parse_input(text)

    if not pairs_to_remove:
        await update.message.reply_text("❌ Invalid format")
        return

    removed_count = 0
    new_data = data[row][col].copy()

    for num, val in pairs_to_remove:
        for i, (n, v) in enumerate(new_data):
            if n == num and v == val:
                new_data.pop(i)
                removed_count += 1
                break  # remove only one match

    data[row][col] = new_data

    await update.message.reply_text(
        f"✅ Removed {removed_count} entries from {row} → {col}"
    )

# =========================
# REMOVE ALL
# =========================
async def remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_context:
        await update.message.reply_text("Set context first")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /removeall 12 10")
        return

    num = context.args[0].zfill(2)
    val = int(context.args[1])

    ctx = user_context[user_id]
    row = ctx["row"]
    col = ctx["col"]

    data[row][col] = [
        (n, v) for n, v in data[row][col] if not (n == num and v == val)
    ]

    await update.message.reply_text("Removed all ✅")

# =========================
# RESET
# =========================
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data
    data = {row: {col: [] for col in COLS} for row in ROWS}
    await update.message.reply_text("Reset done ✅")

# =========================
# RUN
# =========================
TOKEN = os.getenv("TOKEN")   

if not TOKEN:
    raise ValueError("❌ TOKEN not found")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("new", new))
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CommandHandler("sum", sum_cell))
app.add_handler(CommandHandler("sumall", sum_all))
app.add_handler(CommandHandler("view", view))
app.add_handler(CommandHandler("remove", remove))
app.add_handler(CommandHandler("removeall", remove_all))
app.add_handler(CommandHandler("reset", reset))


if __name__ == "__main__":
    print("🚀 Bot Running...")
    app.run_polling()
