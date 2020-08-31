
# A a connect 4 game with head to head ability

from flask import Flask, render_template, request, redirect, make_response
import MySQLdb
import Connect4


app = Flask(__name__)
app.config["DEBUG"] = True




def opponent(code):
    if code == 'O':
        return 'X'
    else:
        return 'O'

@app.route('/')
def hello_world():
    return 'Hello from Flask!'

@app.route('/c4')
def c4():
    return render_template('c4.html')

@app.route('/c4/start', methods=['GET', 'POST'])
def c4_start():
    return render_template('c4_start.html', name=request.form.get('name'))

@app.route('/c4/start/<code>', methods=['GET', 'POST'])
def c4_start_player(code):
    db = MySQLdb.connect(DATABASE_CONNECTION, HOST_ACCOUNT, DATABASE_PW, DATABASE_NAME)
    password = request.form.get('password')
    curs = db.cursor()
    game_id = None
    try:
        curs.execute("delete from games where created < date_sub(now(), interval 2 hour);")
        curs.execute("insert into games(password) values(NULL);")
        game_id = db.insert_id()
        curs.execute("select created from games where game_id = {};".format(game_id))
        created = curs.fetchone()[0];
        if password:
            curs.execute("update games set password = {} where game_id = {};".format(hash(password + str(created)), game_id))
        curs.execute('insert into players(game_id, player, player_name) values({}, "{}", "{}");'.format(game_id, code, request.form.get("name")))
        if request.form.get("opponent", "human") == "computer":
            curs.execute('insert into players(game_id, player) values({}, "{}");'.format(game_id, opponent(code)))
            if code == 'O':
                game = Connect4.Connect4(db, game_id)
        db.commit()
    except Exception as ex:
        db.rollback()
        print('c4 start', code, ex)
        return ' '.join('c4 start', code, str(ex))
    curs.close()
    db.close()
    if request.form.get("opponent", "human") == "computer":
        if code == 'O':
            move = game.select_move()
            row = game.make_move(move)
            db = MySQLdb.connect(DATABASE_CONNECTION, HOST_ACCOUNT, DATABASE_PW, DATABASE_NAME)
            curs = db.cursor()
            try:
                curs.execute('insert into board(game_id, row, col, player) values({}, {}, {}, "{}");'.format(game_id, row, move, opponent(code)))
                curs.execute('update games set turn = {} where game_id = {};'.format(game.next_turn(), game_id))
                db.commit()
            except Exception as ex:
                db.rollback()
                print('c4 start', code, ex)
                return str(ex)
            curs.close()
            db.close()
    key = str(hash(str(game_id) + str(created)))
    print("Create cookie for", game_id, created, 'as', key)
    response = make_response(redirect('/c4/play/' + str(game_id) + '/' + code))
    response.set_cookie('c4', key)
    return response

@app.route('/c4/play/<game_id>/<player>')
def c4_play(game_id, player):
    db = MySQLdb.connect(DATABASE_CONNECTION, HOST_ACCOUNT, DATABASE_PW, DATABASE_NAME)
    try:
        game = Connect4.Connect4(db, game_id)
    except Exception as ex:
        print ('c4 play', game_id, player, ex)
        return str(ex)
    db.close()
    created = game.get_created()
    key = str(hash(str(game_id) + str(created)))
    for _ in range(4):
        cookie = request.cookies.get('c4')
        if cookie is not None:
            break
    if key != cookie:
        print("c4 play Cookie not valid")
        return "c4 play Cookie not valid"
    block_moves = True
    refresh_state = True
    winner = game.get_winner()
    if len(game.get_players()) < 2:
        message = "Waiting for " + game.get_opponent() + " to join"
    elif not game.more_moves():
        message = "No more moves"
        refresh_state = False
    elif winner and winner == player:
        message = "You won"
        refresh_state = False
    elif winner and winner != player:
        message = "You lost"
        refresh_state = False
    elif player == game.get_curr_player():
        block_moves = False
        refresh_state = False
        message = "Your turn " + player
    else:
        message = "Waiting for " + game.get_curr_player() + " to move"
    # db.close()
    return render_template("c4_play.html", board=game.get_board(), game_id=game_id, player=player, message=message, block_moves=block_moves, refresh_state=refresh_state)

