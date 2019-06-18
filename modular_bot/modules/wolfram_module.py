import logging
import requests
import discord
import io


class WolframModule:
    """
    Class for Wolfram Module. Queries WolframAlpha and returns simple text answer or detailed image answer.
    """
    module_name = "Wolfram Module"
    module_description = "Queries user's question to WolframAlpha. User can select to receive answer in simple" \
                         " text-only form or detailed image-based form."
    commands = ["wolfram", "wolfram_detail"]
    command_char = ''
    app_id = "75GQ8R-VJ8AX4VT75"

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
        if message.content.split(" ", maxsplit=1)[0] == self.command_char + "wolfram":
            await self.wolfram_result(message)
        elif message.content.split(" ", maxsplit=1)[0] == self.command_char + "wolfram_detail":
            await self.wolfram_simple(message)

    async def wolfram_result(self, message):
        """
        Queries WolframAlpha and returns short text-only answer to server.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("wolfram requested by " + message.author.name + " on " + message.channel.name)
        query = message.content[9:]
        if len(query) == 0:
            await message.channel.send("Ask me something!")
            return
        url = "http://api.wolframalpha.com/v1/result?appid=" + self.app_id + "&i=" + query
        async with message.channel.typing():
            response = requests.get(url)
            if response.status_code == 501:
                await message.channel.send("I can't understand your question.")
                return
            answer = response.text  # Response from api is a simple text; no other conversion required
            await message.channel.send(answer)

    async def wolfram_simple(self, message):
        """
        Queries WolframAlpha and returns simple image result to server.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("wolfram_detail requested by " + message.author.name + " on " + message.channel.name)
        query = message.content[16:]
        if len(query) == 0:
            await message.channel.send("Ask me something!")
            return
        url = "http://api.wolframalpha.com/v1/simple?appid=" + self.app_id + "&i=" + query
        async with message.channel.typing():
            response = requests.get(url)  # Now contains binary for image
            if response.status_code == 501:
                await message.channel.send("I can't understand your question.")
                return
            answer = io.BytesIO(response.content)  # Convert bytes object to file-like object
            await message.channel.send(file=discord.File(answer, filename="answer.png"))
