import requests
import json
import unittest
import matplotlib.pyplot as plt
import os
import sqlite3

def get_harvard_info(api_key, endpoint, params=None):
    base_url = 'https://api.harvardartmuseums.org'

    url = f'{base_url}{endpoint}&apikey={api_key}'

    try:
        # print(f'API Key: {api_key}')
        # print(f'Request URL: {url}')
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

# Creates a pie chart
def plot_top_classifciations(api_key, cur, conn, top_n=10):

    classifications = {
        'Paintings': ['Paintings with Text', 'Paintings with Calligraphy', 'Paintings'],
        'Sculpture': ['Sculpture', 'Casts', 'Models', 'Statues'],
        'Graphic Arts': ['Graphic Design', 'Drawings', 'Prints', 'Photographs']
    }

    classification_counts = {}
    total_objects = 0

    for category, subcategories in classifications.items():
        subcategories_query = ', '.join(f"'{subcategory}'" for subcategory in subcategories)
        cur.execute(f"SELECT SUM(object_count) FROM classification WHERE name IN ({subcategories_query})")
        count = cur.fetchone()[0]
        classification_counts[category] = count
        total_objects += count

    percentages = {category: (count / total_objects) * 100 for category, count in classification_counts.items()}

    labels = percentages.keys()
    sizes = percentages.values()

    fig, ax = plt.subplots(figsize=(8,8))
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops=dict(color="w"))

    legend_labels = []
    for category, subcategories in classifications.items():
        subcategory_str = ',\n'.join(subcategories)
        legend_labels.append(f"{category}: {subcategory_str}")
    
    ax.legend(wedges, legend_labels, title="Subcategories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    ax.set_title('Percentage of Artwork by Classification')
    
    return plt

def plot_top_periods(api_key, cur, conn, top_n=10):

    cur.execute('''
        SELECT name, object_count
        FROM period
        ORDER BY object_count DESC
        LIMIT ?
    ''', (top_n,))

    top_periods = cur.fetchall()

    period_names, object_counts = zip(*top_periods)

    plt.figure(figsize=(10, 6))

    norm = plt.Normalize(0, len(period_names))
    colors = plt.cm.viridis_r(norm(range(len(period_names))))

    plt.bar(period_names, object_counts, color=colors)
    plt.xlabel('Art Periods')
    plt.ylabel('Number of Artworks')
    plt.title(f'Art Periods With The Highest Number of Artworks')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    return plt

class TestHarvardArtMuseumAPI(unittest.TestCase):    

    def setUp(self):
        self.api_key = '39ce36a2-869c-4bc0-b20b-d1bf6a65f855'

    def test_set_up_period_table(self):
        cur, conn = set_up_database("harvardmuseum")

        set_up_period_table(self.api_key, cur, conn, max_items=25)

        conn.close()

    def test_set_up_classifciation_table(self):
        cur, conn = set_up_database("harvardmuseum")

        set_up_classification_table(self.api_key, cur, conn, max_items=25)

        conn.close()

    def test_plot_top_periods(self):
        cur, conn = set_up_database("harvardmuseum")
        set_up_period_table(self.api_key, cur, conn, max_items=25)
        plotter = plot_top_periods(self.api_key, cur, conn, top_n=10)
        plotter.show()  
        conn.close()

    def test_plot_top_classifications(self):
        cur, conn = set_up_database("harvardmuseum")
        set_up_classification_table(self.api_key, cur, conn, max_items=25)
        plotter = plot_top_classifciations(self.api_key, cur, conn, top_n=10)
        plotter.show()  
        conn.close()

if __name__ == '__main__':
    unittest.main()