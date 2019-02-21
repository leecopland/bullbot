import logging
import re
import requests

import pajbot.models
from pajbot.modules import BaseModule
from pajbot.modules import ModuleSetting


log = logging.getLogger(__name__)


class QuoteModule(BaseModule):

    ID = __name__.split('.')[-1]
    NAME = 'Random quote'
    DESCRIPTION = 'Some recent/random message stuff'
    CATEGORY = 'Feature'

    def __init__(self):
        self.baseURL = 'https://api.gempir.com/channel/admiralbulldog/user'

    def random_quote(self, **options):
        bot = options['bot']
        source = options['source']
        message = options['message']

        if message is None or len(message) == 0:
            # The user did not supply any arguments
            return False

        msg_split = message.split(' ')
        if len(msg_split) < 1:
            # The user did not supply enough arguments
            bot.whisper(source.username, 'Usage: !rq USERNAME')
            return False

        username = msg_split[0].lower()
        if len(username) < 2:
            # The username specified was too short. ;-)
            return False

        with bot.users.find_context(username) as target:
            r = requests.get("{}/{}/random".format(self.baseURL, username))

            if target is None:
                bot.say('This user does not exist FailFish')
                return False

            if r.status_code != 200 or not r.text:
                bot.say('Error with fetching website: {}'.format(r.status_code))
                return False

            bot.say('{}: {}'.format(username, r.text))

    def last_quote(self, **options):
        bot = options['bot']
        source = options['source']
        message = options['message']

        if message is None or len(message) == 0:
            # The user did not supply any arguments
            return False

        msg_split = message.split(' ')
        if len(msg_split) < 1:
            # The user did not supply enough arguments
            bot.whisper(source.username, 'Usage: !lq USERNAME')
            return False

        username = msg_split[0].lower()
        if len(username) < 2:
            # The username specified was too short. ;-)
            return False

        with bot.users.find_context(username) as target:
            r = requests.get("{}/{}".format(self.baseURL, username))

            if target is None:
                bot.say('This user does not exist FailFish')
                return False

            if r.status_code != 200 or not r.text:
                bot.say('Error with fetching website: {}'.format(r.status_code))
                return False

            recentMsg = r.text.splitlines()[-1]


            bot.say(re.search(r'ldog (.*)', recentMsg).group(1))

    def load_commands(self, **options):
        self.commands['rq'] = pajbot.models.command.Command.raw_command(
                self.random_quote,
                delay_all=2,
                delay_user=5
        )
        self.commands['randomquote'] = self.commands['rq']
        self.commands['lastquote'] = pajbot.models.command.Command.raw_command(
                self.last_quote,
                delay_all=2,
                delay_user=5
        )
        self.commands['lq'] = self.commands['lastquote']
        self.commands['lastmessage'] = self.commands['lastquote']
