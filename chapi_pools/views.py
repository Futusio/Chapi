from aiohttp import web
import aiohttp
from sqlalchemy import select
import aiohttp_jinja2
import json
from datetime import datetime
import db
from settings import config
from hashlib import md5


# Index page is below 
@aiohttp_jinja2.template('index.html')
async def index(request):
    """ GET method to give index page """
    async with request.app['db'].acquire() as conn:
        query = db.users.select().where(db.users.c.id == 0)
        result = await conn.fetch(query)
    return {}


class AJAX():
    async def get_api(request):
        """ The view with AJAX get API Token """
        data = await request.json()
        login = data['login'] # Unpack data
        async with request.app['db'].acquire() as conn: # Looking for the row in the table
            query = db.users.select().where(db.users.c.login.contains(login.title()))
            result = await conn.fetch(query)
            if len(result) > 0: # If row is found view returns error
                return web.json_response({'status':'error','message':'The login is busy'})
            else: # Else inserting new user to database
                token = md5(login.title().encode()).hexdigest()
                query = db.users.insert().values(
                                login=login.title(), 
                                token=token,)
                await conn.fetch(query)
                return web.json_response({'status':'success','token':token})


    async def check_api(request):
        data = await request.json()
        API = data['API']
        async with request.app['db'].acquire() as conn:
            query = db.users.select().where(db.users.c.token == API)
            result = await conn.fetch(query)
            if len(result) == 0:
                response = {'status':'error'}
            else:
                response = {'status':'success'}
        return web.json_response(response)


    async def check_permission(request):
        data = await request.json()
        API = data['API']
        chat = data['chat']
        async with request.app['db'].acquire() as conn:
            # First check status of the chat 
            query = db.chats.select().where(db.chats.c.name == chat)
            chat = await conn.fetch(query)
            user_id = await PostgreSQL.get_user_id(conn, token=API)
            
            if chat[0]['isOpen'] or chat[0]['owner_id'] == user_id:
                response = {'status':'success'}
            else:
                query = db.users.select().where(db.users.c.token == API)
                user = await conn.fetch(query)
                query = db.members.select().where((db.members.c.chat_id == chat[0]['id']) & (db.members.c.user_id == user[0]['id']))
                result = await conn.fetch(query)
                if len(result) == 0:
                    response = {'status':'erroe'}
                else:
                    response = {'status':'success'}
        return web.json_response(response)

    async def get_chats(request):
        data = await request.json()
        name = data['name']
        result = await PostgreSQL.get_chats(request, name)
        return web.json_response(result)

