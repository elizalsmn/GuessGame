# Guess the Truth 

This project demonstrates a simple client-server application where clients can join "rooms" to play a guessing game. The game showcases the use of sockets and threading in Python for network-based applications. Clients authenticate with the server, join rooms, and guess the outcome of a randomized Boolean value. This project is intended as an example for implementing network applications using sockets and threading in Python.

## Setup

### Server Setup

1. Start the server by running:
   ```bash
   python3 GameServer.py <server_port> <Path_for_UserInfo.txt> 
   ```
   - Replace <server_port> with the desired port number for the server.
   - Replace <Path_for_UserInfo.txt> with the path to a text file containing user information in the format:
    ```
    username1:password1
    username2:password2
    ```
2. The server will continue running until manually terminated. It can handle multiple client connections simultaneously.

### Client Setup

1. Start a client by running:
   ```bash
   python3 GameClient.py <server_address> <server_port>
   ```
   - Replace <server_address> with the IP address or hostname of the server (use localhost if running locally).
   - Replace <server_port> with the same port number used to start the server.
2. Multiple clients can connect to the server, each in a separate terminal.

## Game Starts

### Client Authentication

1. After starting the client, you will be prompted to enter a username and password. These credentials should match entries in the server's user information file. (you can log in to multiple sessions under 1 user)

2. Authentication responses:
    - If the username and password are valid, you will receive the message:
    ```
    1001 Authentication successful
    ```
    - If authentication fails you can try again but you will receive:
    ```
    1002 Authentication failed
    ```
3. If authentication is successful, you will be connected and can start using game commands.


### Game Commands
1. /list: View available rooms and the number of players in each room.
2. /enter <room_number>: Join the specified room. If another player is already in the room, the game will start.
3. /guess <true/false>: Make your guess in an active game.
4. /exit: Exit the game.

### Game Rules
1. Players can join rooms. If two players are in a room, the game will begin.
2. Each player makes a guess of either true or false.
3. The server generates a random true or false value.
4. The server announces results:
    - If both guesses match the random value, it’s a tie.
    - If one guess matches and the other doesn’t, the matching player wins
    - If neither matches, it’s a tie.
5. After the game, both players are removed from the room, and the room is reset.

### Additional Information
1. Server Termination: The server runs indefinitely. To stop it, manually close the terminal or press CTRL+C.
2. Room Management: Rooms reset after each game. Players need to rejoin to start a new game.
3. Multiple Clients: Each client operates independently; however, only two players can be in a room at a time to initiate the game.
