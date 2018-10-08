import logging

import pajbot.models
from pajbot.managers.adminlog import AdminLogManager
from pajbot.managers.db import DBManager
from pajbot.managers.handler import HandlerManager
from pajbot.modules import BaseModule

log = logging.getLogger(__name__)


class AutoresponseModule(BaseModule):

    ID = __name__.split('.')[-1]
    NAME = 'Autoresponse'
    DESCRIPTION = 'Looks at each message for specified triggers, and replies to them accordingly'
    ENABLED_DEFAULT = True
    CATEGORY = 'Filter'
    SETTINGS = []

    def is_message_bad(self, source, msg_raw, event):
        msg_lower = msg_raw.lower()

        res = self.bot.autoresponse_manager.check_message(msg_raw, source)
        if res is not False:
            self.bot.autoresponse_manager.reply(source, res)
            return True

        for f in self.bot.filters:
            if f.filter in msg_lower:
                log.debug('Matched autoresponse filter \'{0}\''.format(f.name))
                f.run(self.bot, source, msg_raw, event)
                return True

        return False  # message was ok

    def enable(self, bot):
        self.bot = bot
        HandlerManager.add_handler('on_message', self.on_message, priority=150)

    def disable(self, bot):
        HandlerManager.remove_handler('on_message', self.on_message)

    def on_message(self, source, message, emotes, whisper, urls, event):
        if self.is_message_bad(source, message, event):
            # we matched a filter.
            # return False so no more code is run for this message
            return False

    def add_autoresponse(self, **options):
        """Method for creating and editing autoresponses.
        Usage: !add autoresponse TRIGGER RESPONSE [options]
        Multiple options available:
        --whisper/--no-whisper
        """

        message = options['message']
        bot = options['bot']
        source = options['source']

        if message:
            options, phrase = bot.autoresponse_manager.parse_autoresponse_arguments(message)

            if options is False:
                bot.whisper(source.username, 'Invalid autoresponse')
                return False

            options['added_by'] = source.id
            options['edited_by'] = source.id

            autoresponse, new_autoresponse = bot.autoresponse_manager.create_autoresponse(phrase, **options)

            if new_autoresponse is True:
                bot.whisper(source.username, 'Added your autoresponse (ID: {autoresponse.id})'.format(autoresponse=autoresponse))
                AdminLogManager.post('Banphrase added', source, phrase)
                return True

            autoresponse.set(**options)
            autoresponse.data.set(edited_by=options['edited_by'])
            DBManager.session_add_expunge(autoresponse)
            bot.autoresponse_manager.commit()
            bot.whisper(source.username, 'Updated your autoresponse (ID: {autoresponse.id}) with ({what})'.format(autoresponse=autoresponse, what=', '.join([key for key in options if key != 'added_by'])))
            AdminLogManager.post('Banphrase edited', source, phrase)

    def remove_autoresponse(self, **options):
        message = options['message']
        bot = options['bot']
        source = options['source']

        if message:
            id = None
            try:
                id = int(message)
            except ValueError:
                pass

            autoresponse = bot.autoresponse_manager.find_match(message=message, id=id)

            if autoresponse is None:
                bot.whisper(source.username, 'No autoresponse with the given parameters found')
                return False

            AdminLogManager.post('Autoresponse removed', source, autoresponse.trigger, autoresponse.response)
            bot.whisper(source.username, 'Successfully removed autoresponse with id {0}'.format(autoresponse.id))
            bot.autoresponse_manager.remove_autoresponse(autoresponse)
        else:
            bot.whisper(source.username, 'Usage: !remove autoresponse (AUTORESPONSE_ID)')
            return False

    def load_commands(self, **options):
        self.commands['add'] = pajbot.models.command.Command.multiaction_command(
                level=100,
                delay_all=0,
                delay_user=0,
                default=None,
                command='add',
                commands={
                    'autoresponse': pajbot.models.command.Command.raw_command(self.add_autoresponse,
                        level=500,
                        description='Add a autoresponse!',
                        delay_all=0,
                        delay_user=0,
                        examples=[
                            pajbot.models.command.CommandExample(None, 'Create a autoresponse',
                                chat='user:!add autoresponse testman123 yikes\n'
                                'bot>user:Inserted your autoresponse (ID: 83)',
                                description='This creates a autoresponse with the default settings. Whenever a user types testman123 in chat the bot will tag them and say \'yikes\'').parse(),
                            pajbot.models.command.CommandExample(None, 'Make it so a response is sent through whisper',
                                chat='user:!add autoresponse testman123 yikes --whisper\n'
                                'bot>user:Updated the given autoresponse (ID: 83) with (whisper)',
                                description='Changes a command so that the response would only be sent through a whisper.').parse(),
                            ]),
                        }
                )

        self.commands['remove'] = pajbot.models.command.Command.multiaction_command(
                level=100,
                delay_all=0,
                delay_user=0,
                default=None,
                command='remove',
                commands={
                    'autoresponse': pajbot.models.command.Command.raw_command(self.remove_autoresponse,
                        level=500,
                        delay_all=0,
                        delay_user=0,
                        description='Remove a autoresponse!',
                        examples=[
                            pajbot.models.command.CommandExample(None, 'Remove a autoresponse',
                                chat='user:!remove autoresponse KeepoKeepo\n'
                                'bot>user:Successfully removed autoresponse with id 33',
                                description='Removes a autoresponse with the trigger KeepoKeepo.').parse(),
                            pajbot.models.command.CommandExample(None, 'Remove a autoresponse with the given ID.',
                                chat='user:!remove autoresponse 25\n'
                                'bot>user:Successfully removed autoresponse with id 25',
                                description='Removes a autoresponse with id 25').parse(),
                            ]),
                    }
                )