class Handler():

    def __init__(self):
        self.connected = dict()

    async def chat_handler(self, request):
        token = request.match_info['API'] # Get token
        try: 
            data = await request.json()
            json_status = JSONParser.parse_chat_json(data)
            if json_status['status'] == 'error':
                response = { # And make a response if the status is error
                    'status':'error',
                    'message': json_status['message']
                }
                return web.json_response(response)
            action = data['action']
            if action == 'create':
                response = await PostgreSQL.chat_actions(request, token, data)
            else:            
                isExist = await PostgreSQL.does_chat_exist(request, data['chat'])
                if isExist['status'] == 'success':
                    response = await PostgreSQL.chat_actions(request, token, data)
                else:
                    response = {'status': 'fail', 'message':'Chat does not exist'}

        except json.decoder.JSONDecodeError:
            response = {
                'status': 'error',
                'message': 'You have to pass a JSON with the request'
            }
        return web.json_response(response)

    async def user_handler(self, request):
        # First step: Call RequestParser()
        token = request.match_info['API'] # Get token
        # Second step: 
        try:
            data = await request.json() # get json data
            json_status = JSONParser.parse_user_json(data)

            if json_status['status'] == 'error':
                response = { # And make a response if the status is error
                    'status':'error',
                    'message': json_status['message']
                }
                return web.json_response(response)
            # Next go to the database    
            action = data['action']
            isExist = await PostgreSQL.does_chat_exist(request, data['chat'])
            if isExist['status'] == 'success':
                response = await PostgreSQL.user_action(request, token, data)
            else:
                response = {'status':'fail', 'message':'chat does not exist'}
        except json.decoder.JSONDecodeError:
            response = {
                'status':'error',
                'message': 'You have to pass a JSON with the request'
            }
        return web.json_response(response)

    async def message_handle(self, request):
        token = request.match_info['API']
        try:
            # First function checks JSON format
            data = await request.json()
            json_status = JSONParser.parse_message_json(data)
            if json_status['status'] == 'error':
                response = { # And make a response if the status is error
                    'status':'error',
                    'message': json_status['message']
                }
                return web.json_response(response)
            # If json_status is success
            action = data['action']
            isExist = await PostgreSQL.does_chat_exist(request, data['chat'])
            # END OF FIRST BLOCK 
            if isExist['status'] == 'success':
                if action == 'send':
                    response = await PostgreSQL.send_message(request, token, data)
                    to_front = {
                        'action': action,
                        'user': await PostgreSQL.get_user_name(request, token),
                        'text': data['message'],
                        'token': token,
                        'id': response['msg_id'],
                    }
                elif action == 'update' or action == 'delete':
                    response = await PostgreSQL.change_message(request, token, data)
                    if action == 'delete' : # Prepare a response to 'delete'
                        to_front = {
                            'action':action,
                            'id': data.get('msg_id') if data.get('msg_id') else None
                        }
                    else:  # Prepare to 'update'
                        to_front = {
                            'action': 'update',
                            'id': data.get('msg_id') if data.get('msg_id') else None,
                            'text': data['message']
                        }
                        
                # Next need to send data on front-end
                if response['status'] == 'success':
                    for conn in self.connected[data['chat']]:
                        await conn.send_json(to_front)
            else:
                response = {
                    'status':'error',
                    'message':'The chat does not exist',
                }
        except json.decoder.JSONDecodeError:
            response = {
                'status':'error',
                'message': 'You have to pass a JSON with the request'
            }
        return web.json_response(response)


    async def websocket_handler(self, request):
        self.ws = web.WebSocketResponse()
        chat = request.match_info['chat']
        token = request.match_info['API']
        response = {}
        # If first user in chat session
        if chat not in self.connected:
            self.connected[chat] = list()

        await self.ws.prepare(request)
        self.connected[chat].append(self.ws)
        
        async with request.app['db'].acquire() as conn:
            # here we get all messages
            user_id = await PostgreSQL.get_user_id(conn, token=token)
            chat_id = await PostgreSQL.get_chat_id(conn, chat)
            query = db.messages.select().where(db.messages.c.chat_id == chat_id)
            messages = await conn.fetch(query)
            query = db.members.select().\
                where((db.members.c.chat_id == chat_id)&(db.members.c.user_id == user_id))
            status = await conn.fetch(query)
            status =  len(status) == 0 or status[0]['permit']
                
            # Below we make messages to json
            response = dict()
            response['status'] = status
            response['first'] = True
            for message in messages:
                query = db.users.select().where(db.users.c.id == message['owner_id'])
                user = await conn.fetch(query)
                response[str(message['id'])] = {
                    'action': 'send',
                    'id': message['id'],
                    'edited':message['isEdited'],
                    'user': user[0]['login'],
                    'text': message['text'],
                    'own':  True if user[0]['token'] == token else False,
                }
   

        # Send all messages
        await self.ws.send_json(response)
        # WebSocket Loop
        async for msg in self.ws:
            # Actions before mailing
            try:
                message = json.loads(msg.data)
                new_message = await PostgreSQL.send_message(request, message['token'], {'chat':message['chat'], 'message':message['message']})
                
            except: pass
            # Actions after mailing
            for conn in self.connected[chat]:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == 'close':
                        self.connected[chat].remove(conn)
                        await self.ws.close()
                    else:
                        # Send all responses
                        response = dict()
                        response['action'] = 'send'
                        response['user'] = await PostgreSQL.get_user_name(request, message['token'])
                        response['text'] = message['message']
                        response['token'] = message['token']
                        response['id'] = new_message['msg_id']
                        await conn.send_json(response)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print('ws connection closed with exception %s' %
                        self.ws.exception())

        print('websocket connection closed')
        return self.ws


