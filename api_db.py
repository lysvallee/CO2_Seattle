import requests
import psycopg2

# Set up the API endpoint URL, table name, and database connection string
url = "https://data.seattle.gov/resource/2bpz-gwpy.json"
table_name = "buildings"
connection_string = "postgresql://co2-sa-db.postgres.database.azure.com:5432/seattlebeb?user=co2sodapg&password=Greta2023&sslmode=require"

# Connect to the database and retrieve the column names from the buildings table
with psycopg2.connect(connection_string) as conn:
    with conn.cursor() as cur:
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
        columns = [row[0] for row in cur.fetchall()]

# Set the maximum number of rows per request and the starting offset
limit = 1000
offset = 0

# Keep requesting data until all rows have been retrieved
rows = []
while True:
    # Send a request to the API with the current limit and offset values
    response = requests.get(f"{url}?$limit={limit}&$offset={offset}")
    data = response.json()
    
    # If there is no data, we have reached the end of the results
    if not data:
        break
    
    # Add the retrieved rows to our list of rows
    for row in data:
        # Set a default value for the totalghgemissions column
        row.setdefault("totalghgemissions", -1)
        
        # Filter out any columns that are not in the buildings table
        filtered_row = {key: value for key, value in row.items() if key in columns}
        rows.append(filtered_row)
    
    # Increment the offset to retrieve the next page of results
    offset += limit

# Connect to the database and insert the retrieved data into the buildings table
with psycopg2.connect(connection_string) as conn:
    with conn.cursor() as cur:
        # Loop through the rows and insert each one into the table
        for row in rows:
            values = [row.get(column) for column in columns]
            placeholders = ",".join(["%s"] * len(values))
            query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            cur.execute(query, values)
    
    # Commit the changes to the database
    conn.commit()
