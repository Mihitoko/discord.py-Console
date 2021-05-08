import importlib
import sys
from inspect import iscoroutinefunction
import asyncio
from dpyConsole.converter import Converter
import inspect
import logging
import traceback
import shlex
from dpyConsole.errors import CommandNotFound


logger = logging.getLogger("dpyConsole")


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
        # noinspection PyUnresolvedReferences
        module.setup(self)

    def listen(self):
        """
        Console starts listening for inputs.
        This is a blocking call. To avoid the bot being stopped this has to run in an executor (New Thread)
        :return:
        """
        logger.info("Console is ready and is listening for commands\n")
        while True:
            try:
                console_in = shlex.split(self.input.readline())
                try:
                    command = self.__commands__.get(console_in[0], None)

                    if not command:
                        raise CommandNotFound(console_in[0])

                    if len(command.__subcommands__) == 0:
                        self.prepare(command, console_in[1:])
                    else:
                        try:
                            sub_command = command.__subcommands__.get(console_in[1], None)
                        except IndexError:
                            sub_command = None
                        if not sub_command:
                            self.prepare(command, console_in[1:])
                            continue
                        self.prepare(sub_command, console_in[2:])

                except (IndexError, KeyError):
                    traceback.print_exc()
            except Exception:
                traceback.print_exc()

    def prepare(self, command, args):
        args_ = args.copy()
        logger.info(f"Invoking command {command.name} with args {args}")
        if getattr(command, "cog", None):
            args_.insert(0, command.cog)
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
                try:
                    new_param = converter_(args_[count])
                except IndexError:
                    continue
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
