import logging
import re
import requests
import datetime
import sys

import pajbot.models
from pajbot.managers.adminlog import AdminLogManager
from pajbot.managers.db import DBManager
from pajbot.models.banphrase import Banphrase
from pajbot.models.sock import SocketClientManager
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
    PARENT_MODULE = BasicCommandsModule

    def nuke_command(self, **options):
        message = options['message']
        bot = options['bot']
        source = options['source']

        self.actually_nuke(message, bot, source)

    def actually_nuke(self, message, bot, source):
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
            splitText = r.text.translate(non_bmp_map).splitlines()[-messages:][:-1]

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
            i = 1
            for timeoutUser in badUsers:
                bot.execute_delayed(0.25 * i, bot._timeout, (timeoutUser, duration, reason))
                i += 1

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

    def monkeypurge(self, **options):
        message = options['message']
        bot = options['bot']
        source = options['source']

        # bot.execute_delayed(0.5, self.actually_nuke, ('cmonBruh 14400', bot, source))
        # bot.execute_delayed(0.5, self.actually_nuke, ('TriHard 14400', bot, source))

        self.toggle_banphrases()

        bot.execute_delayed(30, self.toggle_banphrases, ())

    def toggle_banphrases(self):
        with DBManager.create_session_scope() as db_session:
            row = db_session.query(Banphrase).filter_by(id=108).one_or_none()
            row2 = db_session.query(Banphrase).filter_by(id=113).one_or_none()

            row.enabled = True if not row.enabled else False
            row2.enabled = True if not row2.enabled else False

            db_session.commit()
            payload1 = {
                    'id': row.id,
                    'new_state': row.enabled,
                    }
            payload2 = {
                    'id': row2.id,
                    'new_state': row2.enabled,
                    }

            SocketClientManager.init('/tmp/.bullbot.sock')
            SocketClientManager.send('banphrase.update', payload1)
            SocketClientManager.send('banphrase.update', payload2)

    def load_commands(self, **options):
        self.commands['oldnuke'] = pajbot.models.command.Command.raw_command(self.nuke_command,
            level = 420,
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
        self.commands['tcpurge'] = pajbot.models.command.Command.raw_command(self.monkeypurge,
                level = 500,
                delay_all=0,
                delay_user=0,
                can_execute_with_whisper = True,
                description='Purge stuff when monkey is on screen'
                )
