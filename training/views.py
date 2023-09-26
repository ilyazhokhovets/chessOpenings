import json
import time

from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import *
from .lichess_api import *

def home(request):

    return render(request, 'training/base.html')


from .logic import _delete_db, self_play, Suggest, Processing


class MoveView(APIView):
    def post(self, request):
        _delete_db()
        # self_play()
        return Response(request.data)

class GetTree(APIView):
    def post(self, request):
        global moves
        moves = {
            'fen': STARTING_FEN,
            'children': []
        }


        def make(temp, my_move):
            fen = temp['fen']
            # print(temp)
            if Training.objects.filter(move__initial_fen__fen=fen).exists() or Training.objects.filter(move__new_fen__fen=fen).exists():
                if my_move:
                    print('yes')
                    obj = Training.objects.filter(move__initial_fen__fen=fen).get()
                    x = {
                        'fen': obj.move.new_fen.fen,
                        'move': obj.move.uci,
                        'len': 1,
                        'children': [],

                    }
                    temp['children'].append(x)
                    # print(temp, 'if end')
                    make(x, False)
                    # print(temp, 'if full')

                else:
                    print('no')
                    all_moves = legal_moves(fen)
                    for move in all_moves:
                        a = Position.objects.filter(fen=fen).get()

                        next_fen = get_next_fen(fen, move)
                        obj = Training.objects.filter(move__initial_fen__fen=next_fen)
                        if len(obj) != 0:
                            # if int(a.positionparsed.n_moves) == 1:
                            #     print(len(temp['children']))
                            #     for iii in temp['children']:
                            #         print(iii)
                            #     print('-------')
                            x = {
                                'fen': next_fen,
                                'move': move,
                                'len': 0,
                                'children': [],

                            }
                            temp['children'].append(x)
                            temp['len'] += 1

                            make(x, True)
                            print(temp, 'else full')

        print(moves)
        make(moves, True)
        print(moves)
        return Response(moves)

class Connection(APIView):
    def hint(self, text_data_json):
        r = dict()
        r['status'] = 'hint'
        try:
            obj = Training.objects.filter(move__initial_fen__fen=text_data_json['fen']).get()
            r['move_uci'] = obj.move.uci
        except KeyError:
            r['move_uci'] = 'Not Found'
        return r

    def reset(self, text_data_json):
        r = {}
        r['status'] = 'reset'
        obj = Training.objects.filter(move__initial_fen__fen=text_data_json['fen'])
        print(len(Training.objects.all()))
        r['record'] = len(obj) == 0

        return r

    def send_move(self, text_data_json):
        r = {}
        processing_obj = Processing(text_data_json)
        processing_obj.get_response()

        r['record'] = processing_obj.record
        r['move_uci'] = processing_obj.response_move
        r['status'] = processing_obj.status
        r['stats'] = processing_obj.stats
        return r

    def send_cp(self, text_data_json):
        r = {}
        r['status'] = 'cp'
        obj = PositionInfo.objects.filter(fen__fen=text_data_json['fen']).get()
        cp = obj.cp
        r['cp'] = cp

        return r

    def suggest(self, text_data_json):
        r = {}
        x = Suggest(text_data_json)
        r['status'] = 'suggest'
        r['listMove'] = x.create_list()

        return r

    def post(self, request):
        t1 = time.time()
        text_data_json = request.data
        r = {}
        # text_data_json = json.loads(text_data)

        print('request', text_data_json)

        if text_data_json.get('action') == 'sendMove':
            r =  self.send_move(text_data_json)

        elif text_data_json.get('action') == 'sendCP':
            r =  self.send_cp(text_data_json)

        elif text_data_json.get('action') == 'hint':

            r =  self.hint(text_data_json)

        elif text_data_json.get('action') == 'sendSuggest':
            r =  self.suggest(text_data_json)

        elif text_data_json.get('action') == 'reset':
            r =  self.reset(text_data_json)

        t2 = time.time()
        r['time'] = f'{round(t2 - t1, 2)}s'
        print('response', r['time'], r)

        return Response(json.dumps(r))



