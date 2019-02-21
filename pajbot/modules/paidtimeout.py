import datetime
import logging
import math

import pajbot.models
from pajbot.managers.handler import HandlerManager
from pajbot.modules import BaseModule
from pajbot.modules import ModuleSetting

log = logging.getLogger(__name__)


class PaidTimeoutModule(BaseModule):

    ID = __name__.split('.')[-1]
    NAME = 'Paid Timeout'
    DESCRIPTION = 'Allows user to time out other users with points'
    CATEGORY = 'Feature'
    SETTINGS = [
            ModuleSetting(
                key = 'command_names',
                label = 'Command name (i.e. $timeout)',
                type = 'text',
                required = True,
                placeholder = 'Command name (no !)',
                default = 'timeout'),
            ModuleSetting(
                key = 'timeout_lengths',
                label = 'Timeout length',
                type = 'text',
                required = True,
                placeholder = 'Timeout length in seconds',
                ),
            ModuleSetting(
                key = 'costs',
                label = 'Point cost',
                type = 'text',
                required = True,
                placeholder = 'Point cost'),
            ModuleSetting(
                key = 'bypass_level',
                label = 'Level to bypass module (people with this level or above are immune to paid timeouts)',
                type = 'number',
                required = True,
                placeholder = '',
                default = 500,
                constraints = {
                    'min_value': 100,
                    'max_value': 1000,
                    }),
            ModuleSetting(
                key = 'show_on_clr',
                label = 'Show timeouts on the clr overlay',
                type = 'boolean',
                required = True,
                default = True),
            ]

    def base_paid_timeout(self, bot, source, target, _time, _cost):
        with bot.users.find_context(target) as victim:
            if victim is None:
                bot.whisper(source.username,
                            'This user does not exist FailFish')
                return False

            if victim.last_active is None or (datetime.datetime.now() - victim._last_active).total_seconds() > 10 * 60:
                bot.whisper(
                    source.username, 'This user has not been active in chat within the last 10 minutes.')
                return False

            if victim == source:
                bot.whisper(source.username,
                            'You can\'t timeout yourself FailFish')
                return False

            if victim.moderator is True:
                bot.whisper(
                    source.username, 'This person has mod privileges, timeouting this person is not worth it.')
                return False

            if victim.level >= self.settings['bypass_level']:
                bot.whisper(
                    source.username, 'This person\'s user level is too high, you can\'t timeout this person.')
                return False

            now = datetime.datetime.now()

            if victim.timed_out and victim.timeout_end > now:
                bot.whisper(source.username, '{} is already timed out.'.format(victim.username))
                return False

            """if victim.timed_out is True and victim.timeout_end > now:
                victim.timeout_end += datetime.timedelta(seconds = _time)
                bot.whisper(victim.username, '{victim.username}, you were timed out for an additional {time} seconds by {source.username}'.format(
                    victim = victim,
                    source = source,
                    time = _time))
                bot.whisper(source.username, 'You just used {0} points to time out {1} for an additional {2} seconds.'.format(
                    _cost, victim.username, _time))
                num_seconds = int((victim.timeout_end - now).total_seconds())
                bot._timeout(victim.username, num_seconds,
                             reason = 'Timed out by {}'.format(source.username_raw))
            # songs = session.query(PleblistSong, func.count(PleblistSong.song_info).label('total')).group_by(PleblistSong.youtube_id).order_by('total DESC')
            else:"""

            if source.subscriber and not victim.subscriber:
                _cost = int(_cost * 0.8)

            if not source.can_afford(_cost):
                bot.whisper(source.username, 'You can only timeout people when you can afford it with your own, heard-earned points. You\'re missing {} for this stage'.format(source.points - _cost))
                return False

            source.points -= _cost

            bot.whisper(source.username, 'You just used {0} points to time out {1} for {2} seconds.'.format(
                _cost, victim.username, _time))
            bot.whisper(victim.username, '{0} just timed you out for {1} seconds.'.format(
                source.username, _time))
            bot._timeout(victim.username, _time,
                         reason = 'Timed out by {} for {} points! See !paidtimeout'.format(source.username_raw, _cost))
            bot.say('{} timed out {} with paidtimeout for {} seconds!'.format(source.username_raw, victim.username, _time))
            victim.timed_out = True
            victim.timeout_start = now
            victim.timeout_end = now + datetime.timedelta(seconds = _time)

            if self.settings['show_on_clr']:
                payload = {'user': source.username, 'victim': victim.username}
                bot.websocket_manager.emit('timeout', payload)

            HandlerManager.trigger('on_paid_timeout',
                    source, victim, _cost,
                    stop_on_false = False)

    def paid_timeout(self, **options):
        message = options['message']
        bot = options['bot']
        source = options['source']
        num = 0

        if message is None or len(message) < 2:
            bot.whisper(source.username, 'Incorrect usage. See !help')
            return False

        target = message.split(' ')[0]
        if len(target) < 2:
            bot.whisper(source.username, 'Incorrect usage. See !help')
            return False

        durationSpec = message.split(' ')[1]
        if durationSpec not in self.settings['command_names'].split():
            bot.whisper(source.username, 'Incorrect usage. See !help')
            return False

        _time = int(self.settings['timeout_lengths'].split()[int(durationSpec) - 1])
        _cost =  int(self.settings['costs'].split()[int(durationSpec) - 1])

        return self.base_paid_timeout(bot, source, target, _time, _cost)


    def load_commands(self, **options):
        self.commands['paidtimeout'] = pajbot.models.command.Command.raw_command(
            self.paid_timeout,
            can_execute_with_whisper = False
            )
