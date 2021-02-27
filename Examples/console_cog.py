from dpyConsole import Cog
from dpyConsole import console
import discord


class ConsoleCog(Cog):
    def __init__(self, console):
        super(ConsoleCog, self).__init__()
        self.console = console

    @console.command()
    async def cog_test(self, user: discord.User):
        await user.send("Hello from Console \n"
                        f"This command operates in a Cog and my name is {self.console.client.user.name}")


def setup(console):
    """
    Loads Cog
    This function must be present.
    As you can see the implementation is just like in discord.py
    :param console:
    :return:
    """
    console.add_console_cog(ConsoleCog(console))
