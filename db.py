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
    picture1_id TEXT,
    picture2_id TEXT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    phone_number TEXT);''')
    conn.commit()
    conn.close()

def get_main_categories():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM categories WHERE previous_category = 0;''')
    return [{'id': i[0], 'name': i[1], 'previous_category': i[2]} for i in c.fetchall()]


def is_subcategories(category_id : int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM categories WHERE previous_category = {category_id};''')
    if c.fetchall():
        return True

def get_subcategories(category_id: int):
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


def remove_category(category_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''DELETE FROM categories WHERE id = {category_id} or previous_category = {category_id};''')
    conn.commit()
    conn.close()
    return None


def create_item(item_data: dict):
    print(item_data)
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''INSERT INTO items(creator_id, category_id, name, description, price, picture1_id, picture2_id, active, target)
    VALUES ( {item_data['creator_id']}, {item_data['category_id']}, '{item_data['title']}', 
    '{item_data['description']}', {item_data['price']}, '{item_data['picture1']}', '{item_data['picture2']}', 1, '{item_data['target']}');''')
    conn.commit()
    conn.close()
    return None


def check_user(user_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM users WHERE id ={user_id};''')
    if c.fetchall():
        return True
    return None

def add_user(user_id: int, username: str, phone_number: str):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''INSERT INTO users VALUES ({user_id}, '{username}', '{phone_number}');''')
    conn.commit()
    conn.close()


def get_items_by_category(category_id: int, target: str):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM items WHERE category_id = {category_id} AND active = 1 AND target = '{target}';''')
    data = c.fetchall()
    if data:
        return [{'id': i[0], 'creator_id': i[1], 'category_id': i[2], 'name': i[3], 'description': i[4], 'price': i[5],
                'picture1_id': i[6], 'picture2_id': i[7], 'active': i[8]} for i in data]
    return []


def get_items_by_creator(creator_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM items WHERE creator_id = {creator_id} AND active = 1;''')
    data = c.fetchall()
    if data:
        return [{'id': i[0], 'creator_id': i[1], 'category_id': i[2], 'name': i[3], 'description': i[4], 'price': i[5],
                'picture1_id': i[6], 'picture2_id': i[7], 'active': i[8]} for i in data]
    return []

def get_item_by_id(item_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM items WHERE id = {item_id} AND active = 1;''')
    data = c.fetchall()
    if data:
        return [{'id': i[0], 'creator_id': i[1], 'category_id': i[2], 'name': i[3], 'description': i[4], 'price': i[5],
                'picture1_id': i[6], 'picture2_id': i[7], 'active': i[8], 'target': i[9]} for i in data][0]
    return None


def get_phone_number(user_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT phone_number FROM users WHERE id = {user_id};''')
    return c.fetchall()[0][0]


def get_category_by_id(category_id: int):
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


def remove_item_by_id(item_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''UPDATE items SET active = 0 WHERE id = {item_id};''')
    conn.commit()
    conn.close()
    return None


def get_category_name(category_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT name FROM categories WHERE id = {category_id};''')
    return c.fetchall()[0][0]


def get_amount_items_per_user(user_id: int):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM items WHERE creator_id = {user_id};''')
    return len(c.fetchall())


def get_users():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute(f'''SELECT * FROM users;''')
    data = list()
    for i in c.fetchall():
        user_id = i[0]
        username = i[1]
        phone_number = i[2]
        items_amount = get_amount_items_per_user(user_id)
        data.append([username, user_id, phone_number, items_amount])
    return data
