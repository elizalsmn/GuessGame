#!/usr/bin/python3

import socket
import sys
import logging
import os.path
import time, traceback, threading, random

logging.basicConfig(level=logging.ERROR)
lock = threading.Lock()

user_list = {}
room_list = {}
active_user = {}

#authenticate the user
def handle_client(conn, addr):    
    while True:
        try:
            login = conn.recv(1024)
        except socket.error as err:
            print("Recv error: ", err)
            traceback.print_exc()
            conn.close()
            return
        
        try:
            if not login:
                print(f"Connection broken with {addr}")
                conn.close()
                return
            flag, user_name, user_password = login.decode('ascii').split()
            print(f"User {user_name} trying to login with password {user_password}")
            if flag == '/login' and user_list.get(user_name) == user_password:
                conn.send(b"1001 Authentication successful")
                active_user[addr[1]]=[conn, None]
                print("active users", active_user)
                break
            else:
                conn.send(b"1002 Authentication failed")
        except Exception as emsg:
            print(f"Error during login processing: {emsg}")
            traceback.print_exc()
            conn.close()
            return
    
    #checks the room condition
    def check_room(room):
        players = room_list[room]["players"]
        if len(players) == 2:
            return 2
        if len(players) == 1:
            return 1
        return 0
    
    def is_game_ready(room):
        return len(room_list[room]["players"])==2
    
    #reset the room from room list and the player's info in active_user
    def reset_room(room):
        lock.acquire()
        try:
            print('Starting room reset...')
            if room in room_list:
                players = room_list[room]["players"]

                for player_addr in list(players.keys()):
                    if player_addr in active_user:
                        active_user[player_addr][0].sendall(b"3024 The game has ended. The room is now reset.")
                        active_user[player_addr][-1] = None 

                # Delete the room from room_list
                del room_list[room]
                print(f"Room {room} has been reset and deleted.")
        finally:
            lock.release()

    # Game starts
    while True:
        try:
            rmsg = conn.recv(4096).decode('ascii')
            print(f'message received from {addr[1]} : {rmsg}')
            if not rmsg:
                break

            if rmsg=="/list":
                msg = "3001 "
                if room_list:
                    for room_id, room_info in room_list.items():
                        players = room_info["players"]
                        msg += f"Room {room_id} : {len(players)} "
                else :
                    msg += "no room created"
                conn.sendall(msg.encode('ascii'))

            elif rmsg.split()[0]=='/enter':
                if not rmsg.split()[-1].isdigit():
                    conn.sendall(b"4002 Unrecognized message")
                    continue 
                room = int(rmsg.split()[-1])  
                
                #check if the player is already in the room, each player can only join 1 room at the same time
                if active_user[addr[1]][-1] is not None:
                    current_room = active_user[addr[1]][-1]
                    conn.sendall(f"3016 You already joined room {current_room}".encode('ascii'))
                    continue

                if room not in room_list:
                    room_list[room] = {"players": {}, "result": None, "room_reset": False}  # Initialize the room with attributes

                players = room_list[room]["players"]

                #if room is full send 3013
                if check_room(room) == 2:
                    conn.send(b"3013 The room is full")  
                else:
                    lock.acquire()
                    try:
                        players[addr[1]] = None 
                        active_user[addr[1]][-1] = room 
                    finally:
                        lock.release()

                    print("Player added:", room_list)

                    #send either 3012 and 3011 based on the room condition
                    if check_room(room) == 2:
                        for player_addr, _ in players.items():
                            active_user[player_addr][0].send(b"3012 Game started. Please guess true or false")
                            print(f"Notified player {player_addr} to start the game")
                    elif check_room(room) == 1:
                        conn.send(b"3011 Wait")

            elif rmsg == '/exit':
                lock.acquire()
                try:
                    player_room = active_user[addr[1]][-1]

                    if player_room is not None and player_room in room_list:
                        players = room_list[player_room]["players"]
                        
                        remaining_player = None
                        if len(players) == 2:
                            remaining_player = next(p for p in players if p != addr[1])
                            if remaining_player in active_user:
                                active_user[remaining_player][0].sendall(b"3021 You are the winner, your opponent has left the game.")
                                active_user[remaining_player][-1] = None  # Reset the other player's room info

                        del room_list[player_room]
                        active_user[addr[1]][-1] = None  # Clear room info for the exiting player

                        #reset room
                        if not players:
                            del room_list[player_room]
                    
                    conn.sendall(b"4001 Bye bye")
                finally:
                    lock.release()
                
                conn.close()
                break

            elif rmsg.split()[0]=='/guess':
                room = active_user[addr[1]][-1]
                print(room_list[room])

                #check the room status, if still waiting will send 3015 msg
                if not is_game_ready(room):
                    conn.sendall(b"3015 The game is not ready. Please wait for another player.")
                    continue

                if room_list[room].get("room_reset", False):
                    print(f"Room {room} has already been reset. Exiting result processing for this thread.")
                    continue 

                lock.acquire()
                try:
                    guess_value = rmsg.split()[1].lower() == "true"
                    room_list[room]["players"][addr[1]] = guess_value
                    players = room_list[room]["players"]
                finally:
                    lock.release()
                    print("updated answer", room_list)

                # checking for the other player guess
                while not all(guess is not None for guess in players.values()):
                    time.sleep(1)

                if not room_list.get(room):
                    print(f"Room {room} has already been reset. Exiting result processing for this thread.")
                    continue

                # Determine the result for both players
                player_addresses = list(players.keys())
                if len(player_addresses) < 2:
                    print("Error: Not enough players in the room to determine the result.")
                    continue 

                player1_addr = player_addresses[0]
                player2_addr = player_addresses[1]
                player1_guess = players[player1_addr]
                player2_guess = players[player2_addr]

                # Randomize a boolean value to determine the result
                random_boolean = random.choice([True, False])
                print(f"Randomized value: {random_boolean}")

                # Retrieve the connection objects for both players
                player1_conn = active_user[player1_addr][0]
                player2_conn = active_user[player2_addr][0]

                # Send result to both players
                if player1_guess == random_boolean and player2_guess == random_boolean:
                    player1_conn.sendall(b"3023 The result is a tie")
                    player2_conn.sendall(b"3023 The result is a tie")
                elif player1_guess == random_boolean:
                    player1_conn.sendall(b"3021 You are the winner")
                    player2_conn.sendall(b"3022 You lost this game")
                elif player2_guess == random_boolean:
                    player1_conn.sendall(b"3022 You lost this game")
                    player2_conn.sendall(b"3021 You are the winner")
                else:
                    player1_conn.sendall(b"3023 The result is a tie")
                    player2_conn.sendall(b"3023 The result is a tie")

                lock.acquire()
                try:
                    room_list[room]["room_reset"] = True
                finally:
                    lock.release()
                reset_room(room)                    

            else:
                conn.sendall(b"4002 Unrecognized message")

        except Exception as e:
            print(f"Error handling client {addr}: {e}")
            traceback.print_exc()
            break


def main(argv):
    # get port number from argv
    port = int(argv[1])

    try:
        if not os.path.exists(argv[2]):
            raise FileNotFoundError(f"File not found: {argv[2]}")
        
        if not argv[2].endswith('.txt'):
            raise ValueError("The file is not a .txt file")
    
    except (FileNotFoundError, ValueError, os.error) as emsg:
        print(f"File error: {emsg}")
        traceback.print_exc()
        sys.exit(1)

    #read UserInfo.txt and save it
    try:
        with open(argv[2], 'r') as fd:
            lines = fd.readlines()
            for line in lines:
                username, password = line.strip().split(':')
                user_list[username] = password
    except Exception as emsg:
        print(f"Error: {emsg}")
        traceback.print_exc()
        sys.exit(1)

    if not user_list:
        print(f"Error: no users detected in {argv[2]}")
        sys.exit(1)
    print(user_list)
    
    sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd.bind(("", port))
    sockfd.listen(5)
    print("The server is ready to receive connections")

    while True:
        conn, addr = sockfd.accept()
        print(f"Accepted connection from {addr}")

        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

    sockfd.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 GameServer.py <Server_port> <Path_for_UserInfo.txt>")
        sys.exit(1)
    main(sys.argv)
