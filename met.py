import requests
import json
import unittest
import matplotlib.pyplot as plt
import os
import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + 'metmuseum.db')
cur = conn.cursor()

# Create a table to keep track of the last processed ID
cur.execute('''CREATE TABLE IF NOT EXISTS api_state (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      last_processed_id INT
                  )''')

# Initialize or fetch the last processed ID
cur.execute("SELECT last_processed_id FROM api_state ORDER BY id DESC LIMIT 1")
most_recent_id = cur.fetchone()
last_id = most_recent_id[0] if most_recent_id else 0
limit = 25 # Retrieve at most 25 entries every time

# Create a table
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

# Only fetch from isOnDisplay pieces
BASE_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search?isOnView=true&q=sunflower"


# Fetch object IDs
def fetch_object_ids(last_id):
    try:
        r = requests.get(BASE_URL)
        if r.status_code == 200:

            start_id = last_id + 1 # if last_id in object_ids else 0

            object_ids = r.json().get('objectIDs', []) 

            return object_ids[start_id:start_id + limit] # Fetch 25 IDs
    except:
        print("Exception!")
        return []


# Insert data into the database
def insert_data(artwork):
    # Check if the artwork already exists in the database
    cur.execute("SELECT id FROM artworks WHERE id = ?", (artwork['objectID'],))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO artworks (id, title, artist, medium, period, isHighlight) VALUES (?, ?, ?, ?, ?, ?)",
                    (artwork['objectID'], artwork['title'], artwork['artistDisplayName'], artwork['medium'], artwork['period'], artwork['isHighlight']))
        conn.commit()


def main(last_id):
    new_last_id = last_id

    # Fetch data from the API from the last_id
    object_ids = fetch_object_ids(last_id)

    for object_id in object_ids:
        # Get each object's detail
        detail = requests.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}")
        
        if detail.status_code == 200:
            insert_data(detail.json())
            new_last_id = object_id

    # Update the last processed ID in the database
    cur.execute("INSERT INTO api_state (last_processed_id) VALUES (?)", (new_last_id,))
    conn.commit()


# for offset in range(0, len(object_ids), limit):
#     ids_subset = object_ids[offset:offset+limit]

#     for object_id in ids_subset:
#     # Get each object's detail
#         detail = requests.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}")
#         if detail.status_code == 200:
#             insert_data(detail.json())
     

if __name__ == '__main__':
    main(last_id)
    conn.close()