import logging
import discord
import requests
from bs4 import BeautifulSoup


class PSNModule:
    """
    Class for PSN Module. Gets user profile, recently played games, recently earned trophies from my.playstation.com.
    """
    module_name = "PSN Module"
    module_description = "Fetches Playstation Network user profile, recently played games or recently " \
                         "earned trophies. All data referenced from my.playstation.com."
    commands = ["psn_user", "psn_recent", "psn_trophies"]
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
        if message.content.startswith(self.command_char + "psn_user"):
            await self.get_user_info(client, message)
        elif message.content.startswith(self.command_char + "psn_recent"):
            await self.get_recent_games(client, message)
        elif message.content.startswith(self.command_char + "psn_trophies"):
            await self.get_recent_trophies(client, message)

    async def get_user_info(self, client, message):
        """
        Gets PSN User info from my.playstation.com, make embed from it and sends back to server.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("psn_user requested by " + message.author.name + " on " + message.channel.name)
        search_arg = message.content[10:]
        if len(search_arg) == 0:
            await client.send_message(message.channel, "No user name is provided!")
            return
        target_url = "https://my.playstation.com/" + search_arg
        await client.send_typing(message.channel)
        raw_page = requests.get(target_url)
        soup = BeautifulSoup(raw_page.text, "lxml")
        try:
            avatar_image_src = "http:" + soup.find("img", {"class": "avatar"})["src"]
            user_info_div = soup.find("div", {"class": "user-info"})
            user_name = user_info_div.find("h2").text
            user_last_trophy = user_info_div.find("h3").text
            user_level = soup.find("div", {"class": "quantity content level-num"}).text
            user_trophies = soup.find("div", {"class": "quantity content trophy-num"}).text
            result_embed = discord.Embed(title=user_name, description=user_last_trophy)
            result_embed.set_thumbnail(url=avatar_image_src)
            result_embed.add_field(name="LEVEL", value=user_level, inline=True)
            result_embed.add_field(name="TROPHIES", value=user_trophies, inline=True)
        except (AttributeError, TypeError):
            await client.send_message(message.channel, "User not found or profile set to private.")
            return
        await client.send_message(message.channel, embed=result_embed)

    async def get_recent_games(self, client, message):
        """
        Gets recently plated games of user from web, make embed and send back to server.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("psn_recent requested by " + message.author.name + " on " + message.channel.name)
        search_arg = message.content[12:]
        if len(search_arg) == 0:
            await client.send_message(message.channel, "No user name is provided!")
            return
        target_url = "https://my.playstation.com/" + search_arg
        await client.send_typing(message.channel)
        raw_page = requests.get(target_url)
        soup = BeautifulSoup(raw_page.text, "lxml")
        try:
            recent_games = soup.find("ul", {"class": "tile-grid-trophies"}).findAll("li", {"class": "tile"})
        except AttributeError:
            await client.send_message(message.channel, "User not found.")
            return
        for game_soup in recent_games:
            game_title = game_soup.find("h2").text
            game_platform = game_soup.find("span").text
            game_img_src = "http:" + game_soup.find("img")["src"]
            trophy_bronze = game_soup.find("li", {"class": "bronze"}).text
            trophy_silver = game_soup.find("li", {"class": "silver"}).text
            trophy_gold = game_soup.find("li", {"class": "gold"}).text
            trophy_platinum = game_soup.find("li", {"class": "platinum"}).text
            result_embed = discord.Embed(title=game_title, description=game_platform)
            result_embed.set_thumbnail(url=game_img_src)
            result_embed.add_field(name="BRONZE", value=trophy_bronze, inline=True)
            result_embed.add_field(name="SILVER", value=trophy_silver, inline=True)
            result_embed.add_field(name="GOLD", value=trophy_gold, inline=True)
            result_embed.add_field(name="PLATINUM", value=trophy_platinum, inline=True)
            await client.send_message(message.channel, embed=result_embed)

    async def get_recent_trophies(self, client, message):
        """
        Gets recently earned trophies of user from web, create embeds and sent them back to server.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("psn_trophies requested by " + message.author.name + " on " + message.channel.name)
        search_arg = message.content[14:]
        if len(search_arg) == 0:
            await client.send_message(message.channel, "No user name is provided!")
            return
        target_url = "https://my.playstation.com/" + search_arg
        await client.send_typing(message.channel)
        raw_page = requests.get(target_url)
        soup = BeautifulSoup(raw_page.text, "lxml")
        try:
            recent_trophies = soup.find("ul", {"class": "tile-grid-trophies clearfix"}).findAll("li", {"class": "tile"})
        except AttributeError:
            await client.send_message(message.channel, "User not found.")
            return
        for trophy_soup in recent_trophies:
            game_title = trophy_soup.find("h1").text
            trophy_img_src = "http:" + trophy_soup.find("img")["src"]
            trophy_name = trophy_soup.find("div", {"class": "trophy_name"}).text
            trophy_rarity = trophy_soup.find("div", {"class": "trophy_name"})["class"][1].upper()
            trophy_desc = trophy_soup.find("h2").text
            result_embed = discord.Embed(title=trophy_name, description=trophy_desc)
            result_embed.set_thumbnail(url=trophy_img_src)
            result_embed.set_author(name=game_title)
            result_embed.add_field(name="Rarity", value=trophy_rarity)
            await client.send_message(message.channel, embed=result_embed)
