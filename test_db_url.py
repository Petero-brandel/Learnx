import os
import dj_database_url

password = "mypassword#@/"
os.environ['DATABASE_URL'] = f"postgres://user:{password}@host:5432/dbname"

print(dj_database_url.config(default=os.environ['DATABASE_URL']))
