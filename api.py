""" Hey! The file includes all API methods
    You should start it witk '-i' key, example: 
                            python -i api.py """

import requests

TOKEN = None
URI = "http://192.168.1.104:5000"
URI = "http://localhost:8080"

def create_chat():
    chat_name = input("Enter chat name: ")
    status = input("You wanna create an open chat(y/any): ?")
    if status.lower() == 'y':
        status = True
    else: status = False
    r = requests.post(f'{URI}/api-{TOKEN}/chat', 
        json={
            'action': 'create',
            'chat': chat_name,
            'status': status,
    })
    return r


def destroy_chat():
    chat_name = input("Enter chat name: ")
    r = requests.post(f'{URI}/api-{TOKEN}/chat', 
        json={
            'action':'destroy',
            'chat':chat_name,
    })
    return r


def update_chat():
    chat_name = input("Enter chat name: ")
    new_name = input("Enter new chat name: ")
    status = input("Chat will be open or closed(y/any): ")
    if status.lower() == 'y':
        status = True
    else: status = False

    r = requests.post(f'{URI}/api-{TOKEN}/chat', 
        json={
            'action':'update',
            'chat':chat_name,
            'name': new_name, 
            'status': status,
    })
    return r


def send_message():
    chat_name = input("Enter chat name: ")
    message = input("Enter the text of the message: ")
    r = requests.post(f'{URI}/api-{TOKEN}/message', 
        json = {
            'action': 'send',
            'chat': chat_name,
            'message': message
        })
    return r


def delete_message():
    chat_name = input("Enter chat name: ")
    msg_id = int(input("Enter the message ID "))
    r = requests.post(f'{URI}/api-{TOKEN}/message', 
        json = {
            'action': 'delete',
            'chat': chat_name,
            'msg_id': msg_id
        })
    return r


def update_message():
    chat_name = input("Enter chat name: ")
    msg_id = int(input("Enter the message ID "))
    message = input("Enter the new text of the message: ")
    r = requests.post(f'{URI}/api-{TOKEN}/message', 
        json = {
            'action': 'update',
            'chat': chat_name,
            'msg_id': msg_id,
            'message': message,
        })
    return r


def invite_user():
    chat_name = input("Enter chat name: ")
    permit = bool(input("Do user have a permit: "))
    user = input("Enter user name")
    r = requests.post(f'{URI}/api-{TOKEN}/user', 
        json = {
            'action': 'invite',
            'chat': chat_name,
            'permit': permit,
            'user': user
        })
    return r


def kick_user():
    chat_name = input("Enter chat name: ")
    user = input("Enter user name")
    r = requests.post(f'{URI}/api-{TOKEN}/user', 
        json = {
            'action': 'kick',
            'chat': chat_name,
            'user': user
        })
    return r

def permit_user():
    chat_name = input("Enter chat name: ")
    permit = bool(input("Do user have a permit: "))
    user = input("Enter user name")
    r = requests.post(f'{URI}/api-{TOKEN}/user', 
        json = {
            'action': 'permit',
            'chat': chat_name,
            'permit': permit,
            'user': user
        })
    return r

if __name__ == "__main__":
    TOKEN = input('Enter your API-Token: ')
