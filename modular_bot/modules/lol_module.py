import logging
import requests
from bs4 import BeautifulSoup
import discord


class LOLEsportsModule:
    """
    Class for LOL e-sports Module. Gets player profile, top champions used, recent matches from best.gg.
    """
    module_name = "LOL e-sports Module"
    module_description = "Fetches profile, top champions used or recent official matches of professional League of" \
                         " Legends player. All data referenced from best.gg."
    commands = ["lol_player", "lol_topchamps", "lol_recent"]
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
        if message.content.startswith(self.command_char + "lol_player"):
            await self.get_player_info(client, message)
        elif message.content.startswith(self.command_char + "lol_topchamps"):
            await self.get_top_champs(client, message)
        elif message.content.startswith(self.command_char + "lol_recent"):
            await self.get_recent_match(client, message)

    async def get_player_info(self, client, message):
        """
        Gets profile of player, makes embed and returns to server as message. Fetches data from best.gg.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("lol_player requested by " + message.author.name + " on " + message.channel.name)
        search_arg = message.content[12:]
        if len(search_arg) == 0:
            await client.send_message(message.channel, "No user name is provided!")
            return
        target_url = "http://best.gg/player/" + search_arg
        await client.send_typing(message.channel)
        raw_page = requests.get(target_url, headers={"Accept-Language": "en-US"})
        soup = BeautifulSoup(raw_page.text, "lxml")
        try:
            # Parse html elements and get needed values
            img_src = "http:" + soup.find("img", {"class": "player__profile-face-img"})["src"]
            info_div = soup.find("div", {"class": "player__profile-info"})
            player_name = info_div.find("div", {"class": "player__profile-info-name"}).text
            player_team = info_div.find("div", {"class": "player__profile-info-team-team"}).text
            player_league = info_div.find("span", {"class": "player__profile-info-team-league"}).text
            player_position = info_div.find("div", {"class": "player__profile-info-team-position"}).text
            player_realname = info_div.find("span", {"class": "player__profile-info-full-name-name"}).text
            player_birth_div = info_div.find("div", {"class": "player__profile-info-birth"}).find("span")
            # Birth date is not always provided
            if player_birth_div is None:
                player_birth = " "
            else:
                player_birth = player_birth_div.text
            # Create embed to send back
            result_embed = discord.Embed(title=player_realname, description=player_birth)
            result_embed.set_author(name=player_name, url=target_url)
            result_embed.set_thumbnail(url=img_src)
            result_embed.add_field(name="TEAM", value=player_team, inline=True)
            result_embed.add_field(name="LEAGUE", value=player_league, inline=True)
            result_embed.add_field(name="POSITION", value=player_position, inline=True)
        except (AttributeError, TypeError):
            await client.send_message(message.channel, "Player not found.")
            return
        await client.send_message(message.channel, embed=result_embed)

    async def get_top_champs(self, client, message):
        """
        Gets top 5 champions used by player this year, makes embed and returns to server as message.
        Fetches data from best.gg.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("lol_topchamps requested by " + message.author.name + " on " + message.channel.name)
        search_arg = message.content[15:]
        if len(search_arg) == 0:
            await client.send_message(message.channel, "No user name is provided!")
            return
        target_url = "http://best.gg/player/" + search_arg
        await client.send_typing(message.channel)
        raw_page = requests.get(target_url, headers={"Accept-Language": "en-US"})
        soup = BeautifulSoup(raw_page.text, "lxml")
        try:
            # parse html elements and get needed values
            info_div = soup.find("div", {"class": "player__profile-info"})
            player_name = info_div.find("div", {"class": "player__profile-info-name"}).text
            result_embed = discord.Embed(title="Top 5 Champions Used")
            result_embed.set_author(name=player_name)
            champ_list = soup.findAll("li", {"class": "topChampions__item"})
            # Only show first 5 from list of li tags
            for champ in champ_list[:5]:
                champ_name = champ.find("div", {"class": "topChampions__item-champ-info-name"}).text
                champ_kda = champ.find("div", {"class": "topChampions__item-kda-count"}).text
                champ_winrate = champ.find("div", {"class": "topChampions__item-winRate-percent"}).text
                champ_played = champ.find("div", {"class": "topChampions__item-winRate-played"}).text
                result_embed.add_field(name=champ_name, value=champ_kda + " / " + champ_winrate + " / " + champ_played, inline=False)
        except (AttributeError, TypeError):
            await client.send_message(message.channel, "Player not found.")
            return
        await client.send_message(message.channel, embed=result_embed)

    async def get_recent_match(self, client, message):
        """
        Gets recent matches of player, makes embed and returns to server as message. Fetches data from best.gg.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("lol_recent requested by " + message.author.name + " on " + message.channel.name)
        search_arg = message.content[12:]
        if len(search_arg) == 0:
            await client.send_message(message.channel, "No user name is provided!")
            return
        target_url = "http://best.gg/player/" + search_arg
        await client.send_typing(message.channel)
        raw_page = requests.get(target_url, headers={"Accept-Language": "en-US"})
        soup = BeautifulSoup(raw_page.text, "lxml")
        try:
            matches = soup.findAll("div", {"class": "player__matches-item"})
            for match in matches:
                match_name = match.find("div", {"class": "player__matches-item-content-header-info-name"}).text
                match_date = match.find("div", {"class": "player__matches-item-content-header-info-date"}).text
                match_myteam = match.find("span", {"class": "player__matches-item-content-header-match-info-my-team"}).text
                match_enemy = match.find("span", {"class": "player__matches-item-content-header-match-info-opponent"}).find("span").text
                result_embed = discord.Embed(title=match_name, description=match_date)
                result_embed.set_author(name=match_myteam + " vs " + match_enemy)
                sets = match.find("ul", {"class": "player__matches-sets"}).findAll("li")
                for set_item in sets:
                    set_number = set_item.find("div", {"class": "player__matches-set-info-set"}).text
                    set_result = set_item.find("div", {"class": "player__matches-set-info-win"}).text
                    set_time = set_item.find("div", {"class": "player__matches-set-info-time"}).text
                    set_champ = set_item.find("div", {"class": "player__matches-set-champion-name"}).text
                    set_kda = set_item.find("div", {"class": "player__matches-set-kda-detail"}).text
                    result_embed.add_field(name=set_number, value=set_time + " / " + set_result, inline=True)
                    result_embed.add_field(name="Champion", value=set_champ, inline=True)
                    result_embed.add_field(name="KDA", value=set_kda, inline=True)
                await client.send_message(message.channel, embed=result_embed)
        except (AttributeError, TypeError):
            await client.send_message(message.channel, "Player not found.")
            return