class JSONParser():
    """ The class exists a few staticmethods each one checks the JSON
    which passed along with the request and returns the status of checking """
    def parse_message_json(data):
        """ The method checks JSON passed along with POST:.../api-<API>/message request """
        response = {'status':'error'} # Blank
        if data.get('chat'): # First step check does the chat exist
            chat = data['chat']
            if data.get('action'):
                action = data['action']
                print('Action is: ', action)
                if action in ['send', 'update', 'delete']:
                    if action == 'send':
                        if data.get('message'):
                            return {'status':'success'}
                        else: 
                            response['message'] = 'Request with send action has to have a message'
                    elif action == 'update':
                        if data.get('message') and data.get('msg_id'):
                            return {'status':'success'}
                        else:
                            response['message'] = 'Request with update action has to have a message and a message id'
                    elif action == 'delete':
                        if data.get('msg_id'):
                            return {'status':'success'}
                        else:
                            response['message'] = 'Request with delete action has to have a message id'
                else:
                    response['message'] = 'Message request has to have a type of the action (send, update, delete)'
            else:
                response['message'] = 'Message request has to have an action'
        else: 
            response['message'] = 'JSON must to have a chat'
        return response


    def parse_chat_json(data):
        """ The method checks JSON passed along with POST:.../message request """
        response = {'status':'error'}
        if data.get('chat'): # First step check does the chat exist
            chat = data['chat']
            if data.get('action'):
                action = data['action']
                if action in ['create', 'destroy', 'update']:
                    if action == 'create':
                        if data.get('status') is not None:
                            return {'status':'success'}
                        else: 
                            response['message'] = 'Request with create action has to have a status'
                    elif action == 'destroy':
                        return {'status':'success'}
                    elif action == 'update':
                        if data.get('name') and data.get('status') is not None:
                            return {'status':'success'}
                        else:
                            response['message'] = 'Request with update action has to have a status and new name'
                else:
                    response['message'] = 'Message request has to have a type of the action (send, update, delete)'
            else:
                response['message'] = 'Message request has to have an action'
        else: 
            response['message'] = 'JSON must to have a chat'
        return response

    def parse_user_json(data):
        response = {'status':'error'}
        if data.get('action'):
            action = data['action']
            if action in ['invite', 'kick', 'permit']:
                if action == 'invite':
                    if data.get('user') and data.get('permit') is not None: # Check constains user and writer cells 
                        response = {'status':'success'}
                    else: 
                        response['message'] = 'Request with invite action has to have a users login and boolean status'
                elif action == 'kick':
                    if data.get('user'):
                        return {'status':'success'}
                    else:
                        response['message'] = 'Request with kick action has to have a user login'
                elif action == 'permit':
                    if data.get('user') and data.get('permit') is not None:
                        return {'status': 'success'}
                    else:
                        response['message'] = 'Request with permit action has to have a users login and boolean status'
            else:
                response['message'] = 'User request has to have a type of the action (invite, kick, permit)'
        else:
            response['message'] = 'User request has to have an action'
        return response

