import logging

import pajbot.models
from pajbot.modules import BaseModule
from pajbot.modules import ModuleSetting

log = logging.getLogger(__name__)


class ShowEmoteTokenCommandModule(BaseModule):

    ID = 'tokencommand-' + __name__.split('.')[-1]
    NAME = 'Show emote'
    DESCRIPTION = 'Show a single emote on screen for a few seconds'
    SETTINGS = [
            ModuleSetting(
                key='point_cost',
                label='Point cost',
                type='number',
                required=True,
                placeholder='Point cost',
                default=0,
                constraints={
                    'min_value': 0,
                    'max_value': 999999,
                    }),
                ModuleSetting(
                    key='token_cost',
                    label='Token cost',
                    type='number',
                    required=True,
                    placeholder='Token cost',
                    default=1,
                    constraints={
                        'min_value': 0,
                        'max_value': 15,
                        }),
            ModuleSetting(
                key='blacklisted_emotes',
                label='Blacklisted emotes',
                type='text',
                required=False,
                placeholder='TriHard NaM'
                )]

    def show_emote(self, **options):
        bot = options['bot']
        source = options['source']
        args = options['args']

        if len(args['emotes']) == 0:
            # No emotes in the given message
            bot.whisper(source.username, 'No valid emotes were found in your message.')
            return False

        first_emote = args['emotes'][0]
     
        for badEmote in self.settings['blacklisted_emotes'].split(' '):
            if badEmote == first_emote['code']:
                bot.whisper(source.username, 'The emote you tried to show is blacklisted. Your points haven\'t been deducted.')
                return False

        payload = {'emote': first_emote}
        bot.websocket_manager.emit('new_emote', payload)
        bot.whisper(source.username, 'Successfully sent the emote {} to the stream!'.format(first_emote['code']))

    def load_commands(self, **options):
        self.commands['showemote'] = pajbot.models.command.Command.raw_command(
                self.show_emote,
                cost=self.settings['point_cost'],
                description='Show an emote on stream! Costs 1 token.',
                can_execute_with_whisper=True,
                examples=[
                    pajbot.models.command.CommandExample(None, 'Show an emote on stream.',
                        chat='user:!#showemote Keepo\n'
                        'bot>user: Successfully sent the emote Keepo to the stream!',
                        description='').parse(),
                    ])
