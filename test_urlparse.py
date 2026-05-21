from urllib.parse import urlparse

password = "mypassword#@/"
url = f"postgres://user:{password}@host:5432/dbname"

parsed = urlparse(url)
print("hostname:", parsed.hostname)
print("password:", parsed.password)
print("path:", parsed.path)
