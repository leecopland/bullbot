import logging
import re
import requests
import datetime
import sys

import pajbot.models
from pajbot.managers.adminlog import AdminLogManager
from pajbot.modules import BaseModule
from pajbot.modules import ModuleType
from pajbot.modules.basic import BasicCommandsModule

log = logging.getLogger(__name__)


class NukeModule(BaseModule):
    AUTHOR = 'DatGuy1'
    ID = __name__.split('.')[-1]
    NAME = 'Nuke'
    DESCRIPTION = 'Nuke specific phrase'
    CATEGORY = 'Feature'
    ENABLED_DEFAULT = True
    MODULE_TYPE = ModuleType.TYPE_ALWAYS_ENABLED
    PARENT_MODULE = BasicCommandsModule
    
    def nuke_command(self, **options):
        message = options['message']
        bot = options['bot']
        source = options['source']
        
        if message and len(message) > 0:
            message_split = []
            
            try:
                if message.startswith('\''):
                    filteredMessage = re.search(r'\'(.+?(?<!\\))\'(.*)', message)
                    message_split.append(filteredMessage.group(1))
                    message_split.extend(filteredMessage.group(2).strip().split(' '))
                else:
                    message_split = message.split(' ')
            except IndexError as e:
                bot.whisper(source.username, 'Error with syntax: {}.'.format(e))        

            if len(message_split) >= 1:
                phrase = message_split[0]
                if not message_split[1].isdigit():
                    bot.whisper(source.username, 'Duration must be numbers in seconds only.')
                    return
                duration = int(message_split[1])

                if len(message_split) == 3:
                    if message_split[2].isdigit():
                        messages = int(message_split[2])
                else:
                    messages = 200
            
            today = datetime.date.today()
            url = 'https://overrustlelogs.net/Admiralbulldog' \
                  ' chatlog/{:%B %Y}/{:%Y-%m-%d}.txt'.format(today, today)
            log.debug(url)
            
            r = requests.get(url)
            if r.status_code != 200:
                log.warning('Error with getting log')
                bot.whisper(source.username, 'Error with getting channel log. Contact DatGuy1 for help.')
                return

            non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
            splitText = r.text.translate(non_bmp_map).splitlines()[-messages:]

            badUsers = []
            
            for fullMessage in splitText:
                messageContent = re.findall(r'[^: ]*: (.*)', fullMessage)[0]
                if phrase.startswith('r/'):
                    try:
                        if re.search(phrase[2:], messageContent):
                            badUsers.append(re.findall(r'[^\]]*] ([^:]*)', fullMessage)[0])
                    except:
                        bot.whisper(source.username, 'Invalid regex')
                        return False
                else:
                    if phrase in messageContent:
                        badUsers.append(re.findall(r'[^\]]*] ([^:]*)', fullMessage)[0])

            badUsers = list(set(badUsers))

            reason = '{} nuked {} users for the phrase "{}" for {}'.format(source.username, len(badUsers),
                                                                           phrase, self.format_time(duration))

            for timeoutUser in badUsers:
                bot.execute_delayed(0.5, bot._timeout, (timeoutUser, duration, reason))

            AdminLogManager.add_entry('Users nuked', source, reason.replace(source.username, '').strip().capitalize())
            
        else:
            bot.whisper(source.username, 'You did not include enough arguments. Contact DatGuy1 for help.')

    def format_time(self, totalSeconds):
        res = ''
    
        seconds = int(totalSeconds % 60)
        timeoutMinutes = int(totalSeconds / 60)
        minutes = int(timeoutMinutes % 60)
        timeoutHours = int(timeoutMinutes / 60)
        hours = int(timeoutHours % 24)
        days = int(timeoutHours / 24)
        
        if days > 1:
            res += '{} days'.format(days)
        if hours > 1:
            if res:
                res += ', '
            res += '{} hours'.format(hours)
        if minutes > 1:
            if res:
                res += ', '
            res += '{} minutes'.format(minutes)
        if seconds > 0:
            if res:
                res += ', and '
            res += '{} seconds'.format(seconds)
        return res

    def load_commands(self, **options):
        self.commands['nuke'] = pajbot.models.command.Command.raw_command(self.nuke_command,
            level = 500,
            delay_all = 0,
            delay_user = 0,
            description='Nuke a specific string',
            examples=[
                pajbot.models.command.CommandExample(None,
                    'Nuke the last 30 messages that have \'TriHard\' in them for 1 minute',
                    chat='user:!nuke TriHard 60 30\n'
                    'bot:DatGuy1 nuked 3 users for the phrase "TriHard" in the last 30 messages for 1 minutes',
                    description='Nuke the last 30 messages that have \'TriHard\' in them for 1 minute').parse(),
                pajbot.models.command.CommandExample(None,
                    'Nuke the last 100 messages that have \'I like boats\' in them for 3 minutes',
                    chat='user:!nuke \'I like boats\' 180 100\n'
                    'bot:DatGuy1 nuked 5 users for the phrase "I like boats" in the last 100 messages for 3 minutes',
                    description='Nuke the last 100 messages that have \'I like boats\' in them for 3 minutes').parse(),
                pajbot.models.command.CommandExample(None,
                    'Nuke the last 100 messages that match the \'\bnam\' regex for 1 hour',
                    chat='user:!nuke r/\bnam 3600 100\n'
                    'bot:DatGuy1 nuked 5 users for the phrase "\bnam" in the last 100 messages for 1 hours',
                    description='Nuke the last 100 messages that match the \'\bnam\' regex for 1 hour').parse()
                ])
