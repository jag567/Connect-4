import random

class Connect4:
    def __init__(self, db, game_id):
        self.board = []
        self.players = {}
        self.winner = None
        for row in range(6):
            self.board.append([])
            for col in range(7):
                self.board[row].append(' ')
        curs = db.cursor()
        try:
            curs.execute("select turn, created, winner from games where game_id = {};".format(game_id))
            game = curs.fetchone()
            self.turn = int(game[0])
            self.created = game[1]
            if game[2]:
                self.winner = game[2]
            curs.execute("select row, col, player from board where game_id = {};".format(game_id))
            for row, col, player in curs.fetchall():
                self.board[row][col] = player;
            curs.execute("select player, player_name from players where game_id = {};".format(game_id))
            for player, player_name in curs.fetchall():
                self.players[player] = player_name
        except:
            raise Exception("Unable to load game state")
        finally:
            curs.close()

    def get_board(self):
        return self.board

    def get_turn(self):
        return self.turn

    def get_players(self):
        return self.players

    def get_created(self):
        return self.created

    def get_curr_player(self):
        return ('X', 'O') [self.turn]

    def get_opponent(self):
        return ('X', 'O') [(self.turn + 1) % 2]

    def get_winner(self):
        return self.winner
    def next_turn(self):
        self.turn = (self.turn + 1) % 2
        return self.turn

    def make_move(self, move, player=None):
        for row in range(len(self.board)):
            if row < len(self.board) - 1:
                if self.board[row + 1][move] != ' ':
                    break
        if not player:
            player = ('X', 'O') [self.turn]
        self.board[row][move] = player
        if not self.winner:
            self.check_across(row, move, player)
        if not self.winner:
            self.check_down(row, move, player)
        if not self.winner:
            self.check_lr(row, move, player)
        if not self.winner:
            self.check_rl(row, move, player)
        return row

    def check_across(self, row, col, player):
        count = 0
        co = col
        while co >= 0 and self.board[row][co] == player:
            count += 1
            co -= 1
        co = col + 1
        while co < len(self.board[row]) and self.board[row][co] == player:
            count += 1
            co += 1
        if count >= 4:
            self.winner = player

    def check_down(self, row, col, player):
        count = 0
        ro = row
        while ro >= 0 and self.board[ro][col] == player:
            count += 1
            ro -= 1
        ro = row + 1
        while ro < len(self.board) and self.board[ro][col] == player:
            count += 1
            ro += 1
        if count >= 4:
            self.winner = player

    def check_lr(self, row, col, player):
        count = 0
        ro = row
        co = col
        while min(ro, co) >= 0 and self.board[ro][co] == player:
            count += 1
            ro -= 1
            co -= 1
        ro = row + 1
        co = col + 1
        while ro < len(self.board) and co < len(self.board[ro]) and self.board[ro][co] == player:
            count += 1
            ro += 1
            co += 1
        if count >= 4:
            self.winner = player

    def check_rl(self, row, col, player):
        count = 0
        ro = row
        co = col
        while ro >= 0 and co < len(self.board[ro]) and self.board[ro][co] == player:
            count += 1
            ro -= 1
            co += 1
        ro = row + 1
        co = col - 1
        while ro < len(self.board) and co >= 0 and self.board[ro][co] == player:
            count += 1
            ro += 1
            co -= 1
        if count >= 4:
            self.winner = player


    def select_move(self):
        score = 8 ** 6
        points = [0 for _ in  range(len(self.board[0]))]
        turn = self.get_turn()
        self.score_moves(turn, points, score, None)
        best = None
        for move in range(len(points)):
            if not self.is_col_full(move):
                if best is None or best < points[move]:
                    best = points[move]
        moves = []
        for move in range(len(points)):
            if points[move] == best and not self.is_col_full(move):
                moves.append(move)
        if moves:
            return random.choice(moves)
        else:
            return None

    def score_moves(self, turn, points, score, pos):
        if score < 1 or not self.more_moves():
            return
        for move in range(len(self.board[0])):
            if self.is_col_full(move):
                continue
            if pos is None:
                index = move
            else:
                index = pos
            self.make_move(move, ('X', 'O') [turn])
            if self.get_winner():
                if turn == self.turn:
                    points[index] += score
                else:
                    points[index] -= score
            else:
                self.score_moves((turn + 1) % 2, points, int(score / 8), index)
            self.remove_move(move)

    def remove_move(self, move):
        for row in range(len(self.board)):
            if self.board[row][move] != ' ':
                break
        self.board[row][move] = ' '
        self.winner = None

    def more_moves(self):
        for col in self.board[0]:
            if col == ' ':
                return True
        return False

    def is_col_full(self, move):
        return self.board[0][move] != ' '
