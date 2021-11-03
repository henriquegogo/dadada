from fastapi import Body, FastAPI, HTTPException
from uvicorn import run # type: ignore
import sqlite3

class Database:
    db_path = 'database.db'

    def __init__(self):
        connection = sqlite3.connect(self.db_path)
        self.cursor = connection.cursor()
        self.execute = self.cursor.execute
        self.commit = connection.commit

    def tables(self):
        return [row[0] for row in
                self.execute('SELECT name FROM sqlite_master WHERE type="table" AND name NOT LIKE "sqlite_%"')]

    def list(self, collection: str):
        schema = [row[1] for row in self.execute(f'PRAGMA table_info({collection})')]
        return [zip(schema, row) for row in self.execute(f'SELECT * FROM {collection}')]

    def create(self, collection: str, body: dict):
        schema = [row[1] for row in self.execute(f'PRAGMA table_info({collection})')]
        if not len(schema): self.execute(f'CREATE TABLE {collection} (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE)')
        for key, value in body.items():
            column_type = 'INTEGER' if isinstance(value, int) else 'REAL' if isinstance(value, float) else 'TEXT'
            if key not in schema: self.execute(f'ALTER TABLE {collection} ADD COLUMN {key} {column_type}')
        keys = ', '.join([key for key in body.keys()])
        values = str([value for value in body.values()])[1:-1]
        self.execute(f'INSERT INTO {collection} ({keys}) VALUES ({values})')
        self.commit()
        return self.read(collection, str(self.cursor.lastrowid))

    def read(self, collection: str, id: str):
        schema = [row[1] for row in self.execute(f'PRAGMA table_info({collection})')]
        return [zip(schema, row) for row in self.execute(f'SELECT * FROM {collection} WHERE id = ?', id)][0]

    def update(self, collection: str, id: str, body: dict):
        for key, value in body.items(): self.execute(f'UPDATE {collection} SET {key} = "{value}" WHERE id = ?', id)
        self.commit()
        return self.read(collection, id)

    def delete(self, collection: str, id: str):
        self.execute(f'DELETE FROM {collection} WHERE id = ?', id)
        self.commit()

app = FastAPI()

@app.get('/')
def root():
    return Database().tables()

@app.get('/{collection}')
def list(collection: str):
    try: return Database().list(collection)
    except: raise HTTPException(status_code=404)

@app.post('/{collection}')
def create(collection: str, body: dict = Body(None)):
    try: return Database().create(collection, body)
    except: raise HTTPException(status_code=400)

@app.get('/{collection}/{id}')
def read(collection: str, id: str):
    try: return Database().read(collection, id)
    except: raise HTTPException(status_code=404)

@app.put('/{collection}/{id}')
def update(collection: str, id: str, body: dict = Body(None)):
    try: return Database().update(collection, id, body)
    except: raise HTTPException(status_code=400)

@app.delete('/{collection}/{id}')
def delete(collection: str, id: str):
    try:
        Database().delete(collection, id)
        return HTTPException(status_code=200)
    except: raise HTTPException(status_code=404)

if __name__ == '__main__':
    run('__main__:app')
