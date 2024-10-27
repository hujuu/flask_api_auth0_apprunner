from sqlalchemy import create_engine
from os import environ as env

SQLALCHEMY_DATABASE_URI = env.get("SQLALCHEMY_DATABASE_URI")
# create the engine with the database URL
engine = create_engine(SQLALCHEMY_DATABASE_URI)
# create a connection to the database
conn = engine.connect()
# execute a SQL query
result = conn.execute('SELECT * FROM speakers')
# loop through the result set and print the values
for row in result:
    print(row)
# close the result set and connection
result.close()
conn.close()
