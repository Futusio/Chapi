from aiohttp import web
import aiohttp_jinja2
import jinja2
from settings import config, BASE_DIR
from routes import setup_routes
from db import init_pg, close_pg

app = web.Application()
aiohttp_jinja2.setup(app,
    loader=jinja2.FileSystemLoader(str(BASE_DIR / 'chapi_pools' / 'templates')))
app['config'] = config
setup_routes(app) # SetUp routes
app.on_startup.append(init_pg) # A Database pool 
app.on_cleanup.append(close_pg) # Drop the poop

# web.run_app(app, host='192.168.1.104', port=5000) # House 
# web.run_app(app, host="192.168.1.89", port=5000) # Artem
web.run_app(app)