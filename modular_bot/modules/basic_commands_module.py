import discord
import time
import logging
import asyncio


class BasicCommands:
    """
    Class for basic commands module.
    """
    module_name = "Basic Commands"
    module_description = "Basic commands for testing purpose and shutdown."
    commands = ["echo", "sleep", "shutdown"]
    command_char = ''

    def __init__(self, user_cmd_char):
        """
        Sets command prefix while initializing.
        :param user_cmd_char: command prefix.
        """
        self.command_char = user_cmd_char

    def get_module_name(self):
        """
        Returns name of the module.
        :return: name of the module in string.
        """
        return self.module_name

    def get_module_description(self):
        """
        Returns description of the module.
        :return: description of the module in string.
        """
        return self.module_description

    def get_all_commands(self):
        """
        Returns all commands of the module.
        :return: commands of the module in string list.
        """
        return self.commands

    async def parse_command(self, bundle):
        """
        Decides which command should be executed and calls it.
        :param bundle Dictionary passed in from caller.
        :return: no return value.
        """
        client = bundle.get("client")
        message = bundle.get("message")
        if message.content.startswith(self.command_char + "echo"):
            await self.echo(client, message)
        elif message.content.startswith(self.command_char + "sleep"):
            await self.sleep(client, message)
        elif message.content.startswith(self.command_char + "shutdown"):
            await self.shutdown(client, message)

    async def echo(self, client, message):
        """
        Echoes given message(excluding command term).
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("Echo requested by " + message.author.name + " on " + message.channel.name)
        return_text = message.content[6:]
        if len(return_text) == 0:
            return_text = "`null`"
        await client.send_message(message.channel, return_text)

    async def sleep(self, client, message):
        """
        Sleeps for 5 seconds. Any commands initiated during sleep will executed after sleep finishes.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("Sleep requested by " + message.author.name + " on " + message.channel.name)
        await client.send_message(message.channel, "Sleeping...")
        time.sleep(5)
        await client.send_message(message.channel, "Slept 5 seconds!")

    async def shutdown(self, client, message):
        """
        Shuts down the bot.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("Shutdown requested by " + message.author.name + " on " + message.channel.name)
        await client.send_message(message.channel, ":wave:")
        await client.logout()
        logging.info("Logged out and closed connection.")