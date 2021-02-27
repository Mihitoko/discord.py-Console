import discord
from dpyConsole import Console

client = discord.Client(intents=discord.Intents.all())
console = Console(client)
console.load_extension("console_cog")  # Loads extension (use doted path)


@client.event
async def on_ready():
    pass


@console.command()
async def hey(user: discord.User):  # Library automatically converts type annotations, just like in discord.py
    """
    Library can handle both synchronous or asynchronous functions
    """
    print(f"Sending message to {user.name} id: = {user.id}")
    await user.send("Hello from Console")


console.start()
client.run("NzAxMDQ5NjMxMzU3Nzk2NDAy.Xpr1WA.4lqMzYFU1OyBjhdhoJ6mqcjUF9g")
