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

# Create a table
cur.execute('''CREATE TABLE IF NOT EXISTS artworks (
                      id INTEGER PRIMARY KEY, 
                      title TEXT, 
                      artist TEXT, 
                      medium TEXT, 
                      isOnView BOOLEAN
                  )''')