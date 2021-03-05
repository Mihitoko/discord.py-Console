# Discord.py-Console
Discord.py Console is a command line tool that allows you to control your bot and execute commands,  
so you can **use your Bot in the terminal/console** and run Discord commands as usual.


### Installation
----------

#### Windows
`py -3 -m pip install discord.py-Console`

#### Linux/macOS
`python3 -m pip install discord.py-Console`


### Usage and Example
----------

The implementation is similar to the regular commands in discord.py.
Just implement the discord.py-Console like this:

```python
import discord
from dpyConsole import Console

client = discord.Client(intents=discord.Intents.all())
my_console = Console(client)

@client.event
async def on_ready():
    print("I'm Ready")


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
To execute the mentioned command run ``hey exampleUser#0001`` or ``hey <valid_user_id>``.


### Links and Infos
----------

Note: You can split up discord.py-Console commands into cogs view an example in the Example folder.
- [PyPI Download](https://pypi.org/project/discord.py-Console)
