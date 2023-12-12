import requests
import json
import unittest
import matplotlib.pyplot as plt
import os
import sqlite3

def get_harvard_info(api_key, endpoint, params=None):
    base_url = 'https://api.harvardartmuseums.org'

    url = f'{base_url}{endpoint}?apikey={api_key}'

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
    conn = sqlite3.connect(path + "/" + db)
    cur = conn.cursor()
    return cur, conn

def set_up_table(harvard_data, cur, conn):
    pass

class TestHarvardArtMuseumAPI(unittest.TestCase):    

    def setUp(self):
        self.api_key = '39ce36a2-869c-4bc0-b20b-d1bf6a65f855'

    def test_get_data_valid_object(self):
        endpoint = '/period'
        harvard_data = get_harvard_info(self.api_key, endpoint)
        print(harvard_data)
        
        # self.assertIsNotNone(harvard_data)
        # title = harvard_data.get('title', None)
        # date = harvard_data.get('dated', None)
        # self.assertIsNotNone(title)
        # self.assertIsNotNone(date)


if __name__ == '__main__':
    unittest.main()