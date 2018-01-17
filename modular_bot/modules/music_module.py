import discord
import logging
import asyncio
import queue
import os


class MusicModule:
    """
    Class for music module. Music module supports streaming audio from youtube url or local files. User can switch
    between each player instance anytime, but all queue or playlist index data will be lost during switching.
    """
    module_name = "Music Module"
    module_description = "Streams audio from Youtube URLs or local mp3 files. Users can add musics if playing on" \
                         " Youtube player, but local file player has a fixed playlist(order by filename). Users can" \
                         " skip, pause or change volume while playing."
    commands = ["play", "play_local", "stop", "pause", "resume", "skip", "volume", "music", "musicoff"]
    command_char = ''
    function_dict = {}
    voice_channel = ""
    voice_client = None
    current_player = None
    song_queue = queue.Queue(0)
    local_song_list = []
    local_song_index = 0
    player_switch = False
    is_playing = False
    is_local = False
    default_volume = 0.15

    def __init__(self, user_cmd_char):
        """
        Sets command prefix while initializing.
        :param user_cmd_char: command prefix.
        """
        self.command_char = user_cmd_char
        self.initialize_function_dict()

    def initialize_function_dict(self):
        """
        Initializes dictionary for functions. Result of refactoring if-elif statements.
        :return: No return value.
        """
        self.function_dict[self.command_char + "play"] = self.play
        self.function_dict[self.command_char + "play_local"] = self.play_local
        self.function_dict[self.command_char + "stop"] = self.stop
        self.function_dict[self.command_char + "pause"] = self.pause
        self.function_dict[self.command_char + "resume"] = self.resume
        self.function_dict[self.command_char + "skip"] = self.skip
        self.function_dict[self.command_char + "volume"] = self.volume
        self.function_dict[self.command_char + "music"] = self.music
        self.function_dict[self.command_char + "musicoff"] = self.musicoff

    def clear_attributes(self):
        """
        Clears all data holding attributes of class on end of connection.
        :return: No return value.
        """
        self.song_queue = queue.Queue(0)
        self.local_song_list = []
        self.local_song_index = 0
        self.player_switch = False
        self.is_playing = False
        self.is_local = False

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

    def end_song(self, client, message):
        """
        Function to be executed after youtube player stops.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        if not self.player_switch:
            self.current_player = None
            return
        logging.info("Playing next song in queue")
        if self.song_queue.qsize() == 0:
            logging.info("Queue is empty; stopping player")
            self.is_playing = False
            asyncio.run_coroutine_threadsafe(self.end_song_queue_empty(client), client.loop)
            return
        # Setup new player in different thread
        asyncio.run_coroutine_threadsafe(self.end_song_await_ytdl_player(client, message), client.loop)

    async def end_song_queue_empty(self, client):
        """
        Empties now playing status if queue exhausts.
        :param client: discord.Client instance.
        :return: No return value.
        """
        await client.change_presence(game=None)

    async def end_song_await_ytdl_player(self, client, message):
        """
        Sets up new youtube player instance and sends now playing message.
        Wrapped in asyncio to be included in non-async function.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        target_song = self.song_queue.get()
        self.current_player = await self.voice_client.create_ytdl_player(target_song,
                                                                         after=lambda: self.end_song(client, message))
        self.current_player.volume = self.default_volume
        self.current_player.start()
        await client.change_presence(game=discord.Game(name=self.current_player.title))
        await client.send_message(message.channel, "Now Playing " + self.current_player.title)

    def end_song_local(self, client, message):
        """
        Function to be executed after local music player stops.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        if not self.player_switch:
            self.current_player = None
            return
        if len(self.local_song_list) == 0:
            return
        logging.info("Playing next song in playlist")
        local_music_path = os.getcwd() + "/music_cache"
        self.local_song_index += 1
        if self.local_song_index == len(self.local_song_list):
            self.local_song_index = 0
        self.current_player = self.voice_client.create_ffmpeg_player(local_music_path + "/" +
                                                                     self.local_song_list[self.local_song_index],
                                                                     after=lambda: self.end_song_local(client, message))
        self.current_player.volume = self.default_volume
        # Send message must be awaited; run in different thread
        asyncio.run_coroutine_threadsafe(self.end_song_local_await_send_message(client, message), client.loop)
        self.current_player.start()

    async def end_song_local_await_send_message(self, client, message):
        """
        Sends now playing message; wrapped by asyncio to be included in non-async function.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        song_name = self.local_song_list[self.local_song_index]
        song_name = song_name[:len(song_name) - 4]
        await client.change_presence(game=discord.Game(name=song_name))
        await client.send_message(message.channel, "Now Playing " + song_name)

    async def parse_command(self, bundle):
        """
        Decides which command should be executed and calls it.
        :param bundle Dictionary passed in from caller.
        :return: no return value.
        """
        client = bundle.get("client")
        message = bundle.get("message")
        self.voice_channel = bundle.get("vchannel")
        await self.function_dict[message.content.split(" ")[0]](client, message)

    async def music(self, client, message):
        """
        Turns on the music player and connects client to voice channel.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        logging.info("music requested by " + message.author.name + " on " + message.channel.name)
        if self.player_switch:
            await client.send_message(message.channel, "Music player is already on.")
            return
        self.voice_client = await client.join_voice_channel(client.get_channel(self.voice_channel))
        self.player_switch = True
        await client.send_message(message.channel, ":musical_note: Turning on music player!")

    async def musicoff(self, client, message):
        """
        Turns off music player and disconnects from voice channel. All data holding attributes are cleared.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        logging.info("musicoff requested by " + message.author.name + " on " + message.channel.name)
        if not self.player_switch:
            await client.send_message(message.channel, "Music player is already off.")
            return
        self.clear_attributes()
        try:
            self.current_player.stop()
        except AttributeError:
            logging.info("Player already stopped; continuing")
        await self.voice_client.disconnect()
        self.voice_client = None
        await client.send_message(message.channel, "Turning off music player!")

    async def stop(self, client, message):
        """
        Stops current player instance. Player must be stopped first to switch between youtube player or local
        file player.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        logging.info("stop requested by " + message.author.name + " on " + message.channel.name)
        if not self.player_switch:
            await client.send_message(message.channel, "Player is offline. Turn on player first by !music command.")
            return
        self.clear_attributes()
        self.current_player.stop()
        await client.send_message(message.channel, "Player stopped.")
        await client.change_presence(game=None)
        self.player_switch = True

    async def play(self, client, message):
        """
        Streams audio to voice channel from youtube video of given url. If youtube player is already playing, adds
        url to song queue. If local player is playing or self.current_player is None, plays video from url right away.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        logging.info("play requested by " + message.author.name + " on " + message.channel.name)
        if not self.player_switch:
            await client.send_message(message.channel, "Player is offline. Turn on player first by !music command.")
            return
        if self.is_local:
            await client.send_message(message.channel, "Local file player is already online. Use !stop to stop it first and try again.")
            return
        self.is_local = False
        url = message.content[6:]
        self.song_queue.put(url)
        if not self.is_playing:
            target_song = self.song_queue.get()
            self.current_player = await self.voice_client.create_ytdl_player(target_song,
                                                                             after=lambda: self.end_song(client, message))
            self.current_player.volume = self.default_volume
            await client.change_presence(game=discord.Game(name=self.current_player.title))
            await client.send_message(message.channel, "Now Playing " + self.current_player.title)
            self.current_player.start()
            self.player_switch = True  # Turn on player again
            self.is_playing = True
        else:
            await client.send_message(message.channel, "Added item to queue (Current queue size: " + str(self.song_queue.qsize()) + ")")

    async def play_local(self, client, message):
        """
        Streams audio to voice channel from local music files in /music_cache. If local player is already playing, do
        nothing. If youtube player is playing or self.current_player is None, play local files right away.
        self.play_local loads all mp3 files in /music_cache and adds them to playlist.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        if not self.player_switch:
            await client.send_message(message.channel, "Player is offline. Turn on player first by !music command.")
            return
        logging.info("play_local requested by " + message.author.name + " on " + message.channel.name)
        if self.is_local:
            await client.send_message(message.channel, ":x: I'm already playing local music.")
            return
        else:
            if self.is_playing:
                await client.send_message(message.channel, "Youtube player is already online. Use !stop to stop it first and try again.")
                return
        self.is_local = True
        local_music_path = os.getcwd() + "/music_cache"
        try:
            file_list = os.listdir(local_music_path)
        except FileNotFoundError:
            logging.warning("music_cache folder in bot's working directory is not found.")
            await client.send_message(message.channel, "`Error: Directory not found`")
            return
        for file in file_list:
            if file.endswith(".mp3"):
                self.local_song_list.append(file)
        logging.info("Added " + str(len(self.local_song_list)) + " songs to playlist")
        if len(self.local_song_list) == 0:
            await client.send_message(message.channel, "music_cache is empty.")
            return
        song_name = self.local_song_list[self.local_song_index]
        self.current_player = self.voice_client.create_ffmpeg_player(local_music_path + "/" + song_name,
                                                                     after=lambda: self.end_song_local(client, message))
        self.current_player.volume = self.default_volume
        song_name = song_name[:len(song_name) - 4]
        await client.change_presence(game=discord.Game(name=song_name))
        await client.send_message(message.channel, "Now Playing " + song_name)
        self.current_player.start()
        self.player_switch = True  # Turn player back on
        self.is_playing = True

    async def skip(self, client, message):
        """
        Skips current song.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        logging.info("skip requested by " + message.author.name + " on " + message.channel.name)
        if not await self.check_player_status(client, message):
            return
        self.current_player.stop()  # after parameter of player is called

    async def pause(self, client, message):
        """
        Pauses current song.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        logging.info("pause requested by " + message.author.name + " on " + message.channel.name)
        if not await self.check_player_status(client, message):
            return
        self.current_player.pause()
        await client.send_message(message.channel, ":pause_button:")

    async def resume(self, client, message):
        """
        Resumes current song.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        logging.info("resume requested by " + message.author.name + " on " + message.channel.name)
        if not await self.check_player_status(client, message):
            return
        self.current_player.resume()
        await client.send_message(message.channel, ":arrow_forward:")

    async def volume(self, client, message):
        """
        Sets volume of current player. If no argument is given, displays current volume of player.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: No return value.
        """
        logging.info("volume requested by " + message.author.name + " on " + message.channel.name)
        if not await self.check_player_status(client, message):
            return
        volume_args = message.content.split(" ")
        if len(volume_args) == 1:  # no argument is given for command
            await client.send_message(message.channel, "Current volume: " + str(self.current_player.volume * 100) + "%")
            return
        try:
            volume_arg = int(volume_args[1])
            if volume_arg > 100 or volume_arg < 0:
                await client.send_message(message.channel, "Invalid argument; volume must be `integer` between 0 and 100.")
                return
            else:
                volume_arg = volume_arg / 100.0
        except ValueError:
            await client.send_message(message.channel, "Invalid argument; volume must be `integer` between 0 and 100.")
            return
        self.current_player.volume = volume_arg
        await client.send_message(message.channel, "Set volume to " + str(self.current_player.volume * 100) + "%")

    async def check_player_status(self, client, message):
        """
        Helper function to check current status of player.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: False if player is offline or no song is being played. True otherwise.
        """
        if not self.player_switch:
            await client.send_message(message.channel, "Player is offline. Turn on player first by !music command.")
            return False
        if not self.is_playing:
            await client.send_message(message.channel, "Player is stopped. First start playing by !play or !play_local command.")
            return False
        return True
