import logging

from numpy import random

import pajbot.models
from pajbot.managers.redis import RedisManager
from pajbot.modules import BaseModule
from pajbot.modules import ModuleSetting

log = logging.getLogger(__name__)

class PlaySoundTokenCommandModule(BaseModule):
    ID = 'tokencommand-' + __name__.split('.')[-1]
    NAME = '!playsound'
    DESCRIPTION = 'Play a sound on stream'
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
                default=3,
                constraints={
                    'min_value': 0,
                    'max_value': 15,
                    }),
            ModuleSetting(
                key='sample_cd',
                label='Cooldown for the same sample (seconds)',
                type='number',
                required=True,
                placeholder='',
                default=20,
                constraints={
                    'min_value': 5,
                    'max_value': 120,
                    }),
            ModuleSetting(
                key='sub_only',
                label='Subscribers only',
                type='boolean',
                required=True,
                default=True),
            ModuleSetting(
                key='global_cd',
                label='Global playsound cooldown (seconds)',
                type='number',
                required=True,
                placeholder='',
                default=2,
                constraints={
                    'min_value': 0,
                    'max_value': 600,
                    }),
            ]

    def __init__(self):
        super().__init__()
        self.valid_samples = []
        self.sample_cache = []
        possibleCategories = ['bulldog', 'gachi', 'others', 'personalities', 'weeb']

        for category in possibleCategories:
            for sampleName, sampleURL in RedisManager.get().hgetall('playsounds:{}'.format(category)).items():
                self.valid_samples.append(sampleName)

    def refresh_sounds(self, **options):
        self.valid_samples = []
        possibleCategories = ['bulldog', 'gachi', 'others', 'personalities', 'weeb']

        for category in possibleCategories:
            for sampleName, sampleURL in RedisManager.get().hgetall('playsounds:{}'.format(category)).items():
                self.valid_samples.append(sampleName)

    def play_sound(self, **options):
        bot = options['bot']
        message = options['message']
        source = options['source']

        if message:
            sample = message.split(' ')[0].lower()

            if sample in self.sample_cache:
                bot.whisper(source.username, 'The sample {0} was played too recently. Please wait before trying to use it again'.format(sample))
                return False

            if sample == 'random':
                sample = random.choice(self.valid_samples)

            if sample in self.valid_samples:
                log.debug('Played sound: {0}'.format(sample))
                bot.whisper(source.username, 'Played sound: {}'.format(sample))
                payload = {'sample': sample}
                bot.websocket_manager.emit('play_sound', payload)
                if not (source.username.lower() == 'datguy1' or source.username.lower() == 'admiralbulldog') or True:
                    self.sample_cache.append(sample)
                    bot.execute_delayed(self.settings['sample_cd'], self.sample_cache.remove, ('{0}'.format(sample), ))
                return True

        bot.whisper(source.username, 'Your sample is not valid. Check out all the valid samples here: http://chatbot.admiralbulldog.live/playsound')
        return False

    def load_commands(self, **options):
        self.commands['playsound'] = pajbot.models.command.Command.raw_command(
                self.play_sound,
                cost=self.settings['point_cost'],
                sub_only=self.settings['sub_only'],
                delay_all=self.settings['global_cd'],
                description='Play a sound on stream! Costs {} points.'.format(self.settings['point_cost']),
                can_execute_with_whisper=True,
                examples=[
                    pajbot.models.command.CommandExample(None, 'Play the "cumming" sample',
                        chat='user:!playsound cumming\n'
                        'bot>user:Successfully played your sample cumming').parse(),
                    pajbot.models.command.CommandExample(None, 'Play the "fuckyou" sample',
                        chat='user:!playsound fuckyou\n'
                        'bot>user:Successfully played your sample fuckyou').parse(),
                    ],
                )

        self.commands['playsound'].long_description = 'Playsounds can be tried out <a href="http://chatbot.admiralbulldog.live/playsound">here</a>'
        self.commands['refreshsound'] = pajbot.models.command.Command.raw_command(
            self.refresh_sounds,
            level=500,
            can_execute_with_whisper=True)