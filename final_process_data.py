import os
import sqlite3
import matplotlib.pyplot as plt

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "museums.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()


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
    ax.set_title('Percentage of Artwork by Classification')
    
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


def met_pie_chart_with_legend():
    # Count the number of artworks for each medium
    cur.execute("SELECT medium, COUNT(*) FROM artworks GROUP BY medium")
    medium_counts = cur.fetchall()

    # Extract medium names and counts for the pie chart
    mediums = [item[0] for item in medium_counts]
    counts = [item[1] for item in medium_counts]

    conn.close()

    ###########################
    # Determine the threshold for minimum count to get its own slice
    threshold = 4

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
    patches, texts, autotexts = plt.pie(adjusted_counts, autopct='%1.1f%%', startangle=140)
    plt.legend(patches, adjusted_mediums, loc="upper right", title="Mediums")
    plt.title('Distribution of Mediums in the Met Collection of Asian Art')

    plt.show()


def met_join_chart():
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

if __name__ == '__main__':
    process_and_visualize_data()
    met_pie_chart_with_legend()
    met_join_chart()
