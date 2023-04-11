import sqlite3


def start_db():
    conn = sqlite3.connect( 'data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    name TEXT,
    description TEXT, 
    price INTEGER,
    pictures_id TEXT,
    active INTEGER,
    target TEXT);''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    previous_category INTEGER);''')
    c.execute('''SELECT * FROM categories;''')
    if not c.fetchall():
        create_category('Автозапчасти ⚙️', 0)
        create_category('Спецтехника 🚜️', 0)
        create_category('Аренда и найм 📆', 0)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    phone_number TEXT);''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users(
    id INTEGER PRIMARY KEY,
    banned INTEGER
    );''')
    c.execute('''CREATE TABLE IF NOT EXISTS params(
    param_name TEXT UNIQUE,
    param_value TEXT);''')
    c.execute('''SELECT * FROM params;''')
    if not c.fetchall():
        create_param('amount_pictures', '2')
    conn.commit()
    conn.close()


def create_param(param_name, param_value):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''INSERT INTO params (param_name, param_value) VALUES ('{param_name}', '{param_value}');''')
    conn.commit()


async def get_param_value(param_name):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM params WHERE param_name = '{param_name}';''')
    return c.fetchall()[0][1]


async def get_main_categories():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM categories WHERE previous_category = 0;''')
    return [{'id': i[0], 'name': i[1], 'previous_category': i[2]} for i in c.fetchall()]


async def is_subcategories(category_id : int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM categories WHERE previous_category = {category_id};''')
    if c.fetchall():
        return True


async def get_subcategories(category_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM categories WHERE previous_category = {category_id};''')
    return [{'id': i[0], 'name': i[1], 'previous_category': i[2]} for i in c.fetchall()]


def create_category(category_name: str, previous_category: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM categories WHERE name = '{category_name}';''')
    if c.fetchall():
        return False
    c.execute(f'''INSERT INTO categories(name, previous_category) VALUES ('{category_name}', {previous_category});''')
    conn.commit()
    conn.close()
    return True


async def remove_category(category_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''DELETE FROM categories WHERE id = {category_id} or previous_category = {category_id};''')
    conn.commit()
    conn.close()
    return None


async def create_item(item_data: dict):
    print(item_data)
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''INSERT INTO items(creator_id, category_id, name, description, price, pictures_id, active, target)
    VALUES ( {item_data['creator_id']}, {item_data['category_id']}, '{item_data['title']}', 
    '{item_data['description']}', {item_data['price']}, '{item_data['pictures']}', 1, '{item_data['target']}');''')
    conn.commit()
    conn.close()
    return None


async def check_user(user_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM users WHERE id ={user_id};''')
    if c.fetchall():
        return True
    return None

async def add_user(user_id: int, username: str, phone_number: str):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''INSERT INTO users VALUES ({user_id}, '{username}', '{phone_number}');''')
    conn.commit()
    conn.close()


async def get_items_by_category(category_id: int, target: str):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM items WHERE category_id = {category_id} AND active = 1 AND target = '{target}';''')
    data = c.fetchall()
    if data:
        return [{'id': i[0], 'creator_id': i[1], 'category_id': i[2], 'name': i[3], 'description': i[4], 'price': i[5],
                'pictures_id': i[6], 'active': i[7]} for i in data]
    return []


async def get_items_by_creator(creator_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM items WHERE creator_id = {creator_id} AND active = 1;''')
    data = c.fetchall()
    if data:
        return [{'id': i[0], 'creator_id': i[1], 'category_id': i[2], 'name': i[3], 'description': i[4], 'price': i[5],
                'pictures_id': i[6], 'active': i[7]} for i in data]
    return []

async def get_item_by_id(item_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM items WHERE id = {item_id} AND active = 1;''')
    data = c.fetchall()[0]
    if data:
        return {'id': data[0], 'creator_id': data[1], 'category_id': data[2], 'name': data[3], 'description': data[4], 'price': data[5],
                'pictures_id': data[6], 'active': data[7], 'target': data[8]}
    return None


async def get_phone_number(user_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT phone_number FROM users WHERE id = {user_id};''')
    return c.fetchall()[0][0]


async def get_category_by_id(category_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM categories WHERE id = {category_id};''')
    data = c.fetchall()[0]
    response = {
        'id': data[0],
        'name': data[1],
        'previous_category': data[2]
    }
    return response


async def remove_item_by_id(item_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE items SET active = 0 WHERE id = {item_id};''')
    conn.commit()
    conn.close()
    return None


async def get_category_name(category_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT name FROM categories WHERE id = {category_id};''')
    return c.fetchall()[0][0]


async def get_amount_items_per_user(user_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM items WHERE creator_id = {user_id} AND active = 1;''')
    return len(c.fetchall())


async def get_users():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM users;''')
    data = list()
    for i in c.fetchall():
        user_id = i[0]
        username = i[1]
        phone_number = i[2]
        items_amount = await get_amount_items_per_user(user_id)
        data.append([username, user_id, phone_number, items_amount])
    return data





async def change_phone_number(user_id, phone_number):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE users SET phone_number = '{phone_number}' WHERE id ={user_id};''')
    conn.commit()


async def change_price(item_id, price):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE items SET price = {price} WHERE id = {item_id};''')
    conn.commit()


async def change_param(param_name, param_value):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE params SET param_value = '{param_value}' WHERE param_name = '{param_name}';''')


async def change_title(item_id, title):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE items SET name = '{title}' WHERE id = {item_id};''')
    conn.commit()


async def change_description(item_id, description):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE items SET description = '{description}' WHERE id = {item_id};''')
    conn.commit()


async def change_pictures(item_id, pictures):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE items SET pictures_id = '{pictures}' WHERE id = {item_id};''')
    conn.commit()


async def get_items_by_keyword(keyword):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM items WHERE active = 1;''')
    data = c.fetchall()
    items = list()
    descriptions = [[i[0], i[3] + ' ' + i[4]] for i in data]
    for i in descriptions:
        item_id = i[0]
        description = i[1]
        if keyword.lower() in description.lower():
            items.append(item_id)
    for i in range(len(items)):
        item = await get_item_by_id(items[i])
        items[i] = item
    return items


async def check_banned(user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM banned_users WHERE id = {user_id};''')
    data = c.fetchall()
    if data and data[0][1] == 1:
        return True
    else:
        return False


async def ban_user(user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    if await check_banned(user_id):
        return
    c.execute(f'''SELECT * FROM banned_users WHERE id = {user_id};''')
    if c.fetchall():
        c.execute(f'''UPDATE banned_users SET banned = 1 WHERE id = {user_id};''')
    else:
        c.execute(f'''INSERT INTO banned_users(id, banned) VALUES ({user_id}, 1);''')
    c.execute(f'''UPDATE items SET active = 0 WHERE creator_id = {user_id};''')
    conn.commit()


async def get_user_by_id(user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM users WHERE id = {user_id};''')
    return c.fetchall()[0]


async def unban_user(user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE banned_users SET banned = 0 WHERE id = {user_id};''')
    conn.commit()
