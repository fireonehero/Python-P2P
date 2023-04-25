import socket
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

class Peer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.ip, self.port))

    def encrypt_message(self, message):
        fernet = Fernet(self.key)
        return fernet.encrypt(message.encode("utf-8"))

    def decrypt_message(self, message):
        fernet = Fernet(self.key)
        return fernet.decrypt(message).decode("utf-8")

    def listen_for_messages(self, connection, address):
        while True:
            try:
                encrypted_message = connection.recv(1024)
                if encrypted_message:
                    message = self.decrypt_message(encrypted_message)
                    sender = f"{address[0]}:{address[1]}"
                    if sender == f"{self.ip}:{self.port}":
                        print(f"Self: {message}")
                    else:
                        print(f"{sender} > {message}")
            except:
                connection.close()
                break


    def start_listening(self):
        self.server.listen()
        while True:
            connection, address = self.server.accept()
            print(f"Connected with {address[0]}:{address[1]}")
            thread = threading.Thread(target=self.listen_for_messages, args=(connection, address))
            thread.start()

    def send_message(self, ip, port, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            encrypted_message = self.encrypt_message(message)
            s.sendall(encrypted_message)

    def set_encryption_key(self, key):
        self.key = key
    
    def set_encryption_key(self, key=None):
        if key:
            try:
                Fernet(key)
                self.key = key
            except ValueError:
                print("Invalid key provided. Generating a new key.")
                self.key = Fernet.generate_key()
                print(f"New key: {self.key.decode('utf-8')}")
        else:
            self.key = Fernet.generate_key()
            print(f"Generated key: {self.key.decode('utf-8')}")
            

def login_or_create_account(session):
    accounts = {}

    password_session = PromptSession()
    password_style = Style.from_dict({'password': 'noinherit'})

    while True:
        action = session.prompt("Enter 'Login' or 'Create': ").lower()

        if action == "login":
            username = session.prompt("Enter your username: ")
            password = password_session.prompt("Enter your password: ",
                                               is_password=True,
                                               style=password_style)
            if username in accounts and accounts[username] == password:
                print("Login successful!")
                break
            else:
                print("Invalid username or password. Try again.")
        elif action == "create":
            username = session.prompt("Enter a new username: ")

            if username in accounts:
                print("Username already exists. Try again.")
            else:
                password = password_session.prompt("Enter a new password: ",
                                                   is_password=True,
                                                   style=password_style)
                accounts[username] = password
                print("Account created successfully!")
                break
        else:
            print("Invalid action. Try again.")



if __name__ == "__main__":
    my_ip = "127.0.0.1"
    my_port = 5555

    peer = Peer(my_ip, my_port)

    peer.set_encryption_key()

    listen_thread = threading.Thread(target=peer.start_listening)
    listen_thread.start()

    session = PromptSession()

    login_or_create_account(session)

    target_ip, target_port = None, None

    while True:
        try:
            if target_ip is None or target_port is None:
                input_parts = session.prompt("Enter target IP and port (separated by space): ").split()
                target_ip, target_port = input_parts[0], int(input_parts[1])

            message = session.prompt(f"Message to {target_ip}:{target_port} (Type 'Quit' to change IP/port or 'Exit' to quit): ")

            if message.lower() == "exit":
                break
            elif message.lower() == "quit":
                target_ip, target_port = None, None
            else:
                peer.send_message(target_ip, target_port, message)
        except KeyboardInterrupt:
            break