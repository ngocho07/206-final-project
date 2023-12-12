import requests
import os
import sqlite3

# Get data from Harvard Art Museums API
def get_harvard_info(api_key, endpoint, params=None):
    base_url = 'https://api.harvardartmuseums.org'

    url = f'{base_url}{endpoint}&apikey={api_key}'

    try:        
        response = requests.get(url, params=params)
            
        if response.status_code == 200:
            harvard_data = response.json()
            return harvard_data
        else:
            print(f'Error: {response.status_code} - {response.text}')
    
    except requests.RequestException as e:
        print(f'Request error: {e}')

# Create database
def set_up_database(db):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db + ".db")
    cur = conn.cursor()
    return cur, conn

# Creates period table in database
def set_up_period_table(api_key, cur, conn, max_items=25):
    endpoint = '/period?size=200'
    page = 1

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='period'")
    table_exists = cur.fetchone()

    if not table_exists:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS period (
                period_id INTEGER PRIMARY KEY,
                object_count INTEGER,
                name TEXT            
            )
        ''')

    while True:

        params = {'size': max_items, 'page': page, 'sort': 'periodid'}
        harvard_data = get_harvard_info(api_key, endpoint, params)


        if not harvard_data.get('records'):
            break

        for record in harvard_data.get('records', []):
            period_id = record.get('periodid')
            objectcount = record.get('objectcount')
            name = record.get('name')
            #print(f"Inserting into period: {period_id}, name: {name.encode('utf-8')} objectcount: {objectcount}")
            cur.execute('''
                INSERT OR IGNORE INTO period (period_id, object_count, name)
                VALUES (?, ?, ?)
            ''', (period_id, objectcount, name))

        page += 1
            
    conn.commit()

# Creates period table in database
def set_up_classification_table(api_key, cur, conn, max_items=25):
    endpoint = '/classification?size=200'
    page = 1

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='classification'")
    table_exists = cur.fetchone()

    if not table_exists:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS classification (
                classification_id INTEGER PRIMARY KEY,
                object_count INTEGER,
                name TEXT            
            )
        ''')

    while True:

        params = {'size': max_items, 'page': page, 'sort': 'classificationid'}
        harvard_data = get_harvard_info(api_key, endpoint, params)


        if not harvard_data.get('records'):
            break

        for record in harvard_data.get('records', []):
            classification_id = record.get('classificationid')
            objectcount = record.get('objectcount')
            name = record.get('name')

            cur.execute('''
                INSERT OR IGNORE INTO classification (classification_id, object_count, name)
                VALUES (?, ?, ?)
            ''', (classification_id, objectcount, name))

        page += 1
            
    conn.commit()

def gather_data(api_key):
    cur, conn = set_up_database("testdb")

    set_up_period_table(api_key, cur, conn, max_items=25)

    set_up_classification_table(api_key, cur, conn, max_items=25)

    conn.close()

if __name__ == '__main__':
    api_key = '39ce36a2-869c-4bc0-b20b-d1bf6a65f855'
    gather_data(api_key)