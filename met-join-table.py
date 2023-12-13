import requests
import matplotlib.pyplot as plt
import os
import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + 'museums.db')
cur = conn.cursor()

URL = "https://collectionapi.metmuseum.org/public/collection/v1/departments"

cur.execute('''DROP TABLE IF EXISTS departments''')

# Create artworks table to store artwork data
cur.execute('''CREATE TABLE IF NOT EXISTS departments (
                departmentId INTEGER PRIMARY KEY, 
                displayName TEXT
            )''')
conn.commit()

# Fetch object IDs
# def fetch(url):
try:
    r = requests.get(URL)
    if r.status_code == 200:
        data = r.json()
except:
    print("Cannot open API!")
    data = {}

# Insert each piece info into the database
for department in data["departments"]:
    cur.execute("INSERT INTO departments (departmentId, displayName) VALUES (?, ?)",
                (department['departmentId'], department['displayName']),)
    conn.commit()

cur.execute("""SELECT d.departmentId, d.displayName, COUNT(a.id) AS artworkCount
                FROM departments d
                JOIN artworks a ON d.displayName = a.department
                GROUP BY d.departmentId, d.displayName""")

department_artwork_counts = cur.fetchall()

# for row in department_artwork_counts:
#     print(f"Department ID: {row[0]}, Department Name: {row[1]}, Number of Artworks: {row[2]}")

id = [item[0] for item in department_artwork_counts]
num = [item[2] for item in department_artwork_counts]

conn.close()

plt.figure(figsize=(10, 8))
plt.pie(num, labels = id, autopct='%1.1f%%', startangle=140)
plt.title('Distribution of Artworks by Department Number in a selection of the Met Collection')

plt.show()
