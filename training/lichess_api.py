
import chess

STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from stockfish import Stockfish



stockfish = Stockfish(path="../../../../../opt/homebrew/Cellar/stockfish/15.1/bin/stockfish", )

def move_info(fen: str=STARTING_FEN, frequency=0, max_appearances=0) -> dict:
    params = {"fen": fen,
                'speeds': 'blitz,rapid',
               'ratings': '1800,2000,2200,2400,2600',
               'topGames': 0,
               'recentGames': 0}

    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    r = session.get('https://explorer.lichess.ovh/lichess', params=params)

    moves = {}

    total_moves = r.json()['white'] + r.json()['black']+r.json()['draws']

    for move in r.json()['moves']:
        uci = move['uci']
        moves[uci] = {}
        moves[uci]['white'] = move['white']
        moves[uci]['black'] = move['black']
        moves[uci]['times_played'] = move['white'] + move['black'] + move['draws']
        moves[uci]['frequency'] = round(moves[uci]['times_played'] / total_moves, 3)

        if moves[uci]['frequency'] < frequency or moves[uci]['times_played'] < max_appearances:
            moves.pop(uci, None)
    return moves



def pos_info(fen: str=STARTING_FEN, frequency=0, max_appearances=0) -> dict:
    params = {"fen": fen,
               'speeds': 'blitz,rapid',
               'ratings': '1800,2000,2200,2400,2600',
               'topGames': 0,
               'recentGames': 0}

    session = requests.Session()
    retry = Retry(connect=10, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    r = session.get('https://explorer.lichess.ovh/lichess', params=params)

    pos_info_dict = {}

    total_games = r.json()['white'] + r.json()['black']+r.json()['draws']


    pos_info_dict['white'] = r.json()['white'] or 0
    pos_info_dict['black'] = r.json()['black'] or 0
    pos_info_dict['draws'] = r.json()['draws'] or 0
    pos_info_dict['total_games'] = total_games or 0
    return pos_info_dict


def get_next_fen(fen: str, move: str) -> str:
    board = chess.Board(fen=fen)
    board.push(chess.Move.from_uci(move))

    return board.fen()

def legal_moves(fen):
    board = chess.Board(fen=fen)
    return [chess.Move.uci(i) for i in board.legal_moves]





def position_eval(fen=STARTING_FEN):
    stockfish.set_fen_position(fen)
    eval_dict = {'cp': 0, 'mate':0}
    eval_type_value = stockfish.get_evaluation()
    eval_dict[eval_type_value['type']] = eval_type_value['value']
    return eval_dict





def top_moves_eval(fen=STARTING_FEN):
    stockfish.set_fen_position(fen)
    top_moves = {}
    eval_type_value = stockfish.get_top_moves()
    for obj in eval_type_value:
        top_moves[obj['Move']] = obj

    return top_moves