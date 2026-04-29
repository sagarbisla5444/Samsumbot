from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
import re

# =========================
# CONFIG
# =========================
ROWS = ["fd", "gd", "gli", "ds"]
COLS = ["neeraj","gulab","tangar","ak","kath","bkp","mohit","ludo","shis","lalit","bkaam","bunty","foldar","poli"]

# =========================
# STORAGE
# =========================
data = {col: {row: [] for row in ROWS} for col in COLS}
user_context = {}
user_state = {}

# =========================
# HELP
# =========================
def command_help():
    return (
        "\n\n📌 Commands:\n"
        "/start → select row and column\n"
        "/sum tangar fd → sum of one cell\n"
        "/sum tangar → sum of column (all rows)\n"
        "/sumall fd → sum of entire row\n"
        "/view tangar fd → view raw entries\n"
        "/remove 12 10 → remove one entry\n"
        "/removeall 12 10 → remove all same entries\n"
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
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = "select_col"

    await update.message.reply_text(
        "📊 Select Column 👇",
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

    if data_btn[0] == "col":
        col = data_btn[1]
        user_context[user_id] = {"col": col}
        user_state[user_id] = "select_row"

        await query.edit_message_text(
            f"✅ Column: {col}\n\nNow select row 👇",
            reply_markup=row_buttons()
        )

    elif data_btn[0] == "row":
        row = data_btn[1]
        col = user_context[user_id]["col"]

        user_context[user_id] = (col, row)
        user_state[user_id] = "input"

        await query.edit_message_text(
            f"✅ Selected: {col} → {row}\n\nNow send numbers + value"
        )

# =========================
# HANDLE INPUT
# =========================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_state.get(user_id) != "input":
        await update.message.reply_text(
            "❌ Wrong input\n\nUse buttons 👇",
            reply_markup=column_buttons()
        )
        return

    col, row = user_context[user_id]
    pairs = parse_input(text)

    if not pairs:
        await update.message.reply_text("❌ Invalid format" + command_help())
        return

    data[col][row].extend(pairs)

    input_total = sum(v for _, v in pairs)
    output = "\n".join([f"{n} → {v}" for n, v in pairs])

    await update.message.reply_text(
        output + f"\n\n💰 INPUT TOTAL: {input_total}" + command_help()
    )

# =========================
# SUM (CELL + COLUMN)
# =========================
async def sum_cell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) not in [1, 2]:
        await update.message.reply_text("Usage:\n/sum tangar fd\n/sum tangar")
        return

    col = context.args[0]

    if col not in COLS:
        await update.message.reply_text("❌ Invalid column" + command_help())
        return

    totals = {}
    grand_total = 0

    if len(context.args) == 2:
        row = context.args[1]

        if row not in ROWS:
            await update.message.reply_text("❌ Invalid row" + command_help())
            return

        for n, v in data[col][row]:
            totals[n] = totals.get(n, 0) + v
            grand_total += v

        title = f"{col.upper()} {row.upper()}"

    else:
        for row in ROWS:
            for n, v in data[col][row]:
                totals[n] = totals.get(n, 0) + v
                grand_total += v

        title = f"{col.upper()} ALL"

    sorted_data = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    msg = "\n".join([f"{n} → {v}" for n, v in sorted_data])

    await update.message.reply_text(
        (msg if msg else "No data") +
        f"\n\n💰 TOTAL ({title}): {grand_total}" +
        command_help()
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
        await update.message.reply_text("❌ Invalid row" + command_help())
        return

    totals = {}
    grand_total = 0

    for col in COLS:
        for n, v in data[col][row]:
            totals[n] = totals.get(n, 0) + v
            grand_total += v

    sorted_data = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    msg = "\n".join([f"{n} → {v}" for n, v in sorted_data])

    await update.message.reply_text(
        (msg if msg else "No data") +
        f"\n\n💰 GRAND TOTAL ({row.upper()}): {grand_total}" +
        command_help()
    )

# =========================
# VIEW
# =========================
async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /view neeraj fd")
        return

    col, row = context.args

    if col not in COLS or row not in ROWS:
        await update.message.reply_text("Invalid input" + command_help())
        return

    pairs = data[col][row]
    msg = "\n".join([f"{n} → {v}" for n, v in pairs])

    await update.message.reply_text((msg or "No data") + command_help())

# =========================
# REMOVE
# =========================
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_context:
        await update.message.reply_text("Set context first")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /remove 12 10")
        return

    num = context.args[0].zfill(2)
    val = int(context.args[1])

    col, row = user_context[user_id]

    new = []
    removed = False

    for n, v in data[col][row]:
        if n == num and v == val and not removed:
            removed = True
            continue
        new.append((n, v))

    data[col][row] = new
    await update.message.reply_text("Removed one ✅" + command_help())

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

    col, row = user_context[user_id]

    data[col][row] = [(n, v) for n, v in data[col][row] if not (n == num and v == val)]

    await update.message.reply_text("Removed all ✅" + command_help())

# =========================
# RESET
# =========================
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data
    data = {col: {row: [] for row in ROWS} for col in COLS}
    await update.message.reply_text("Reset done ✅" + command_help())

# =========================
# RUN
# =========================
TOKEN = "token"

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CommandHandler("sum", sum_cell))
app.add_handler(CommandHandler("sumall", sum_all))
app.add_handler(CommandHandler("view", view))
app.add_handler(CommandHandler("remove", remove))
app.add_handler(CommandHandler("removeall", remove_all))
app.add_handler(CommandHandler("reset", reset))

print("🚀 Final Smart Bot Running...")
app.run_polling()
