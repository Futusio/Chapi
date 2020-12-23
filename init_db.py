from sqlalchemy import create_engine, MetaData

from chapi_pools.db import users, members, chats, messages
from chapi_pools.settings import config

DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"

def create_table(engine):
    meta = MetaData()
    meta.create_all(bind=engine, tables=[users, members, chats, messages])


def sample_data(engine):
    conn = engine.connect()
    # Into users
    conn.execute(users.insert(), [
        {'login': 'Test',
         'token': '112233445566'}
    ])
    # Into chat

    conn.close()


if __name__ == "__main__":
    db_url =  DSN.format(**config['postgres'])
    engine = create_engine(db_url)
    try:
        create_table(engine)
        sample_data(engine)
        print('Database was successly created')
    except Exception as e:
        print("Error: ", e)