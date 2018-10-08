import argparse
import logging
import re

import sqlalchemy
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship
from unidecode import unidecode

from pajbot.managers.db import Base
from pajbot.managers.db import DBManager
from pajbot.utils import find

log = logging.getLogger('pajbot')


class Autoresponse(Base):
    __tablename__ = 'tb_autoresponse'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, default='')
    trigger = Column(String(256), nullable=False)
    response = Column(String(256), nullable=False)
    whisper = Column(Boolean, nullable=False, default=True)
    case_sensitive = Column(Boolean, nullable=False, default=False)
    remove_accents = Column(Boolean, nullable=False, default=False)
    enabled = Column(Boolean, nullable=False, default=True)
    operator = Column(Enum('contains', 'startswith', 'endswith', 'exact', 'regex'),
            nullable=False,
            default='contains',
            server_default='contains')

    data = relationship('AutoresponseData',
            uselist=False,
            cascade='',
            lazy='joined')

    DEFAULT_TIMEOUT_LENGTH = 300
    DEFAULT_NOTIFY = True

    def __init__(self, **options):
        self.id = None
        self.name = 'No name'
        self.whisper = False
        self.case_sensitive = False
        self.enabled = True
        self.operator = 'contains'
        self.remove_accents = False

        self.set(**options)

    def set(self, **options):
        self.name = options.get('name', self.name)
        self.trigger = options.get('trigger', self.trigger)
        self.response = options.get('response', self.response)
        self.whisper = options.get('whisper', self.whisper)
        self.case_sensitive = options.get('case_sensitive', self.case_sensitive)
        self.enabled = options.get('enabled', self.enabled)
        self.operator = options.get('operator', self.operator)
        self.remove_accents = options.get('remove_accents', self.remove_accents)

        self.refresh_operator()

    def format_message(self, message):
        if self.case_sensitive is False:
            message = message.lower()
        if self.remove_accents:
            message = unidecode(message)
        return message

    def get_trigger(self):
        if self.case_sensitive is False:
            return self.trigger.lower()
        return self.trigger

    def refresh_operator(self):
        self.predicate = getattr(self, 'predicate_{}'.format(self.operator), None)

    def predicate_regex(self, message):
        return bool(re.search(self.get_trigger(), self.format_message(message)))

    def predicate_contains(self, message):
        return self.get_trigger() in self.format_message(message)

    def predicate_startswith(self, message):
        return self.format_message(message).startswith(self.get_trigger())

    def predicate_endswith(self, message):
        return self.format_message(message).endswith(self.get_trigger())

    def predicate_exact(self, message):
        return self.format_message(message) == self.get_trigger()

    def match(self, message, user):
        """
        Returns True if message matches our trigger.
        Otherwise it returns False
        Respects case-sensitiveness option
        """
        return self.predicate(message)

    def exact_match(self, message):
        """
        Returns True if message exactly matches our autoresponse.
        Otherwise it returns False
        Respects case-sensitiveness option
        """
        if self.case_sensitive:
            return self.trigger == message
        else:
            return self.trigger.lower() == message.lower()

    def jsonify(self):
        return {
                'name': self.name,
                'trigger': self.trigger,
                'response': self.response,
                }


@sqlalchemy.event.listens_for(Autoresponse, 'load')
def on_autoresponse_load(target, context):
    target.refresh_operator()


@sqlalchemy.event.listens_for(Autoresponse, 'refresh')
def on_autoresponse_refresh(target, context, attrs):
    target.refresh_operator()


class AutoresponseData(Base):
    __tablename__ = 'tb_autoresponse_data'

    autoresponse_id = Column(Integer,
            ForeignKey('tb_autoresponse.id'),
            primary_key=True,
            autoincrement=False)
    num_uses = Column(Integer, nullable=False, default=0)
    added_by = Column(Integer, nullable=True)
    edited_by = Column(Integer, nullable=True)

    user = relationship('User',
            primaryjoin='User.id==AutoresponseData.added_by',
            foreign_keys='User.id',
            uselist=False,
            cascade='',
            lazy='noload')

    user2 = relationship('User',
            primaryjoin='User.id==AutoresponseData.edited_by',
            foreign_keys='User.id',
            uselist=False,
            cascade='',
            lazy='noload')

    def __init__(self, autoresponse_id, **options):
        self.autoresponse_id = autoresponse_id
        self.num_uses = 0
        self.added_by = None
        self.edited_by = None

        self.set(**options)

    def set(self, **options):
        self.num_uses = options.get('num_uses', self.num_uses)
        self.added_by = options.get('added_by', self.added_by)
        self.edited_by = options.get('edited_by', self.edited_by)


