class CommandNotFound(Exception):
    def __init__(self, command_name):
        self.name = command_name

    def __str__(self):
        return f"Command with name {self.name} not found"


class ExtensionError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
