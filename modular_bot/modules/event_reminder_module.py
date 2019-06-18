from datetime import datetime
import time
import logging
import asyncio
import _thread
from modular_bot.Module import BaseModule


class EventReminderModule(BaseModule):
    """
    Class for event reminder module. User can add event, see added events and remove added event by commands.
    Bot sends a reminder message that mentions everyone on server on time specified by user when adding event.
    """
    module_name = "Event Reminder Module"
    module_description = "Reminds everyone on server on time specified. Users can see and add/edit/remove events."
    commands = ["addevent", "listevent", "editevent", "removeevent"]
    # Module specific variables
    reminder_thread = False
    events_list = []  # use list to hold events; list will be sorted every time item is added

    async def parse_command(self, bundle):
        """
        Decides which command should be executed and calls it.
        :param bundle Dictionary passed in from caller.
        :return: no return value.
        """
        client = bundle.get("client")
        message = bundle.get("message")
        # Start reminder loop thread on first time when event reminder module is called
        if not self.reminder_thread:
            self.reminder_thread = True
            _thread.start_new_thread(self.reminder_loop, (client, message))
        # Decide which command to execute
        if message.content.startswith(self.command_char + "addevent"):
            await self.add_event(message)
        elif message.content.startswith(self.command_char + "listevent"):
            await self.list_event(message)
        elif message.content.startswith(self.command_char + "editevent"):
            await self.edit_event(message)
        elif message.content.startswith(self.command_char + "removeevent"):
            await self.remove_event(message)

    def reminder_loop(self, client, message):
        """
        Function to be executed in separate thread. This function polls time every 5 seconds, check events list and send
        reminder if current time is equal or larger than event time.
        :param client: discord.Client instance.
        :param message: discord.Message instance.
        :return: no return value.
        """
        target_channel = message.channel
        while True:
            if len(self.events_list) == 0:
                pass  # Do nothing if event list is empty
            elif datetime.now() >= self.events_list[0][1]:
                asyncio.run_coroutine_threadsafe(self.send_reminder(target_channel), client.loop)
            time.sleep(5)

    async def send_reminder(self, channel):
        """
        Coroutine to be called in separate thread to send reminder message.
        :param channel: discord.Channel instance.
        :return: no return value.
        """
        event_item = self.events_list.pop(0)
        logging.info("Sending reminder for event " + event_item[0] + " on channel " + channel.name)
        await channel.send("@everyone Reminder for event " + event_item[0])

    async def add_event(self, message):
        """
        Adds new event to event list. Command should be in format !addevent {event_name} {event_time}.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("Add Event requested by " + message.author.name + " on " + message.channel.name)
        args_list = message.content.split(" ", maxsplit=2)
        try:
            event_name = args_list[1]
            event_time = datetime.strptime(args_list[2], "%Y-%m-%d %H:%M")
        except IndexError:
            await message.channel.send("`Usage: !addevent {event_name} {event_time}`")
            return
        except ValueError:
            await message.channel.send("Time must be in `YYYY-mm-dd HH:MM` format.")
            return
        if event_time <= datetime.now():
            await message.channel.send("Event cannot happen earlier than current time.")
            return
        self.events_list.append((event_name, event_time))
        self.events_list = sorted(self.events_list, key=lambda x: x[1])  # sort events list by time in ascending order
        await message.channel.send("Event " + event_name + " on " + str(event_time)[:-3] + " added by " + message.author.name)

    async def list_event(self, message):
        """
        Lists all events currently stored in event list.
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("List Event requested by " + message.author.name + " on " + message.channel.name)
        if len(self.events_list) == 0:
            await message.channel.send("Event list is empty.")
            return
        list_index = 1
        result_text = "Current event list:\n"
        for event_item in self.events_list:
            result_text += "\t" + str(list_index) + ". " + event_item[0] + " on " + str(event_item[1])[:-3] + "\n"
            list_index += 1
        await message.channel.send(result_text)

    async def edit_event(self, message):
        """
        Edits event in event list. Uses index to identify event item.
        Command: !editevent {index} {new_name} {new time}
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("Edit Event requested by " + message.author.name + " on " + message.channel.name)
        if len(self.events_list) == 0:
            await message.channel.send("Event list is empty. Nothing to edit!")
            return
        args_list = message.content.split(" ", maxsplit=3)
        if len(args_list) != 4:
            await message.channel.send("`Usage: !editevent {index} {new_name} {new_time}`")
            return
        try:
            if args_list[1] == 0:  # assume user picked first item
                list_index = 1
            else:
                list_index = int(args_list[1]) - 1
            old_event_item = self.events_list[list_index]
        except ValueError:
            await message.channel.send("Invalid index. Use index from `!listevent` command.")
            return
        except IndexError:
            await message.channel.send("Index out of bounds. Check index using `!listevent` command.")
            return
        new_event_name = args_list[2]
        try:
            new_event_time = datetime.strptime(args_list[3], "%Y-%m-%d %H:%M")
            if new_event_time <= datetime.now():
                await message.channel.send("Event cannot happen earlier than current time.")
                return
        except ValueError:
            await message.channel.send("Time must be in `YYYY-mm-dd HH:MM` format.")
            return
        self.events_list[list_index] = (new_event_name, new_event_time)
        self.events_list = sorted(self.events_list, key=lambda x: x[1])
        result_text = "Discarded: Event " + old_event_item[0] + " on " + str(old_event_item[1])[:-3] + "\n"
        result_text += "Added: Event " + new_event_name + " on " + str(new_event_time)[:-3]
        await message.channel.send(result_text)

    async def remove_event(self, message):
        """
        Removes event in event list. Uses index to identify event item.
        Command: !removeevent {index}
        :param message: discord.Message instance.
        :return: no return value.
        """
        logging.info("Remove Event requested by " + message.author.name + " on " + message.channel.name)
        if len(self.events_list) == 0:
            await message.channel.send("Event list is empty. Nothing to remove!")
            return
        try:
            remove_index = int(message.content[13:])
            if remove_index == 0:  # assume user picked first item
                remove_index = 1
            removed_event = self.events_list.pop(remove_index - 1)
        except ValueError:
            await message.channel.send("`Usage: !removeevent {event_index}`\n"
                                       "You can check index of event using `!listevent` command.")
            return
        except IndexError:
            await message.channel.send("Index out of bounds. Use `!listevent` command to check index.")
            return
        await message.channel.send("Removed event " + removed_event[0] + " from event list.")
