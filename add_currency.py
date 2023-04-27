import sqlite3
conn = sqlite3.connect('data.db')
c = conn.cursor()


for i in range(6,76):
    item_id = i
    c.execute(f'''SELECT * FROM items WHERE id ={item_id};''')
    item = c.fetchall()[0]
    price = item[5]
    if price.strip()[-1] != '$':
        price += ' ₽'
    c.execute(f'''UPDATE items SET price = '{price}' WHERE id = {item_id};''')
    conn.commit()