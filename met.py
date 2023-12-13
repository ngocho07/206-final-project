import os
import sqlite3
import requests
import matplotlib.pyplot as plt
import random

# Connect to SQLite database (or create it if it doesn't exist)
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + 'museums.db')
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
                      department TEXT
            )''')
conn.commit()


def generate_random_department():
    return f"https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds={random.randint(1, 21)}"


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
        cur.execute("INSERT INTO artworks (id, title, artist, medium, period, department) VALUES (?, ?, ?, ?, ?)",
                    (artwork['objectID'], artwork['title'], artwork['artistDisplayName'], artwork['medium'], artwork['department']))
        conn.commit()


def load_data(last_id, dept_url):
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


def make_pie_chart_with_legend():
    # Count the number of artworks for each medium
    cur.execute("SELECT medium, COUNT(*) FROM artworks GROUP BY medium")
    medium_counts = cur.fetchall()

    # Extract medium names and counts for the pie chart
    mediums = [item[0] for item in medium_counts]
    counts = [item[1] for item in medium_counts]

    conn.close()

    ###########################

    # Adding an 'Other' count

    # Determine the threshold for minimum count to get its own slice
    threshold = 3

    # Create new lists for the adjusted categories and counts
    adjusted_mediums = []
    adjusted_counts = []
    other_count = 0

    # Iterate through the counts and sum up the smaller categories
    for medium, count in zip(mediums, counts):
        if count < threshold:
            other_count += count
        else:
            adjusted_mediums.append(medium)
            adjusted_counts.append(count)

    # Add the 'Other' category if there are any small categories
    if other_count > 0:
        adjusted_mediums.append('Other')
        adjusted_counts.append(other_count)

    
    ###########################

    # Make chart and create legend
    plt.figure(figsize=(10, 8))
    patches, autotexts, texts = plt.pie(adjusted_counts, autopct='%1.1f%%', startangle=140)
    plt.legend(patches, adjusted_mediums, loc="best", title="Mediums")
    plt.title('Distribution of Mediums in the Met Collection of Asian Art')

    plt.show()

def make_pie_chart():
    # Count the number of artworks for each medium
    cur.execute("SELECT medium, COUNT(*) FROM artworks GROUP BY medium")
    medium_counts = cur.fetchall()

    # Extract medium names and counts for the pie chart
    mediums = [item[0] for item in medium_counts]
    counts = [item[1] for item in medium_counts]

    conn.close()

    # Make chart and create legend
    plt.figure(figsize=(10, 8))
    plt.pie(counts, labels = mediums, autopct='%1.1f%%', startangle=140)
    plt.title('Distribution of Art Mediums in the Met Collection')

    plt.show()
    
def make_bar_plot():
    # Count the number of artworks for each medium
    cur.execute("SELECT medium, COUNT(*) FROM artworks GROUP BY medium")
    medium_counts = cur.fetchall()

    # Extract medium names and counts for the pie chart
    mediums = [item[0] for item in medium_counts]
    counts = [item[1] for item in medium_counts]

    plt.figure(figsize=(10, 8))
    plt.barh(mediums, counts, color='skyblue')
    plt.xlabel('Medium')
    plt.ylabel('Number of Artworks')
    plt.title('Number of Artworks by Medium')
    plt.yticks(rotation=45, ha='right')  # Rotate the y-axis labels
    plt.tight_layout()  # Adjust layout to fit all labels
    plt.show()


    
def main():
    # Uncomment to load database

    # Feel free to choose from any of the API links below
    # Example: load_data(last_index, PAINT_URL)
    PAINT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=11"
    SCULP_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=12"
    HIGHL_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search?isHighlight=true&q=sunflowers"
    ASIAN_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=6"
    
    # Or keep it dicey and generate a random department number every time
    load_data(last_index, generate_random_department())

    # Uncomment for visualization
    make_pie_chart_with_legend()


if __name__ == '__main__':
    main()
