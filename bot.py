import telebot
from telebot import types
import threading, random
from datetime import datetime

TOKEN = "8564150511:AAG61lLvtIkgsDbISMIR9p3uSz4HxBKKyFE"  # Replace with your bot token
ADMIN_ID = 7798127593       # Replace with your admin Telegram ID
ADMIN_USERNAME = "Leon_ts_T"
JOIN_CHANNEL = "https://t.me/Toe_tris_Bot_T"

bot = telebot.TeleBot(TOKEN)

# ===== DATA =====
users = {}                     # {user_id: {"balance":0,"orders":[]}}
approved_users = []            # user IDs approved for bot
approved_groups = {}           # {user_id:[group_id1, group_id2,...]}
services = {"TikTok":[],"Telegram":[],"Facebook":[]}
pending_orders = []
total_income = 0

# ===== HELPERS =====
def is_admin(uid):
    return uid == ADMIN_ID

def init_user(uid):
    if uid not in users:
        users[uid] = {"balance":0,"orders":[]}

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    init_user(uid)
    if is_admin(uid):
        show_admin_menu(message)
        return
    if uid not in approved_users:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=JOIN_CHANNEL))
        markup.add(types.InlineKeyboardButton("✅ Request Approval", callback_data=f"req_{uid}"))
        bot.send_message(uid,f"❌ Not approved. Contact @{ADMIN_USERNAME}",reply_markup=markup)
        return
    show_user_menu(message)

# ===== MENUS =====
def show_user_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Balance","📦 Services")
    markup.add("📄 My Orders","➕ Add Balance")
    bot.send_message(message.chat.id,"🔹 User Menu",reply_markup=markup)

def show_admin_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Add Service","🗑 Delete Service","💰 Add Balance")
    markup.add("✅ Approve Users","✅ Approve Orders")
    markup.add("📊 Total Income")
    bot.send_message(message.chat.id,"🔹 Admin Panel",reply_markup=markup)

# ===== CALLBACK HANDLER =====
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    uid = call.from_user.id
    data = call.data
    global total_income

    if data.startswith("req_") and not is_admin(uid):
        req_id = int(data.split("_")[1])
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"appr_{req_id}"))
        bot.send_message(ADMIN_ID,f"User {req_id} requested approval",reply_markup=markup)
        bot.answer_callback_query(call.id,"Request sent to admin")

    if data.startswith("appr_") and is_admin(uid):
        req_id = int(data.split("_")[1])
        approved_users.append(req_id)
        init_user(req_id)
        bot.send_message(req_id,"✅ You are now approved! Use /start")
        bot.edit_message_reply_markup(ADMIN_ID,call.message.message_id,reply_markup=None)
        bot.answer_callback_query(call.id,"User approved ✅")

    if data.startswith(("ok_","no_")) and is_admin(uid):
        idx = int(data.split("_")[1])
        if idx >= len(pending_orders): return
        order = pending_orders.pop(idx)
        user_id = order["user_id"]
        if data.startswith("ok_"):
            total_income += order["price"]
            balance = users[user_id]["balance"]
            notify_text = f"""
✅ Order Approved!
👤 User ID: {user_id}
📂 Service Category: {order['category']}
💻 Service Type: {order['service']}
🆔 Link: {order['link']}
🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔢 Quantity: {order['quantity']}
💰 Price Paid: {order['price']} coins
💳 Current Balance: {balance} coins
"""
            bot.send_message(user_id, notify_text)
            # Optional delayed post
            delay_sec = random.randint(1800, 54000)  # 30min ~ 15h
            def delayed_post():
                text = f"✅ Order Completed!\nUser: {user_id}\nService: {order['service']}\nCategory: {order['category']}\nQty: {order['quantity']}\nPrice: {order['price']} coins\nLink: {order['link']}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                bot.send_message(order["chat_id"], text)
            threading.Timer(delay_sec, delayed_post).start()
            bot.answer_callback_query(call.id,"Order approved and user notified ✅")
        else:
            users[user_id]["balance"] += order["price"]
            bot.send_message(user_id,f"❌ Your order {order['service']} rejected. Balance refunded.")
            bot.answer_callback_query(call.id,"Order rejected and balance refunded ✅")

