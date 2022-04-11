import importlib
import sys
from inspect import iscoroutinefunction
import asyncio
from dpyConsole.converter import Converter
import inspect
import logging
import traceback
import shlex
import threading

from dpyConsole.errors import CommandNotFound, ExtensionError

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
        self.__extensions = {}
        self.__cogs = {}

    def add_console_cog(self, obj):
        if isinstance(obj, Cog):
            self.__cogs.update({obj.__class__.__name__: obj})
            obj.load(self)
            return
        raise Exception

    def remove_console_cog(self, name):
        cog = self.__cogs.pop(name, None)
        cog.unload(self)

    def load_extension(self, path):
        """
        Loads an extension just like in discord.py
        :param path:
        :return:
        """
        if path in self.__extensions:
            raise ExtensionError(f"Extension {path} already loaded")
        module = importlib.import_module(path)
        # noinspection PyUnresolvedReferences
        module.setup(self)
        self.__extensions.update({path: module})

    def unload_extension(self, path):
        """
        Unloads an extension
        :param path:
        :return:
        """
        module = self.__extensions.get(path, None)
        if module is None: # raise if ext is not loaded
            raise ExtensionError(f"This extension is not loaded ({path})")
        for name, cog in self.__cogs.copy().items():
            if _is_submodule(module.__name__, cog.__module__):
                self.remove_console_cog(name)

        sys.modules.pop(module.__name__, None)  # Remove "cached" module

    def reload_extension(self, path):
        module = self.__extensions.get(path, None)
        sys.modules.pop(module.__name__, None)
        if module is None:
            raise ExtensionError(f"This extension is not loaded ({path})")
        old_modules = {}
        cached = []
        """
        Store old module state to fallback if exception occurs
        """
        for name, mod in sys.modules.items():
            if _is_submodule(mod.__name__, path):
                cached.append(mod)
        old_modules.update({path: cached})

        try:
            self.unload_extension(path)
            self.load_extension(path)
        except:
            #  Rollback
            module.setup(self)
            self.__extensions[path] = module
            sys.modules.update(old_modules)
            raise

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
                if len(console_in) == 0:
                    continue
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

    def remove_command(self, command):
        self.__commands__.pop(command.name, None)

    def start(self):
        """
        Abstracts Thread initialization away from user.
        :return:
        """
        thread = threading.Thread(None, self.listen, daemon=True)
        thread.start()


def _is_submodule(parent, child):
    return parent == child or child.startswith(parent + ".")


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
        commands = []
        # noinspection PyUnresolvedReferences
        for base in reversed(cls.__mro__):
            for elem, value in base.__dict__.items():
                if isinstance(value, Command):
                    commands.append(value)
        cls.commands = commands
        return super().__new__(cls)

    def load(self, console: Console):
        """
        Gets called everytime when the Cog gets loaded from console
        :param console:
        :return:
        """
        for cmd in self.__class__.commands:
            cmd.cog = self
            for c in cmd.__subcommands__.values():
                c.cog = self
            console.add_command(cmd)

    def unload(self, console: Console):
        """
        Gets called when unloaded from console.
        Cleans up all commands
        :param console:
        :return:
        """
        for cmd in self.__class__.commands:
            console.remove_command(cmd)
