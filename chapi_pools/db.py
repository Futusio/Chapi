import asyncio
import asyncpgsa
from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date, Boolean
)

meta = MetaData()

users = Table(              # Table of users Data
    'users', meta,
    Column('id', Integer, primary_key=True),
    Column('login', String(64), nullable=False),
    Column('token', String(32), nullable=False)
)

members = Table(            # Table of chat's members Data
    'members', meta, 
    Column('chat_id', Integer, 
        ForeignKey('chats.id',  ondelete='CASCADE')),
    Column('user_id', Integer, 
        ForeignKey('users.id',  ondelete='CASCADE')),
    Column('permit', Boolean) # 
)

chats = Table(              # Table of chats Data
    'chats', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(128), nullable=False),
    Column('isOpen', Boolean, nullable=False),
    Column('owner_id', Integer,
        ForeignKey('users.id', ondelete='CASCADE'))
)

messages = Table(           # Table of messages Data
    'messages', meta,
    Column('id', Integer, primary_key=True),
    Column('text', String(256), nullable=False),
    Column('isEdited', Boolean, nullable=False),
    Column('owner_id', Integer,
        ForeignKey('users.id', ondelete='CASCADE')),
    Column('chat_id', Integer,
        ForeignKey('chats.id', ondelete='CASCADE'))
)


async def init_pg(app):
    "At start application "
    conf = app['config']['database_uri']
    app['db'] = await asyncpgsa.create_pool(dsn=conf)
    

async def close_pg(app):
    " At close application "
    await app['db'].close()