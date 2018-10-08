import logging

import pajbot.models
from pajbot.actions import ActionQueue
from pajbot.modules import BaseModule
from pajbot.modules import ModuleSetting

log = logging.getLogger('pajbot')

class ReportModule(BaseModule):
    AUTHOR = 'DatGuy1'
    ID = __name__.split('.')[-1]
    NAME = 'Report user'
    DESCRIPTION = 'Lets helpers report users'
    CATEGORY = 'Feature'
    SETTINGS = [
        ModuleSetting(
            key = 'receiver_list',
            label = 'List of users to receive a message (seperate by |)',
            type = 'text',
            required = True,
            default = ''),
        ModuleSetting(
            key = 'timeout_duration',
            label = 'Seconds of base timeout',
            type = 'number',
            required = True,
            placeholder = '',
            default = 600,
            constraints = {
                'min_value': 1,
                'max_value': 1209600
                })
        ]

    def report_command(self, **options):
        message = options['message']
        bot = options['bot']
        source = options['source']

        if message and len(message) > 0:
            message_split = message.split(' ')

            username = message_split[0].strip().lower()
            user = bot.users.find(username)

            if user is None and len(message_split) < 2:
                bot.whisper(source.username, 'You reported a user that isn\'t logged ' \
                            'in the viewer list without a reason. Please include one.')
                return False
            if user is not None:
                if user.banned:
                    bot.whisper(source.username, '{} is already permabanned.'.format(username))
                    return False

            sendMessage = '{} reported {}'.format(source.username, username)

            if len(message_split) > 1:
                sendMessage += ' with the reason: {}'.format(' '.join(
                                                             message_split[1:]))

            bot._timeout(username, self.settings['timeout_duration'], reason = 'User report')
            for receivee in self.settings['receiver_list'].split('|'):
                bot.whisper(receivee, sendMessage)

            bot.whisper(source.username, 'Successfully reported \'{}\''.format(username))
                

    def load_commands(self, **options):
        self.commands['report'] = pajbot.models.command.Command.raw_command(self.report_command,
            can_execute_with_whisper = True,
            level = 250,
            delay_all = 0,
            delay_user = 5,
            description = 'Report a user, which times them out for {} seconds'.format(
                self.settings['timeout_duration']),
            examples = [
                pajbot.models.command.CommandExample(None,
                    'Report user Darth_Henry',
                    chat = 'user:!report Darth_Henry\n'
                    'bot>user:Successfully reported \'Darth_Henry\'').parse(),
                pajbot.models.command.CommandExample(None,
                     'Report user Ji3Dan with the reason \'Racism\'',
                      chat = 'user:!report Ji3dan Racism\n'
                      'bot>user:Successfully reported \'Ji3dan\'').parse()
                ])
