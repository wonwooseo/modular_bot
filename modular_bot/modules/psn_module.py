import logging
import discord
import requests
from bs4 import BeautifulSoup
from modular_bot.Module import BaseModule


class PSNModule(BaseModule):
    """
    Class for PSN Module. Gets user profile, recently played games,
    recently earned trophies from psnprofiles.com.
    """
    module_name = "PSN Module"
    module_description = "Fetches Playstation Network user profile, recently played games or recently earned " \
                         "trophies. All data referenced from psnprofiles.com."
    commands = ["psn_user", "psn_recent", "psn_trophies"]

    async def parse_command(self, bundle):
        """
        Decides which command should be executed and calls it.
        :param bundle Dictionary passed in from caller.
        :return: no return value.
        """
        client = bundle.get("client")
        message = bundle.get("message")
        if message.content.startswith(self.command_char + "psn_user"):
            await self.get_user_info(message)
        elif message.content.startswith(self.command_char + "psn_recent"):
            await self.get_recent_games(message)
        elif message.content.startswith(self.command_char + "psn_trophies"):
            await self.get_recent_trophies(message)

    async def get_user_info(self, message):
        """
        Gets PSN User info from my.playstation.com, make embed from it and
        sends back to server.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("psn_user requested by " + message.author.name + " on " + message.channel.name)
        search_arg = message.content[10:]
        if len(search_arg) == 0:
            await message.channel.send("No user name is provided!")
            return
        target_url = "https://psnprofiles.com/" + search_arg
        async with message.channel.typing():
            raw_page = requests.get(target_url)
            soup = BeautifulSoup(raw_page.text, "lxml")
            try:
                # get avatar image
                avatar_image_src = soup.find("div", {"class": "avatar"}).find('img')["src"]
                # find profile bar section
                profile_bar = soup.find("ul", {"class": "profile-bar"})
                user_name = profile_bar.find('span', {'class': 'username'}).text
                user_level = profile_bar.find("div", {"class": "trophy-count level"}).find('li').text
                # get numbers of each trophy
                plat_trophies = profile_bar.find("li", {"class": "platinum"}).text.strip()
                gold_trophies = profile_bar.find("li", {"class": "gold"}).text.strip()
                silver_trophies = profile_bar.find("li", {"class": "silver"}).text.strip()
                bronze_trophies = profile_bar.find("li", {"class": "bronze"}).text.strip()
                # create embed
                result_embed = discord.Embed(title=user_name, description="Level " + user_level)
                result_embed.set_thumbnail(url=avatar_image_src)
                result_embed.add_field(name="PLATINUM", value=plat_trophies)
                result_embed.add_field(name="GOLD", value=gold_trophies, inline=True)
                result_embed.add_field(name="SILVER", value=silver_trophies)
                result_embed.add_field(name="BRONZE", value=bronze_trophies, inline=True)
            except (AttributeError, TypeError):
                await message.channel.send("User not found or profile hasn't been updated yet.")
                return
            await message.channel.send(embed=result_embed)

    async def get_recent_games(self, message):
        """
        Gets recently plated games of user from web, make embed and send back to server.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("psn_recent requested by " + message.author.name + " on " + message.channel.name)
        search_arg = message.content[12:]
        if len(search_arg) == 0:
            await message.channel.send("No user name is provided!")
            return
        target_url = "https://psnprofiles.com/" + search_arg
        async with message.channel.typing():
            raw_page = requests.get(target_url)
            soup = BeautifulSoup(raw_page.text, "lxml")
            try:
                table = soup.find('table', {'id': 'gamesTable'})
                recent_games = table.findAll("tr")[:3]  # limit 3 most recent games
            except AttributeError:
                await message.channel.send("User not found or profile hasn't been updated yet.")
                return
            for game_soup in recent_games:
                game_title = game_soup.find('a', {'class': 'title'}).text
                game_platform = ', '.join([x.text for x in game_soup.findAll('span', {'class': 'platform'})])
                game_img_src = game_soup.find("picture").img["src"]
                # trophy progress and last played date
                info_list = game_soup.findAll('div', {'class': 'small-info'})
                progress = [x.text for x in info_list[0].findAll('b')]
                last_played = info_list[1].text.strip()
                # build embed
                result_embed = discord.Embed(title=game_title, description=game_platform)
                result_embed.set_thumbnail(url=game_img_src)
                result_embed.add_field(name="Trophies", value='{} of {} Trophies'.format(progress[0], progress[1]))
                result_embed.add_field(name="Last Played", value=last_played)
                await message.channel.send(embed=result_embed)

    async def get_recent_trophies(self, message):
        """
        Gets recently earned trophies of user from web, create embeds and sent them back to server.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("psn_trophies requested by " + message.author.name + " on " + message.channel.name)
        search_arg = message.content[14:]
        if len(search_arg) == 0:
            await message.channel.send("No user name is provided!")
            return
        target_url = "https://psnprofiles.com/" + search_arg + '/log'
        async with message.channel.typing():
            raw_page = requests.get(target_url)
            if not raw_page.url == target_url:  # page unreachable
                await message.channel.send("User not found or profile hasn't been updated yet.")
                return
            # page reached
            soup = BeautifulSoup(raw_page.text, "lxml")
            recent_trophies = soup.find("table").findAll("tr")[:3]  # limit last 3 trophies
            for trophy_soup in recent_trophies:
                game_title = trophy_soup.find('img', {'class': 'game'})['title']
                trophy_name = trophy_soup.find('a', {'class': 'title'}).text
                trophy_desc = trophy_soup.find('a', {'class': 'title'}).parent.br.next.strip()
                trophy_img_src = trophy_soup.find("img", {'class': 'trophy'})["src"]
                # list of spans (might be used for other info in future)
                spans = trophy_soup.findAll('span', {'class': 'separator left'})
                trophy_rarity = spans[-1].img['title']
                result_embed = discord.Embed(title=trophy_name, description=trophy_desc)
                result_embed.set_thumbnail(url=trophy_img_src)
                result_embed.set_author(name=game_title)
                result_embed.add_field(name="Rarity", value=trophy_rarity)
                await message.channel.send(embed=result_embed)
