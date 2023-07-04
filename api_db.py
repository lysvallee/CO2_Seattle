import requests
import psycopg2

# Set up the API endpoint URL, table name, and database connection string
url = "https://data.seattle.gov/resource/2bpz-gwpy.json"
table_name = "buildings"
connection_string = "postgresql://co2-sa-db.postgres.database.azure.com:5432/seattlebeb?user=co2sodapg&password=Greta2023&sslmode=require"

# Connect to the database and modify each column to be nullable
with psycopg2.connect(connection_string) as conn:
    with conn.cursor() as cur:
        # Retrieve the column names from the buildings table
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
        columns = [row[0] for row in cur.fetchall()]

        # Retrieve the primary key column name
        cur.execute(f"SELECT column_name FROM information_schema.key_column_usage WHERE table_name = '{table_name}' AND constraint_name LIKE '%_pkey'")
        pk_column = cur.fetchone()[0]

        # Modify each column to be nullable except for the primary key column
        for column_name in columns:
            if column_name == pk_column:
                cur.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE bigint USING osebuildingid::bigint;")
            else:
                cur.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP NOT NULL;")
    
    # Commit the changes to the database
    conn.commit()

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
            print(cur.mogrify(query, values))
            cur.execute(query, values)
    
    # Commit the changes to the database
    conn.commit()
    
    # Print the number of rows inserted
    print(f"Inserted {len(rows)} rows into the '{table_name}' table.")
