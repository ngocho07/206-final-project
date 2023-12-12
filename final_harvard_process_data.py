import os
import sqlite3
import matplotlib.pyplot as plt


# Creates a pie chart
def plot_top_classifications(cur, classification_data, top_n=10):

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
    ax.set_title('Percentage of Art Subcategories by Overall Classifications')
    
    return plt

def plot_top_periods(cur, period_data, top_n=10):

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

def process_and_visualize_data():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "museums.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute('''
        SELECT name, object_count
        FROM classification
        ORDER BY object_count DESC
    ''')

    classification_data = cur.fetchall()
    plot_top_classifications(cur, classification_data)

    cur.execute('''
        SELECT name, object_count
        FROM period
        ORDER BY object_count DESC        
    ''')

    period_data = cur.fetchall()
    plot_top_periods(cur, period_data)

    plt.show()

    conn.close()

if __name__ == '__main__':
    process_and_visualize_data()
