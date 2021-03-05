# discord.py-Console

### Installation
##### Windows
`py -3 -m pip install discord.py-Console`

##### Linux
`python3 -m pip install discord.py-Console`

### Usage

This is a small Command line tool to execute commands from your console while your bot is running.

The implementation ist really similar to register commands in discord.py.
Just implement the Console like this:

```python
import discord
from dpyConsole import Console

client = discord.Client(intents=discord.Intents.all())
my_console = Console(client)

@client.event
async def on_ready():
    print("Im Ready")


@my_console.command()
async def hey(user: discord.User):  # Library automatically converts type annotations, just like in discord.py
    """
    Library can handle both synchronous or asynchronous functions
    """
    print(f"Sending message to {user.name} id: = {user.id}")
    await user.send(f"Hello from Console Im {client.user.name}")


my_console.start() # Starts console listener (opens new Thread to be nonblocking)
client.run("Token")
```
To invoke this command the line would be ``hey exampleUser#0001`` or ``hey <valid_user_id>``.

You can also add Cogs, to see an example look into the Example folder.
