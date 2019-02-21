from flask import render_template

def init(app):
    @app.route('/playsound')
    def playsound():
        return render_template('playsoundlist.html')
