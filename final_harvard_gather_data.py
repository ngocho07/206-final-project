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

# Function to insert data into the database
def insert_data(cur, table, data, page):
    for record in data:
        record_id = record.get(f'{table}id')
        objectcount = record.get('objectcount')
        name = record.get('name')

        cur.execute(f'''
            INSERT OR IGNORE INTO {table} ({table}_id, object_count, name, page)
            VALUES (?, ?, ?, ?)
        ''', (record_id, objectcount, name, page))

# Function to set up a table in the database
def set_up_table(api_key, cur, conn, table, max_items=25, additional_rows=25):
    endpoint = f'/{table}?size=200'
    
    # Add the 'page' column if it doesn't exist
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS {table} (
            {table}_id INTEGER PRIMARY KEY,
            object_count INTEGER,
            name TEXT,
            page INTEGER
        )
    ''')

    # Get the last page number from the database
    cur.execute(f'SELECT MAX(page) FROM {table}')
    last_page = cur.fetchone()[0] or 1  # Default to 1 if no data in the database yet

    page = last_page + 1  # Increment the page to start fetching new data

    rows_added = 0
    while True:
        
        params = {'size': max_items, 'page': page, 'sort': f'{table}id'}
        harvard_data = get_harvard_info(api_key, endpoint, params)

        if not harvard_data.get('records'):
            break

        insert_data(cur, table, harvard_data.get('records', []), page)

        rows_added += max_items

        page += 1
        if page > last_page + additional_rows / max_items:
            break  # Stop after fetching the specified additional rows
            
    conn.commit()

# Function to gather data for both tables
def gather_data(api_key, additional_rows=25):
    cur, conn = set_up_database("museums")

    set_up_table(api_key, cur, conn, 'period', max_items=25, additional_rows=additional_rows)

    set_up_table(api_key, cur, conn, 'classification', max_items=25, additional_rows=additional_rows)

    conn.close()

if __name__ == '__main__':
    api_key = '39ce36a2-869c-4bc0-b20b-d1bf6a65f855'
    additional_rows = 25  # Always set to 25
    gather_data(api_key, additional_rows)