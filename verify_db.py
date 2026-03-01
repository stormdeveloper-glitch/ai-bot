import sqlite3
conn = sqlite3.connect('database/bot.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='card_images';")
print(cursor.fetchone())
conn.close()
