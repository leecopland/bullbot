from flask import render_template

from pajbot.managers.db import DBManager
from pajbot.managers.user import UserManager
from pajbot.models.roulette import Roulette
from pajbot.models.dotabet import DotaBetBet
from pajbot.models.dotabet import DotaBetGame


def init(app):
    @app.route('/user/<username>')
    def user_profile(username):
        with DBManager.create_session_scope() as db_session:
            user = UserManager.find_static(username, db_session=db_session)
            if not user:
                return render_template('no_user.html'), 404

            try:
                roulette_stats, roulettes = get_roulette(app, user)
            except TypeError:
                roulette_stats = None
                roulettes = {}
            try:
                dotabet_stats, recent_bets = get_bets(app, user)
            except TypeError:
                dotabet_stats = None
                recent_bets = {}

            return render_template('user.html',
                    user=user,
                    roulette_stats=roulette_stats,
                    dotabet_stats=dotabet_stats,
                    roulettes=roulettes,
                    bets=recent_bets)

def get_bets(app, user):
    with DBManager.create_session_scope() as db_session:
        bets = db_session.query(DotaBetBet).filter_by(user_id=user.id).order_by(DotaBetBet.game_time.desc()).all()

        bet_stats = None
        if len(bets) > 0:
            profit = 0
            total_points = 0
            biggest_profit = 0
            biggest_winstreak = 0
            biggest_losestreak = 0
            num_wins = 0
            num_losses = 0
            winrate = 0
            num_bets = len(bets)
            cw = 0
            for bet in bets:
                profit += bet.profit
                total_points += bet.points

                if bet.profit > 0:
                    # correct bet
                    num_wins += 1
                    if cw < 0:
                        if abs(cw) > biggest_losestreak:
                            biggest_losestreak = abs(cw)
                        cw = 0
                    cw += 1
                else:
                    # loss
                    num_losses += 1
                    if cw > 0:
                        if cw > biggest_winstreak:
                            biggest_winstreak = cw
                        cw = 0
                    cw -= 1

                if bet.profit > biggest_profit:
                    biggest_profit = bet.profit

            if num_losses == 0:
                winrate = 1
            elif num_wins == 0:
                winrate = 0
            else:
                winrate = num_wins / num_bets

            if cw < 0:
                if abs(cw) > biggest_losestreak:
                    biggest_losestreak = abs(cw)
            elif cw > 0:
                if cw > biggest_winstreak:
                    biggest_winstreak = cw

            bet_stats = {
                    'profit': profit,
                    'total_points': total_points,
                    'num_bets': num_bets,
                    'biggest_profit': biggest_profit,
                    'biggest_winstreak': biggest_winstreak,
                    'biggest_losestreak': biggest_losestreak,
                    'winrate': winrate,
                    'winrate_str': '{:.2f}%'.format(winrate * 100),
                    }
            db_session.expunge_all()
            return bet_stats, bets


def get_roulette(app, user):
    with DBManager.create_session_scope() as db_session:
        roulettes = db_session.query(Roulette).filter_by(user_id=user.id).order_by(Roulette.created_at.desc()).all()

        roulette_stats = None
        if len(roulettes) > 0:
            profit = 0
            total_points = 0
            biggest_loss = 0
            biggest_win = 0
            biggest_winstreak = 0
            biggest_losestreak = 0
            num_wins = 0
            num_losses = 0
            winrate = 0
            num_roulettes = len(roulettes)
            cw = 0
            for roulette in roulettes:
                profit += roulette.points
                total_points += abs(roulette.points)

                if roulette.points > 0:
                    # a win!
                    num_wins += 1
                    if cw < 0:
                        if abs(cw) > biggest_losestreak:
                            biggest_losestreak = abs(cw)
                        cw = 0
                    cw += 1
                else:
                    # a loss
                    num_losses += 1
                    if cw > 0:
                        if cw > biggest_winstreak:
                            biggest_winstreak = cw
                        cw = 0
                    cw -= 1

                if roulette.points < biggest_loss:
                    biggest_loss = roulette.points
                elif roulette.points > biggest_win:
                    biggest_win = roulette.points

            # Calculate winrate
            if num_losses == 0:
                winrate = 1
            elif num_wins == 0:
                winrate = 0
            else:
                winrate = num_wins / num_roulettes

            # Finalize win/lose streaks in case we're currently
            # on the biggest win/lose streak
            if cw < 0:
                if abs(cw) > biggest_losestreak:
                    biggest_losestreak = abs(cw)
            elif cw > 0:
                if cw > biggest_winstreak:
                    biggest_winstreak = cw

            if 'roulette' in app.module_manager:
                roulette_base_winrate = 1.0 - app.module_manager['roulette'].settings['rigged_percentage'] / 100
            else:
                roulette_base_winrate = 0.45

            roulette_stats = {
                    'profit': profit,
                    'total_points': total_points,
                    'biggest_win': biggest_win,
                    'biggest_loss': biggest_loss,
                    'num_roulettes': num_roulettes,
                    'biggest_winstreak': biggest_winstreak,
                    'biggest_losestreak': biggest_losestreak,
                    'winrate': winrate,
                    'winrate_str': '{:.2f}%'.format(winrate * 100),
                    'roulette_base_winrate': roulette_base_winrate,
                    }

            db_session.expunge_all()
            return roulette_stats, roulettes
