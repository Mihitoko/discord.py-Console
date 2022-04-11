"""
dpy-Console
"""

try:
    import discord
except ImportError:
    RuntimeError("Cannot find discord namespace please use:\n"
                 "pip install discord.py-Console[discord.py] or pip install discord.py-Console[py-cord] "
                 "depending on what library you want to use or install it manually")

from dpyConsole.console import Console, Cog
from dpyConsole.converter import Converter