# ===== USER BUTTONS =====
@bot.message_handler(func=lambda m: m.text=="💰 Balance")
def show_balance(message):
    uid = message.from_user.id
    init_user(uid)
    bot.send_message(uid,f"💰 Your balance: {users[uid]['balance']} coins")

@bot.message_handler(func=lambda m: m.text=="📄 My Orders")
def show_orders(message):
    uid = message.from_user.id
    init_user(uid)
    orders=users[uid]["orders"]
    if not orders:
        bot.send_message(uid,"You have no orders yet")
        return
    text="📝 Your Orders:\n"
    for o in orders:
        text+=f"{o['service']} | Qty: {o['quantity']} | Price: {o['price']} | Link: {o['link']}\n"
    bot.send_message(uid,text)

@bot.message_handler(func=lambda m: m.text=="➕ Add Balance")
def user_add_balance(message):
    bot.send_message(message.from_user.id,f"💰 Contact admin @{ADMIN_USERNAME} to add balance")

@bot.message_handler(func=lambda m: m.text=="📦 Services")
def user_services_direct(message):
    uid = message.from_user.id
    init_user(uid)
    all_services_exist = any(services.values())
    if not all_services_exist:
        bot.send_message(uid, "❌ No services available right now")
        return
    text = "👾 Available Services:👾\n\n"
    for category, svc_list in services.items():
        for svc in svc_list:
            text += f"🤖 {category} | 🌳 {svc['name']} | Qty: {svc['quantity']} | Price: {svc['price']} coins\n\n"
    bot.send_message(uid, text)

# ===== ADMIN BUTTONS =====
@bot.message_handler(func=lambda m: m.text=="➕ Add Service")
def admin_add_service(message):
    if not is_admin(message.from_user.id): return
    bot.send_message(message.chat.id,"Send: Category Name Quantity Price\nEx: TikTok Like 1000 300")
    bot.register_next_step_handler(message,save_service_admin)

def save_service_admin(message):
    try:
        cat,name,qty,price=message.text.split()
        qty=int(qty); price=int(price)
        if cat not in services: services[cat]=[]
        services[cat].append({"name":name,"quantity":qty,"price":price})
        bot.send_message(message.chat.id,"✅ Service added")
    except:
        bot.send_message(message.chat.id,"❌ Format error")

@bot.message_handler(func=lambda m: m.text=="🗑 Delete Service")
def admin_delete_service_linear(message):
    if not is_admin(message.from_user.id): return
    uid = message.from_user.id
    all_services = []
    count = 1
    text = "🗑 Delete Services:\n\n"
    for cat, svc_list in services.items():
        for svc in svc_list:
            text += f"{count}. {cat} | {svc['name']} | Qty: {svc['quantity']} | Price: {svc['price']}\n"
            all_services.append((cat, svc['name']))
            count += 1
    if not all_services:
        bot.send_message(uid,"❌ No services available to delete")
        return
    bot.send_message(uid,text)
    bot.send_message(uid,"Send the number of the service to delete:")
    bot.register_next_step_handler(message, lambda m: process_delete_service_linear(m, all_services))

def process_delete_service_linear(message, all_services):
    uid = message.from_user.id
    if not is_admin(uid): return
    try:
        idx = int(message.text.strip()) - 1
        if idx < 0 or idx >= len(all_services):
            bot.send_message(uid,"❌ Invalid number")
            return
        cat, name = all_services[idx]
        services[cat] = [s for s in services[cat] if s['name'] != name]
        bot.send_message(uid,f"✅ Deleted {name} from {cat}")
    except:
        bot.send_message(uid,"❌ Invalid input. Send a number corresponding to the service")

@bot.message_handler(func=lambda m: m.text=="💰 Add Balance")
def admin_add_balance(message):
    if not is_admin(message.from_user.id): return
    bot.send_message(message.chat.id,"Send: UserID Amount\nEx: 1135380346 500")
    bot.register_next_step_handler(message,process_add_balance)

def process_add_balance(message):
    try:
        uid,amount=map(int,message.text.split())
        if uid not in users: users[uid]={"balance":0,"orders":[]}
        users[uid]["balance"]+=amount
        bot.send_message(message.chat.id,f"✅ Added {amount} coins to {uid}")
        bot.send_message(uid,f"💰 Your balance increased by {amount} coins")
    except:
        bot.send_message(message.chat.id,"❌ Format error")

