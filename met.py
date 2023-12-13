import os
import sqlite3
import requests
import matplotlib.pyplot as plt
import random


# Connect to SQLite database or create it if it doesn't exist.
# Defines cursor (cur) and connection (conn) globally.
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + 'museums.db')
cur = conn.cursor()


#########################
# This is the part that limited the data to 25 items stored each time you ran this file

# Create a SQLite table to keep track of the last processed ID.         
cur.execute('''CREATE TABLE IF NOT EXISTS api_state (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      last_processed_index INT
                )''')

# Initialize or fetch the last processed ID
cur.execute("SELECT last_processed_index FROM api_state ORDER BY id DESC LIMIT 1")
most_recent_index = cur.fetchone()
last_index = most_recent_index[0] if most_recent_index else 0

# Define limit at 25 rows each time
limit = 25 

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
    '''
    Generates a URL with a random department ID for accessing the Met Museum API.

    This function creates a URL string for the Met API that includes a random 
    department ID between 1 and 21. This URL can be used to query the API 
    for objects from that randomly selected department.

    Parameters
    ----------
    None

    Returns
    -------
    str: A string representing the API link to the database of generated department ID
    '''  
    return f"https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds={random.randint(1, 21)}"


def fetch_object_ids(start, end, url):
    '''
    Fetches a range of object IDs from the Met Museum API based on the provided 
    start and end indices.

    Parameters
    ----------
    start : int
        The starting index for the range of object IDs to be fetched.
    end : int
        The ending index for the range of object IDs to be fetched.
    url : str
        The URL of the API endpoint from which to fetch the object IDs.

    Returns
    -------
    list of int
        A list of object IDs within the specified range. If the API call fails, 
        an empty list is returned.

    Exceptions
    ----------
    Prints an error message if the API request fails for any reason.
    '''
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


def insert_data(artwork):
    '''
    Inserts an artwork's data into the database.

    This function first checks if an artwork with the same ID already 
    exists to avoid duplicates. If the artwork is not already in the database, 
    it inserts the new record.

    Parameters
    ----------
    artwork : dict
        A dictionary containing the details of the artwork with keys 
        'objectID', 'title', 'artistDisplayName', 'medium', and 'department'.

    Returns
    -------
    None
    '''

    # Check if the artwork already exists in the database
    cur.execute("SELECT id FROM artworks WHERE id = ?", (artwork['objectID'],))

    if cur.fetchone() is None:
        cur.execute("INSERT INTO artworks (id, title, artist, medium, period, department) VALUES (?, ?, ?, ?, ?)",
                    (artwork['objectID'], artwork['title'], artwork['artistDisplayName'], artwork['medium'], artwork['department']))
        conn.commit()


def load_data(last_id, dept_url):
    '''
    Fetches and loads artwork data from the API into the database.

    Parameters
    ----------
    last_id : int
        The ID from which to start fetching artwork data.
    dept_url : str
        The URL of the Met Museum API endpoint for fetching artwork IDs.

    Returns
    -------
    None
    '''

    # Initializes start index to the last_id fetched from api_state table
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

    # Update the last processed ID in the api_state table
    cur.execute("INSERT INTO api_state (last_processed_index) VALUES (?)", (start,))
    conn.commit()


def make_pie_chart_with_legend():
    '''
    Creates and displays a pie chart with a legend, showing the distribution of mediums in the 
    Met Collection. This function adjusts the categories by grouping smaller ones into an 
    'Other' category.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''
    # Count the number of artworks for each medium
    cur.execute("SELECT medium, COUNT(*) FROM artworks GROUP BY medium")
    medium_counts = cur.fetchall()

    # Extract medium names and counts for the pie chart
    mediums = [item[0] for item in medium_counts]
    counts = [item[1] for item in medium_counts]
    conn.close()

    # Call create_other_category_in_pie() to group smaller categories under Other
    adjusted_mediums = create_other_category_in_pie(mediums, counts)[0]
    adjusted_counts = create_other_category_in_pie(mediums, counts)[1]

    # Make chart and create legend
    plt.figure(figsize=(10, 8))
    patches, autotexts, texts = plt.pie(adjusted_counts, autopct='%1.1f%%', startangle=140)
    plt.legend(patches, adjusted_mediums, loc="best", title="Mediums")
    plt.title('Distribution of Mediums in the Met Collection')
    plt.show()


def create_other_category_in_pie(mediums, counts):
    '''
    Creates and counts smaller categories into an 'Other' category in a pie chart.

    Parameters
    ----------
    mediums : list of str
        List of medium names fetched from table.
    counts : list of int
        List of counts of each medium fetched from table.

    Returns
    -------
    adjusted_mediums : list of str
        List of medium names adjusted with small mediums under the threshold 
        abstracted by the label 'Other'.
    adjusted_counts : list of int
        List of counts of each medium adjusted with medium counts under the 
        threshold totaled into one int.
    '''

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

    return [adjusted_mediums, adjusted_counts]


def make_pie_chart():
    '''
    Creates a normal pie chart showing the distribution of art mediums in the Met Collection.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''

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

 
def main():
    '''
    Main function calls load_data() to process data from the Met API and display visualizations.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''
    # Feel free to choose from any of the API links below to load data from that specific 
    # subset of the Met API data. An example is as below:
    # load_data(last_index, PAINT_URL)
    PAINT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=11"
    SCULP_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=12"
    HIGHL_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search?isHighlight=true&q=sunflowers"
    ASIAN_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects?metadataDate=2018-10-22&departmentIds=6"
    
    # Or keep it dicey and generate a random department number every time
    # you call this function
    load_data(last_index, generate_random_department())

    # Call chart making functions to generate visualization
    make_pie_chart_with_legend()


if __name__ == '__main__':
    main()
