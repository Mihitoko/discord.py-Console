from setuptools import setup

setup(
    name="discord.py-Console",
    version="0.1.2",
    description="Executes commands from console while your bot is running.",
    long_description=open("README.md").read(),
    url="https://github.com/Mihitoko/discord.py-Console",
    long_description_content_type="text/markdown",
    author="Mihito",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3.7"
    ],
    packages=["dpyConsole"],
    include_package_data=True,
    extras_require={
        "py-cord": ["py-cord"],
        "discord.py": ["discord.py"]
    }
)
