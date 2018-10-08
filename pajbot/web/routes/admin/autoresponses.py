import logging

from flask import abort
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from sqlalchemy.orm import joinedload

from pajbot.managers.adminlog import AdminLogManager
from pajbot.managers.db import DBManager
from pajbot.models.autoresponse import Autoresponse
from pajbot.models.autoresponse import AutoresponseData
from pajbot.models.sock import SocketClientManager
from pajbot.web.utils import requires_level

log = logging.getLogger(__name__)


def init(page):
    @page.route('/autoresponses/')
    @requires_level(500)
    def autoresponses(**options):
        with DBManager.create_session_scope() as db_session:
            autoresponses = db_session.query(Autoresponse).options(joinedload(Autoresponse.data).joinedload(AutoresponseData.user), joinedload(Autoresponse.data).joinedload(AutoresponseData.user2)).all()
            return render_template('admin/autoresponses.html',
                    autoresponses=autoresponses)

    @page.route('/autoresponses/create', methods=['GET', 'POST'])
    @requires_level(500)
    def autoresponses_create(**options):
        session.pop('autoresponse_created_id', None)
        session.pop('autoresponse_edited_id', None)
        if request.method == 'POST':
            id = None
            try:
                if 'id' in request.form:
                    id = int(request.form['id'])
                name = request.form['name'].strip()
                whisper = request.form.get('whisper', 'off')
                case_sensitive = request.form.get('case_sensitive', 'off')
                remove_accents = request.form.get('remove_accents', 'off')
                trigger = request.form['trigger']
                response = request.form['response']
                operator = request.form['operator'].strip().lower()
            except (KeyError, ValueError) as e:
                abort(403)

            whisper = True if whisper == 'on' else False
            case_sensitive = True if case_sensitive == 'on' else False
            remove_accents = True if remove_accents == 'on' else False

            if len(name) == 0:
                abort(403)

            if len(trigger) == 0:
                abort(403)

            if len(response) == 0:
                abort(403)

            valid_operators = ['contains', 'startswith', 'endswith', 'exact', 'regex']
            if operator not in valid_operators:
                abort(403)

            user = options.get('user', None)

            if user is None:
                abort(403)

            options = {
                    'name': name,
                    'trigger': trigger,
                    'response': response,
                    'whisper': whisper,
                    'case_sensitive': case_sensitive,
                    'remove_accents': remove_accents,
                    'added_by': user.id,
                    'edited_by': user.id,
                    'operator': operator,
                    }

            if id is None:
                autoresponse = Autoresponse(**options)
                autoresponse.data = AutoresponseData(autoresponse.id, added_by=options['added_by'])

            with DBManager.create_session_scope(expire_on_commit=False) as db_session:
                if id is not None:
                    autoresponse = db_session.query(Autoresponse).options(joinedload(Autoresponse.data)).filter_by(id=id).one_or_none()
                    if autoresponse is None:
                        return redirect('/admin/autoresponses/', 303)
                    autoresponse.set(**options)
                    autoresponse.data.set(edited_by=options['edited_by'])
                    log.info('Updated autoresponse ID {} by user ID {}'.format(autoresponse.id, options['edited_by']))
                    AdminLogManager.post('Autoresponse edited', user, autoresponse.trigger, autoresponse.response)
                else:
                    db_session.add(autoresponse)
                    db_session.add(autoresponse.data)
                    log.info('Added a new autoresponse by user ID {}'.format(options['added_by']))
                    AdminLogManager.post('Autoresponse added', user, autoresponse.trigger, autoresponse.response)

            SocketClientManager.send('autoresponse.update', {'id': autoresponse.id})
            if id is None:
                session['autoresponse_created_id'] = autoresponse.id
            else:
                session['autoresponse_edited_id'] = autoresponse.id
            return redirect('/admin/autoresponses/', 303)
        else:
            return render_template('admin/create_autoresponse.html')

    @page.route('/autoresponses/edit/<autoresponse_id>')
    @requires_level(500)
    def autoresponses_edit(autoresponse_id, **options):
        with DBManager.create_session_scope() as db_session:
            autoresponse = db_session.query(Autoresponse).filter_by(id=autoresponse_id).one_or_none()

            if autoresponse is None:
                return render_template('admin/autoresponse_404.html'), 404

            return render_template('admin/create_autoresponse.html',
                    autoresponse=autoresponse)
