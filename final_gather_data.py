import requests
import os
import sqlite3

########################### MET ##############################

# Connect to SQLite database (or create it if it doesn't exist)
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + 'museums.db')
cur = conn.cursor()


#########################
# This is the part that limited the data to 25 items stored each time you ran this file
#########################

# Create a table to keep track of the last processed ID
cur.execute('''DROP TABLE IF EXISTS api_state''')
            
cur.execute('''CREATE TABLE IF NOT EXISTS api_state (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      last_processed_index INT
                )''')

# Initialize or fetch the last processed ID
cur.execute("SELECT last_processed_index FROM api_state ORDER BY id DESC LIMIT 1")
most_recent_index = cur.fetchone()
last_index = most_recent_index[0] if most_recent_index else 0

# Retrieve at most 25 entries every time
limit = 25 

#########################
# Ends part that limited the data to 25 items stored each time you ran this file
#########################


# Create artworks table to store artwork data
cur.execute('''CREATE TABLE IF NOT EXISTS artworks (
                      id INTEGER PRIMARY KEY, 
                      title TEXT, 
                      artist TEXT, 
                      medium TEXT, 
                      period TEXT,
                      department TEXT
            )''')
conn.commit()

PAINT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=11"
SCULP_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=12"
HIGHL_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search?isHighlight=true&q=sunflowers"
ASIAN_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=6"



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

    set_up_period_table(api_key, cur, conn, max_items=25)

    set_up_classification_table(api_key, cur, conn, max_items=25)

    conn.close()




########################### MET ##############################

# Fetch object IDs
def fetch_object_ids(start, end, url):
    try:
        # Requests from specific department
        r = requests.get(url)
        
        if r.status_code == 200:
            # Fetch 25 IDs from last processed index
            object_ids = r.json().get('objectIDs', [])[start:end]
            return object_ids
    except:
        print("Cannot open API!")
        return []


# Insert each piece info into the database
def insert_data(artwork):
    # Check if the artwork already exists in the database
    cur.execute("SELECT id FROM artworks WHERE id = ?", (artwork['objectID'],))

    if cur.fetchone() is None:
        cur.execute("INSERT INTO artworks (id, title, artist, medium, period, department) VALUES (?, ?, ?, ?, ?, ?)",
                    (artwork['objectID'], artwork['title'], artwork['artistDisplayName'], artwork['medium'], artwork['period'], artwork['department']))
        conn.commit()


def load_met_data(last_id, dept_url, cur, conn):
    start = last_id
    end = last_id + limit

    # Fetch data from the API from the last_id
    object_ids = fetch_object_ids(start, end, dept_url)

    for object_id in object_ids:
        # Get each object's detail
        detail = requests.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}")
        
        if detail.status_code == 200:
            insert_data(detail.json())
            start = end + 1

    # Update the last processed ID in the database
    cur.execute("INSERT INTO api_state (last_processed_index) VALUES (?)", (start,))
    conn.commit()


def load_dept_table(cur, conn):
    URL = "https://collectionapi.metmuseum.org/public/collection/v1/departments"

    # Create artworks table to store artwork data
    cur.execute('''CREATE TABLE IF NOT EXISTS departments (
                    departmentId INTEGER PRIMARY KEY, 
                    displayName TEXT
                )''')
    conn.commit()

    # Fetch object IDs
    def fetch(url):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return r.json()
        except:
            print("Cannot open API!")
            return {}

    # Insert each piece info into the database
    def insert_data(data):
        for department in data["departments"]:
            cur.execute("INSERT INTO departments (departmentId, displayName) VALUES (?, ?)",
                        (department['departmentId'], department['displayName']),)
            conn.commit()

    json_data = fetch(URL)
    insert_data(json_data)


if __name__ == '__main__':
    api_key = '39ce36a2-869c-4bc0-b20b-d1bf6a65f855'
    gather_data(api_key)

    load_met_data(last_index, ASIAN_URL, cur, conn)
    load_dept_table(cur, conn)