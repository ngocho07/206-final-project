import requests
import matplotlib.pyplot as plt
import os
import sqlite3

# Connect to SQLite database or create it if it doesn't exist.
# Defines cursor (cur) and connection (conn) globally.
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + 'museums.db')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS departments')

# Creates departments table to store each piece's id with its department value
cur.execute('''CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY,
                department TEXT NOT NULL
            )''')

# Insert each piece's info into the table
cur.execute('''INSERT INTO departments (id, department)
               SELECT id, department
               FROM artworks
            ''')

conn.commit()

# Join departments table and artworks table to find number of distinct mediums
# (stored in artwoks) that belongs to each department in the database (stored
# in departments)
cur.execute('''SELECT departments.department, COUNT(DISTINCT artworks.medium) AS medium_count
                FROM artworks
                JOIN departments
                ON artworks.id = departments.id
                GROUP BY departments.department
                ORDER BY medium_count DESC
                ''')

# Fetches results and store each of deparment names and unique medium counts
# in a separate list
medium_counts = cur.fetchall()
department, medium_count = zip(*medium_counts)

# Close connection
conn.close()

# Set up plot environment
plt.figure(figsize=(10, 6))

# Color maps bar plot
norm = plt.Normalize(0, len(department))
colors = plt.cm.viridis_r(norm(range(len(department))))

# Generate bar chart to rank departments by number of unique mediums displayed in each
plt.bar(department, medium_count, color=colors)
plt.xlabel('Department Names')
plt.ylabel('Number of Unique Mediums')
plt.title(f'Departments With The Highest Number of Unique Mediums')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

plt.show()
