#!/usr/bin/python3

import socket
import sys
import threading

start_game = False
stop_listening = False

def check_enter(game_input):
    if not game_input.startswith('/enter'):
        return False
    if len(game_input.split()) != 2:
        return False
    if game_input.split()[-1].isdigit() and int(game_input.split()[-1]) < 1:
        return False
    return True

def authenticate_user(sockfd):
    while True:
        user_name = input("Please input your user name: ")
        while not user_name or len(user_name.split()) > 1:
            print('The user name field is invalid')
            user_name = input("Please input your user name: ")

        password = input("Please input your password: ")
        while not password or len(password.split()) > 1:
            print('The password field is invalid')
            password = input("Please input your password: ")

        login_info = f'/login {user_name} {password}'
        sockfd.send(login_info.encode('ascii'))
        auth = sockfd.recv(1024).decode('ascii')
        print(auth)
        if auth == "1001 Authentication successful":
            break

def listen_for_server_messages(sockfd):
    global start_game, stop_listening
    while not stop_listening:
        try:
            response_input = sockfd.recv(4096).decode('ascii')
            if not response_input:
                print("Server connection lost. Exiting...")
                stop_listening = True
                break
            print(response_input)
            if response_input.startswith('4001'):
                print('Exiting game...')
                stop_listening=True
                break
            elif response_input.startswith('3012'):
                start_game = True
            elif response_input.startswith('3014'):
                print("Your opponent has left. Waiting for another opponent...")

        except (OSError, ConnectionResetError, ConnectionAbortedError):
            print("Connection to the server was lost")
            stop_listening = True
            break


def process_game_input(sockfd):
    global start_game, stop_listening
    while not stop_listening:
        game_input = input()
        if game_input.startswith('/guess') and not start_game:
            print('You are not in the game yet')
            continue
        sockfd.send(game_input.encode('ascii'))  
        if game_input.startswith('/exit'):
            break


def main(argv):
    try:
        sockfd = socket.socket()
        sockfd.connect((argv[1], int(argv[2])))
    except socket.error as emsg:
        print("Socket error: ", emsg)
        sys.exit(1)

    print("Connection established. My socket address is", sockfd.getsockname())
    authenticate_user(sockfd)

    listen_thread = threading.Thread(target=listen_for_server_messages, args=(sockfd,))
    listen_thread.daemon = True  
    listen_thread.start()
    process_game_input(sockfd)
    listen_thread.join()

    sockfd.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 GameClient.py <Server_addr> <Server_port>")
        sys.exit(1)
    main(sys.argv)