class AutoresponseManager:
    def __init__(self, bot):
        self.bot = bot
        self.autoresponses = []
        self.enabled_autoresponses = []
        self.db_session = DBManager.create_session(expire_on_commit=False)

        if self.bot:
            self.bot.socket_manager.add_handler('autoresponse.update', self.on_autoresponse_update)
            self.bot.socket_manager.add_handler('autoresponse.remove', self.on_autoresponse_remove)

    def on_autoresponse_update(self, data, conn):
        try:
            autoresponse_id = int(data['id'])
        except (KeyError, ValueError):
            log.warn('No autoresponse ID found in on_autoresponse_update')
            return False

        updated_autoresponse = find(lambda autoresponse: autoresponse.id == autoresponse_id, self.autoresponses)
        if updated_autoresponse:
            with DBManager.create_session_scope(expire_on_commit=False) as db_session:
                db_session.add(updated_autoresponse)
                db_session.refresh(updated_autoresponse)
                db_session.expunge(updated_autoresponse)
        else:
            with DBManager.create_session_scope(expire_on_commit=False) as db_session:
                updated_autoresponse = db_session.query(Autoresponse).filter_by(id=autoresponse_id).one_or_none()
                db_session.expunge_all()
                if updated_autoresponse is not None:
                    self.db_session.add(updated_autoresponse.data)

        if updated_autoresponse:
            if updated_autoresponse not in self.autoresponses:
                self.autoresponses.append(updated_autoresponse)
            if updated_autoresponse.enabled is True and updated_autoresponse not in self.enabled_autoresponses:
                self.enabled_autoresponses.append(updated_autoresponse)

        for autoresponse in self.enabled_autoresponses:
            if autoresponse.enabled is False:
                self.enabled_autoresponses.remove(autoresponse)

    def on_autoresponse_remove(self, data, conn):
        try:
            autoresponse_id = int(data['id'])
        except (KeyError, ValueError):
            log.warn('No autoresponse ID found in on_autoresponse_remove')
            return False

        removed_autoresponse = find(lambda autoresponse: autoresponse.id == autoresponse_id, self.autoresponses)
        if removed_autoresponse:
            if removed_autoresponse.data and removed_autoresponse.data in self.db_session:
                self.db_session.expunge(removed_autoresponse.data)

            if removed_autoresponse in self.enabled_autoresponses:
                self.enabled_autoresponses.remove(removed_autoresponse)

            if removed_autoresponse in self.autoresponses:
                self.autoresponses.remove(removed_autoresponse)

    def load(self):
        self.autoresponses = self.db_session.query(Autoresponse).all()
        for autoresponse in self.autoresponses:
            self.db_session.expunge(autoresponse)
        self.enabled_autoresponses = [autoresponse for autoresponse in self.autoresponses if autoresponse.enabled is True]
        return self

    def commit(self):
        self.db_session.commit()

    def create_autoresponse(self, rawMessage, **options):
        trigger = rawMessage.split(' ')[0]
        response = rawMessage.split(' ')[1]
        for autoresponse in self.autoresponses:
            if autoresponse.trigger == trigger:
                return autoresponse, False

        autoresponse = Autoresponse(trigger=trigger, response=response, **options)
        autoresponse.data = AutoresponseData(autoresponse.id, added_by=options.get('added_by', None))

        self.db_session.add(autoresponse)
        self.db_session.add(autoresponse.data)
        self.commit()
        self.db_session.expunge(autoresponse)

        self.autoresponses.append(autoresponse)
        self.enabled_autoresponses.append(autoresponse)

        return autoresponse, True

    def remove_autoresponse(self, autoresponse):
        self.autoresponses.remove(autoresponse)
        if autoresponse in self.enabled_autoresponses:
            self.enabled_autoresponses.remove(autoresponse)

        self.db_session.expunge(autoresponse.data)
        self.db_session.delete(autoresponse)
        self.db_session.delete(autoresponse.data)
        self.commit()

    def reply(self, source, autoresponse):
        self.bot.send_message_to_user(source, autoresponse.response)

    def check_message(self, message, user):
        match = find(lambda autoresponse: autoresponse.match(message, user), self.enabled_autoresponses)
        return match or False

    def find_match(self, message, id=None):
        match = None
        if id is not None:
            match = find(lambda autoresponse: autoresponse.id == id, self.autoresponses)
        if match is None:
            match = find(lambda autoresponse: autoresponse.exact_match(message), self.autoresponses)
        return match

    def parse_autoresponse_arguments(self, message):
        parser = argparse.ArgumentParser()
        parser.add_argument('--whisper', dest='whisper', action='store_true')
        parser.add_argument('--no-whisper', dest='whisper', action='store_false')
        parser.add_argument('--casesensitive', dest='case_sensitive', action='store_true')
        parser.add_argument('--no-casesensitive', dest='case_sensitive', action='store_false')
        parser.add_argument('--removeaccents', dest='remove_accents', action='store_true')
        parser.add_argument('--no-removeaccents', dest='remove_accents', action='store_false')
        parser.add_argument('--name', nargs='+', dest='name')
        parser.set_defaults(whisper=None,
                case_sensitive=None,
                remove_accents=None)

        try:
            args, unknown = parser.parse_known_args(message.split())
        except SystemExit:
            return False, False
        except:
            log.exception('Unhandled exception in add_command')
            return False, False

        # Strip options of any values that are set as None
        options = {k: v for k, v in vars(args).items() if v is not None}
        response = ' '.join(unknown)

        if 'name' in options:
            options['name'] = ' '.join(options['name'])

        log.info(options)

        return options, response
