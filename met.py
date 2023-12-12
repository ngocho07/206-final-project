import requests
import matplotlib.pyplot as plt
import os
import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + 'metmuseum.db')
cur = conn.cursor()


#########################
# This is the part that limited the data to 25 items stored each time you ran this file
#########################

# Create a table to keep track of the last processed ID
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
                      isHighlight BOOLEAN
                  )''')

# results = cur.fetchall() # Fetch before commit
conn.commit()

PAINT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=11"
SCULP_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=12"
HIGHL_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search?isHighlight=true&q=sunflowers"


# Fetch object IDs
def fetch_object_ids(start, end, url):
    try:
        # Requests from specific department
        r = requests.get(PAINT_URL)
        
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
        cur.execute("INSERT INTO artworks (id, title, artist, medium, period, isHighlight) VALUES (?, ?, ?, ?, ?, ?)",
                    (artwork['objectID'], artwork['title'], artwork['artistDisplayName'], artwork['medium'], artwork['period'], artwork['isHighlight']))
        conn.commit()


def main(last_id):
    start = last_id
    end = last_id + limit

    # Fetch data from the API from the last_id
    object_ids = fetch_object_ids(start, end, PAINT_URL)

    for object_id in object_ids:
        # Get each object's detail
        detail = requests.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}")
        
        if detail.status_code == 200:
            insert_data(detail.json())
            start = end + 1

    # Update the last processed ID in the database
    cur.execute("INSERT INTO api_state (last_processed_index) VALUES (?)", (start,))
    conn.commit()

     

if __name__ == '__main__':
    main(last_index)
    conn.close()