class PostgreSQL():

    async def get_user_name(request, token):
        """ The corituine gets user name by user token """
        try: 
            async with request.app['db'].acquire() as conn:
                query = db.users.select().where(db.users.c.token == token)
                result = await conn.fetch(query)
            return result[0]['login']
        except Exception as e:
            print('Was exception: ', e)

    async def get_chats(request, name):
        try: 
            async with request.app['db'].acquire() as conn:
                query = db.chats.select().where(db.chats.c.name.contains(name))
                result = await conn.fetch(query)
                response = {}
                for i, chat in enumerate(result):
                    response[str(i)] = chat['name']
            return response
        except Exception as e:
            print('Was exception: ', e)


    # First block
    async def get_chat_id(conn, chat):
        """ It's DRY code and that two functions call very often """
        query = db.chats.select().where(db.chats.c.name == chat)
        chat = await conn.fetch(query)
        return chat[0]['id']


    async def get_user_id(conn, login=None, token=None):
        """ The second function which will call only correct data
        so it has no try\except block """
        if login:
            query = db.users.select().where(db.users.c.login == login)
            user = await conn.fetch(query)
            if len(user) == 0:
                return None
        else:
            query = db.users.select().where(db.users.c.token == token)
            user = await conn.fetch(query)
        return user[0]['id']

    # SEcond block


    async def does_chat_exist(request, chat):
        """ The corutine returns boolean
        True if the chat exists or
        False if the chat does not exist """
        try:
            async with request.app['db'].acquire() as conn:
                query = db.chats.select().where(db.chats.c.name == chat.lower())
                chat = await conn.fetch(query)
                response = {'status': 'success' if len(chat) > 0 else 'fail'}
        except:
            response = {'status':'exception', 'message':'Database error'}
        return response

    async def send_message(request, token, data):
        """ The function writes a new message into the table
        and returns the result of the try or the error message """
        # If data exists key 'message'
        try: 
            async with request.app['db'].acquire() as conn:
                # First: Get a Chat ID 
                chat_id = await PostgreSQL.get_chat_id(conn, data['chat'])
                # Second: Get an User ID 
                user_id = await PostgreSQL.get_user_id(conn, token=token)
                # Third: Add a new message
                query = db.messages.insert().values(
                        text = data['message'],
                        isEdited = False,
                        owner_id = user_id,
                        chat_id = chat_id
                    )
                # Fourth: make a response
                result = await conn.fetch(query)
                response = {
                    'status':'success',
                    'msg_id': result[0]['id']
                }
        except Exception as e:
            response = {
                'status':'error',
                'message':'Database error'
            }
        return response

    async def change_message(request, token, data):
        """ The function tries to update/delete the data in the table
        and then returns status of the try """
        try: 
            async with request.app['db'].acquire() as conn:
                # First: Get a chat ID 
                chat_id = await PostgreSQL.get_chat_id(conn, data['chat'])
                # Second: Get an User ID
                user_id = await PostgreSQL.get_user_id(conn, token=token)
                # Third: Check the message exists
                query = db.messages.select().where(db.messages.c.id == data['msg_id'])
                result = await conn.fetch(query)
                if len(result) > 0: # And after all making response 
                    if result[0]['owner_id'] != user_id:
                        response = {
                            'status':'fail',
                            'message':'It\'s not your message',
                        }
                    elif result[0]['chat_id'] != chat_id:
                        response = {
                            'status':'fail',
                            'message':'The message is not in the chat'
                        }
                    else: # Success response
                        if data['action'] == 'update': # Update message
                            query = db.messages.update().\
                                where(db.messages.c.id == data['msg_id']).\
                                    values(text = data['message'], isEdited=True)
                        else: # Delete message 
                            query = db.messages.delete().\
                                where(db.messages.c.id == data['msg_id'])
                        # Make response
                        await conn.fetch(query)
                        response = {
                            'status':'success'
                        }
                else:
                    response = {
                        'status':'fail',
                        'message':'The message does not exist'
                    }
        except Exception as e:
            print(e)
            response = {
                'status':'error',
                'message':'Database error'
                }
        return response


    async def user_action(request, token, data):
        try: 
            async with request.app['db'].acquire() as conn:
                # First: Get all need id 
                chat_id = await PostgreSQL.get_chat_id(conn, data['chat'])
                owner_id = await PostgreSQL.get_user_id(conn, token=token)
                user_id = await PostgreSQL.get_user_id(conn, login=data['user'])
                if user_id is None:
                    response = {
                        'status':'fail',
                        'message':'The user does not exist'
                    }
                    return response
                # Second: Check is token user is the owner of the chat
                query = db.chats.select().where((db.chats.c.id == chat_id) & (db.chats.c.owner_id == owner_id))
                result = await conn.fetch(query)
                if len(result) > 0:
                    # Check does user exist in the chat
                    query = db.members.select().\
                        where((db.members.c.user_id == user_id) & (db.members.c.chat_id == chat_id ))
                    result = await conn.fetch(query)
                    # If Action is invite user
                    if data['action'] == 'invite':
                        if len(result) > 0: # The user has already existed 
                            response = {
                                'status':'fail',
                                'message':'The user has already existed'
                            }
                        else: # The user does not exist
                            query = db.members.insert().\
                                values(
                                    chat_id = chat_id,
                                    user_id = user_id,
                                    permit = bool(data['permit'])) # CHANGE IT
                            await conn.fetch(query)
                            response = {'status':'succes'}
                    # If action is kick user
                    elif data['action'] == 'kick':
                        if len(result) > 0: # The user exists
                            query = db.members.delete().\
                                where((db.members.c.user_id == user_id) & (db.members.c.chat_id == chat_id ))
                            await conn.fetch(query)
                            response = {'status':'success'}
                        else:
                            response = {
                                'status':'fail',
                                'message':'The user does not exist'
                            }
                    elif data['action'] == 'permit':
                        if len(result) > 0: # The user exists
                            query = db.members.update().\
                                where(db.members.c.user_id == user_id).values(permit=data['permit'])
                            await conn.fetch(query)
                            response = {'status': 'success'}
                        else:
                            response = {
                                'status':'fail',
                                'message':'The user does not exist'
                            }

                else:
                    response = {
                        'status':'fail',
                        'message':'You\'re not an owner of the chat'
                    }
        except Exception as e:
            print("Exception i found: ",e)
            response = {
                'status':'error',
                'message':'Database error',
            }
        return response

    async def chat_actions(request, token, data):
        response = {'status': 'fail'}
        try: 
            async with request.app['db'].acquire() as conn:
                # First: Get all need id
                owner_id = await PostgreSQL.get_user_id(conn, token=token)
                query = db.chats.select().where(db.chats.c.name == data['chat'].lower())
                result = await conn.fetch(query)

                if data['action'] == 'create':
                    if len(result) > 0:
                        response['message'] = 'The chat has already existed'
                    else: 
                        query = db.chats.insert().\
                            values(
                                name = data['chat'].lower(),
                                isOpen = data['status'],
                                owner_id = owner_id,
                            )
                        await conn.fetch(query)
                        response = {'status': 'success'}
                elif result[0]['owner_id'] != owner_id: 
                    response = {'status': 'fail', 'message':'You are not an owner of the chat'}
                elif data['action'] == 'update':
                    if len(result) == 0: # If chat does not exist
                        response['message'] = 'The chat does not exist'
                    else:
                        query = db.chats.update().\
                            where(db.chats.c.name == data['chat'].lower()).\
                                values(
                                    name = data['name'],
                                    isOpen = data['status'],    
                                )
                        await conn.fetch(query)
                        response = {'status':'success'}

                elif data['action'] == 'destroy':
                    if len(result) == 0:
                        response['message'] = 'The chat does not exist'
                    else:
                        query = db.chats.delete().\
                            where(db.chats.c.name == data['chat'].lower())
                        await conn.fetch(query)
                        response = {
                            'status': 'success',
                            'message':'The chat was destroyed'
                        }

        except Exception as e:
            print("Was exception: ", e)
            response['message'] = 'The database error'

        return response