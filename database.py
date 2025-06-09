import sqlite3

def init_db():
    conn = sqlite3.connect("premiums.db")
    cursor = conn.cursor()
    
    # Создаем таблицу, если она еще не существует
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS premiums (
            tab_number INTEGER PRIMARY KEY,
            premium INTEGER NOT NULL
        )
    """)
    
    # Данные о премиях
    premium_data = [
        (77815, 5011),
        (77816, 6846),
        (77817, 6557),
        (77819, 5897),
        (77818, 4487),
        (77814, 3613),
        (77820, 759)
    ]
    
    # Вставляем данные, если таблица пуста
    cursor.execute("SELECT COUNT(*) FROM premiums")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO premiums (tab_number, premium) VALUES (?, ?)", premium_data)
    
    conn.commit()
    conn.close()

def get_premium(tab_number):
    conn = sqlite3.connect("premiums.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT premium FROM premiums WHERE tab_number = ?", (tab_number,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else None