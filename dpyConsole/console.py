import importlib
import sys
from inspect import iscoroutinefunction
import asyncio
from dpyConsole.converter import Converter
import inspect


class Console:
    """
    Handles console input and Command invocations.
    It also holds the converter in
    """
    def __init__(self, client, **kwargs):
        self.client = client
        self.input = kwargs.get("input", sys.stdin)
        self.out = kwargs.get("out", sys.stdout)
        self.__commands__ = dict()
        self.converter = kwargs.get("converter", Converter(client))

    def add_console_cog(self, obj):
        if isinstance(obj, Cog):
            self.__commands__.update(obj.commands)

    def load_extension(self, path):
        """
        Loads an extension just like in discord.py
        :param path:
        :return:
        """
        module = importlib.import_module(path)
        module.setup(self)

    def listen(self):
        """
        Console starts listening for inputs.
        This is a blocking call. To avoid the bot being stopped this has to run in an executor (New Thread)
        :return:
        """
        self.out.write("[INFO] Console is ready and is listening for commands\n")
        while True:
            try:
                console_in = self.input.readline().replace("\n", "").split(" ")
                try:
                    command = self.__commands__[console_in[0]]
                    if len(command.__subcommands__) == 0:
                        self.prepare(command, console_in[1:])
                    else:
                        try:
                            sub_command = command.__subcommands__[console_in[1]]
                        except (KeyError, IndexError):
                            self.prepare(command, console_in[1:])
                        else:
                            self.prepare(sub_command, console_in[2:])

                except (IndexError, KeyError) as e:
                    print(e)
            except Exception as e:
                print(e)

    def prepare(self, command, args):
        args_ = args.copy()
        if getattr(command, "cog", None):
            args_.insert(0, command.cog)

        converted_args = command.convert(self.converter, args_)
        if iscoroutinefunction(command.__callback__):
            command.invoke(converted_args, loop=self.client.loop)
        else:
            command.invoke(converted_args)

    def command(self, **kwargs):
        cls = Command

        def decorator(func):
            name = kwargs.get("name", func.__name__)
            command = cls(name, func)
            self.add_command(command)
            return command

        return decorator

    def add_command(self, command):
        self.__commands__.update(
            {
                command.name: command
            }
        )

    def start(self, loop=None):
        """
        Abstracts the executor initialization away from you.
        Takes an asyncio Eventloop as param.
        :param loop:
        :return:
        """
        loop = self.client.loop if not loop else loop
        loop.run_in_executor(None, self.listen)


class Command:
    """
    The class every command uses
    """

    def __init__(self, name, callback, parent=None):
        self.name = name
        self.__callback__: type = callback
        self.__subcommands__ = dict()
        self.parent = parent

    def subcommand(self, **kwargs):
        """
        Decorator to add subcommands
        :param kwargs:
        :return:
        """
        cls = Command

        def decorator(func):
            name = kwargs.get("name", func.__name__)
            subcommand = cls(name, func, self)
            self.add_sub_command(subcommand)
            return subcommand

        return decorator

    def add_sub_command(self, command):
        """
        Adds a subcommand to an existing command
        :param command:
        :return:
        """
        self.__subcommands__.update(
            {command.name: command}
        )

    def invoke(self, args, loop: asyncio.AbstractEventLoop = None):
        """
        Invokes command callback.
        :param args:
        :param loop:
        :return:
        """
        if loop:
            asyncio.run_coroutine_threadsafe(self.__callback__(*args), loop=loop)
        else:
            self.__callback__(*args)

    def convert(self, converter: Converter, args: list):
        """
        Convertes the parameters before invoke
        :param converter:
        :param args:
        :return:
        """
        args_ = args.copy()
        signature = inspect.signature(self.__callback__)
        count = 0
        for key, value in signature.parameters.items():
            if value.annotation != inspect.Parameter.empty:
                converter_ = converter.get_converter(value.annotation)
                new_param = converter_(args_[count])
                args_[count] = new_param
                count += 1
            else:
                count += 1
        return args_


def command(**kwargs):
    """
    Decorator to register a command
    :param kwargs:
    :return:
    """
    cls = Command

    def decorator(func):
        name = kwargs.get("name", func.__name__)
        return cls(name, func)

    return decorator


class Cog:
    def __new__(cls, *args, **kwargs):
        commands = {}
        # noinspection PyUnresolvedReferences
        for base in reversed(cls.__mro__):
            for elem, value in base.__dict__.items():
                if isinstance(value, Command):
                    commands.update({value.name: value})
        cls.commands = commands
        return super().__new__(cls)

    def __init__(self):
        for command in self.commands.values():  # updates the cog attribute for  all commands
            for c in command.__subcommands__.values():
                c.cog = self
            command.cog = self
