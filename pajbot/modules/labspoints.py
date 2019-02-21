import logging
import threading

import pajbot.models
from pajbot.modules import BaseModule
from pajbot.modules import ModuleSetting
from socketIO_client_nexus import SocketIO

log = logging.getLogger(__name__)

class asyncSocketIo():
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

        try:
            self.receive_events_thread._stop
        except Exception as e:
            pass

        self.socketio = SocketIO('https://sockets.streamlabs.com', params = {
                                 'token': settings['socket_token']})
        self.socketio.on('event', self.on_event)
        self.socketio.on('disconnect', self.on_disconnect)

        self.receive_events_thread = threading.Thread(target=self._receive_events_thread)
        self.receive_events_thread.daemon = True
        self.receive_events_thread.start()

    def on_event(self, *args):
        DonationPointsModule.updatePoints(args, self.bot, self.settings)

    def on_disconnect(self, *args):
        log.error('Socket disconnected. Donations no longer monitored')
        self.bot.say('Socket disconnected. Donations no longer monitored')
        self.bot.execute_delayed(600, self.__init__, (self.bot, self.settings))

    def _receive_events_thread(self):
        self.socketio.wait()


class DonationPointsModule(BaseModule):
    ID = __name__.split('.')[-1]
    NAME = 'Donate for points'
    DESCRIPTION = 'Users can donate to receive points.'
    ENABLED_DEFAULT = True
    CATEGORY = 'Feature'
    SETTINGS = [
            ModuleSetting(
                key='socket_token',
                label='Socket token',
                type='text',
                required=True),

            ModuleSetting(
                key='multiplynum',
                label='How much of the donation to multiply by',
                type='number',
                required=True),

                ]

    def enable(self, bot):
        self.bot = bot
        asyncSocketIo(self.bot, self.settings)

    def updatePoints(args, bot, settings):
        if args[0]['type'] != 'donation':
            return False

        if 'historical' in args[0]['message'][0]:
            return False

        donation_name = args[0]['message'][0]['name']

        user = bot.users.find(donation_name)
        if user is None:
            return False

        finalValue = int(float(args[0]['message'][0]['amount']) * int(settings['multiplynum']))

        user.points += finalValue
        user.save()

        bot.whisper(user.username, 'You have been given {} points due to a donation in your name'.format(finalValue))