@app.route('/c4/move/<game_id>/<player>/<move>')
def c4_move(game_id, player, move):
    db = MySQLdb.connect(DATABASE_CONNECTION, HOST_ACCOUNT, DATABASE_PW, DATABASE_NAME)
    try:
        game = Connect4.Connect4(db, game_id)
    except Exception as ex:
        print('c4 move (game init)', player, ex)
        return 'c4 move (game init) ' + player + ' ' + str(ex)
    row = game.make_move(int(move))
    curs = db.cursor()
    try:
        curs.execute('insert into board(game_id, row, col, player) values({}, {}, {}, "{}");'.format(game_id, row, move, player))
        winner = game.get_winner()
        if winner:
            winner = '"' + winner + '"'
        else:
            winner = "NULL"
        curs.execute('update games set turn = {}, winner = {} where game_id = {};'.format(game.next_turn(), winner, game_id))
        db.commit()
    except Exception as ex:
        db.rollback()
        print('c4 move (player move)', player, ex)
        return 'c4 move (player move) ' + player + ' ' + str(ex)
    curs.close()
    db.close()

    if not game.get_players()[opponent(player)] and not game.get_winner():
        # print('user move', move, row)
        # print(game.board)
        move = game.select_move()
        if move is None:
            return redirect('/c4/play/' + game_id + '/' + player)
        row = game.make_move(move)
        # print('computer move', move, row)
        winner = game.get_winner()
        if winner:
            winner = '"' + winner + '"'
        else:
            winner = "NULL"
        db = MySQLdb.connect(DATABASE_CONNECTION, HOST_ACCOUNT, DATABASE_PW, DATABASE_NAME)
        curs = db.cursor()
        try:
            curs.execute('insert into board(game_id, row, col, player) values({}, {}, {}, "{}");'.format(game_id, row, move, opponent(player)))
            curs.execute('update games set turn = {}, winner = {} where game_id = {};'.format(game.next_turn(), winner, game_id))
            db.commit()
        except Exception as ex:
            db.rollback()
            print('c4 move (computer move)', opponent(player), move, ex)
            curs.close()
            db.close()
            return 'c4 move (computer move) ' + opponent(player) + ' ' + str(move) + ' ' + str(ex)
        curs.close()
        db.close()
    return redirect('/c4/play/' + game_id + '/' + player)

@app.route('/c4/join', methods=['GET', 'POST'])
def c4_join():
    db = MySQLdb.connect(DATABASE_CONNECTION, HOST_ACCOUNT, DATABASE_PW, DATABASE_NAME)
    curs = db.cursor()
    try:
        curs.execute('select game_id, player, player_name, count(*) from players  group by game_id having count(*) = 1;')
    except Exception as ex:
        print('c4 join', ex)
        return 'c4 join ' + str(ex)
    available = []
    for row in curs.fetchall():
        available.append((row[0], opponent(row[1]), row[2]))
    curs.close()
    db.close()
    return render_template('c4_join.html', name=request.form.get('name'), available=available)

@app.route('/c4/join/<game_id>/<code>', methods=['GET', 'POST'])
def c4_join_game(game_id, code):
    db = MySQLdb.connect(DATABASE_CONNECTION, HOST_ACCOUNT, DATABASE_PW, DATABASE_NAME)
    joinpw = request.form.get('password')
    curs = db.cursor()
    try:
        curs.execute("select password, created from games where game_id = {};".format(game_id))
        gamepw, created = curs.fetchone()

        if gamepw:
            joinpw = str(hash(joinpw + str(created)))
            # print('password', gamepw, joinpw)
            if gamepw != joinpw:
                print('c4 join', game_id, code, 'Password does not match')
                return 'c4 join ' + game_id + ' ' + code + ' Password does not match'
        curs.execute('insert into players(game_id, player, player_name) values({}, "{}", "{}");'.format(game_id, code, request.form.get("name")))
        db.commit()
    except Exception as ex:
        db.rollback()
        print('c4 join', game_id, code, ex)
        curs.close()
        db.close()
        return 'c4 join ' + game_id + ' ' + code + ' ' + str(ex)
    key = str(hash(str(game_id) + str(created)))
    response = make_response(redirect('/c4/play/' + str(game_id) + '/' + code))
    response.set_cookie('c4', key)
    curs.close()
    db.close()
    return response



