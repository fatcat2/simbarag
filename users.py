import sqlite3


class User:
    def __init__(self, email: str, password_hash: str):
        self.email = email
        self.is_authenticated


if __name__ == "__main__":
    connection = sqlite3.connect("users.db")
    c = connection.cursor()
