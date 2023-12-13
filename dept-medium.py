import requests
import matplotlib.pyplot as plt
import os
import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + 'museums.db')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS departments')

cur.execute('''CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY,
                department TEXT NOT NULL, 
                medium TEXT
            )''')

# Insert each piece info into the database
cur.execute('''INSERT INTO departments (id, department, medium)
               SELECT id, department, medium
               FROM artworks
            ''')

conn.commit()

cur.execute('''SELECT departments.department, COUNT(DISTINCT artworks.medium) AS medium_count
                FROM artworks
                JOIN departments
                ON artworks.id = departments.id
                GROUP BY departments.department
                ORDER BY medium_count DESC
                ''')

medium_counts = cur.fetchall()

conn.close()

# print(medium_counts)

department, medium_count = zip(*medium_counts)

plt.figure(figsize=(10, 6))

norm = plt.Normalize(0, len(department))
colors = plt.cm.viridis_r(norm(range(len(department))))

plt.bar(department, medium_count, color=colors)
plt.xlabel('Department Names')
plt.ylabel('Number of Unique Mediums')
plt.title(f'Departments With The Highest Number of Unique Mediums')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

plt.show()
