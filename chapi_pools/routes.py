from views import index, Handler, AJAX
import aiohttp
from settings import BASE_DIR

handler = Handler()

def setup_routes(app):
    app.router.add_get('/', index) # It's done!
    # AJAX 
    app.router.add_post('/get_api', AJAX.get_api, expect_handler = aiohttp.web.Request.json) # Raise on GET API click
    app.router.add_post('/search', AJAX.get_chats, expect_handler = aiohttp.web.Request.json)
    app.router.add_post('/check_api', AJAX.check_api, expect_handler = aiohttp.web.Request.json)
    app.router.add_post('/check_permission', AJAX.check_permission, expect_handler=aiohttp.web.Request.json)
    # Web Socket 
    app.router.add_get('/{API}/{chat}', handler.websocket_handler)  # Get chat with 
    # API routes
    app.router.add_post('/api-{API}/message', handler.message_handle)
    app.router.add_post('/api-{API}/user', handler.user_handler)
    app.router.add_post('/api-{API}/chat', handler.chat_handler)
    # Static 
    app.router.add_static('/static', str(BASE_DIR / 'chapi_pools' / 'static'), name='static')