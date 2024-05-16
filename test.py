import mariadb
import sys

try:
        conn = mariadb.connect(
                user="zavora",
                password="zavora123",
                host="10.42.0.1",
                port=3306,
                database="parkovisko"
)
except mariadb.Error as e:
        print(f"Error: {e}")
        sys.exit(1)

cur = conn.cursor()
cur.execute(f'SELECT * FROM parked_cars WHERE spz="ngkads"')
for spz in cur:
        print(spz[1])