@bot.message_handler(func=lambda m: m.text=="📊 Total Income")
def admin_total_income(message):
    if not is_admin(message.from_user.id): return
    text = f"💰 Total Income: {total_income} coins\n\n"
    text += "👤 Users State:\n"
    for uid, data in users.items():
        orders_count = len(data["orders"])
        balance = data["balance"]
        text += f"User: {uid} | Orders: {orders_count} | Balance: {balance}\n"
    bot.send_message(message.chat.id, text)

# ===== ADMIN GROUP APPROVAL =====
@bot.message_handler(commands=['group'])
def admin_group_approval(message):
    uid = message.from_user.id
    if not is_admin(uid): return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(uid,"❌ Usage: /group <user_id> <group_id>")
            return
        user_id = int(parts[1])
        group_id = int(parts[2])
        if user_id not in approved_groups:
            approved_groups[user_id] = []
        if group_id not in approved_groups[user_id]:
            approved_groups[user_id].append(group_id)
        bot.send_message(uid,f"✅ User {user_id} is allowed to post in group {group_id}")
        bot.send_message(user_id,f"✅ You are now allowed to use bot in group {group_id}")
    except:
        bot.send_message(uid,"❌ Invalid format")

# ===== GROUP ORDER HANDLER – IMMEDIATE NOTIFY + UI =====
@bot.message_handler(func=lambda m: m.text.startswith("/order"))
def handle_group_order(message):
    uid = message.from_user.id
    init_user(uid)

    # Check group permission
    chat_id = message.chat.id
    allowed_groups = approved_groups.get(uid, [])
    if chat_id not in allowed_groups:
        bot.send_message(uid,"❌ You don’t have permission to post in this group. Contact admin")
        return

    try:
        parts = message.text.split()
        if len(parts) < 5:
            bot.send_message(uid,"❌ Invalid format. Use: /order <Category> <Service> <Quantity> <Link>")
            return
        _, category, service, quantity, link = parts[0], parts[1], parts[2], int(parts[3]), parts[4]
        if quantity < 100:
            bot.send_message(uid,"❌ Minimum order quantity is 100")
            return
        svc_list = services.get(category, [])
        svc = next((s for s in svc_list if s["name"]==service), None)
        if not svc:
            bot.send_message(uid,"❌ Service not found")
            return
        price = svc["price"] * quantity // svc["quantity"]
        if users[uid]["balance"] < price:
            bot.send_message(uid,f"❌ Insufficient balance. Needed: {price} coins, Your balance: {users[uid]['balance']} coins")
            return

        # Deduct balance and save order
        users[uid]["balance"] -= price
        order = {"user_id":uid, "category":category, "service":service,
                 "quantity":quantity, "link":link, "price":price, "chat_id":chat_id}
        pending_orders.append(order)
        users[uid]["orders"].append(order)
        idx = len(pending_orders)-1

        # Inline buttons for admin approval
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"ok_{idx}"))
        markup.add(types.InlineKeyboardButton("❌ Reject", callback_data=f"no_{idx}"))

        # Immediate notify user + group with styled UI
        bot.send_message(uid, f"✅ Order success! Pending admin approval.\n💳 Current Balance: {users[uid]['balance']} coins")
        group_text = f"""
🛒 *New Order!*

👤 *User ID:* `{uid}`
📂 *Category:* {category}
💻 *Service:* {service}
🔢 *Quantity:* {quantity}
💰 *Price:* {price} coins
🆔 *Link:* [Click Here]({link})
💳 *Remaining Balance:* {users[uid]['balance']} coins
🕒 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        bot.send_message(chat_id, group_text, parse_mode="Markdown")

        # Notify admin
        bot.send_message(ADMIN_ID,f"New order from {uid}:\n{category} | {service} | Qty:{quantity} | Price: {price} coins\nLink: {link}", reply_markup=markup)

    except:
        bot.send_message(uid,"❌ Error parsing order. Use: /order <Category> <Service> <Quantity> <Link>")

# ===== RUN BOT =====
bot.infinity_polling()
