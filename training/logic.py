import time

import numpy
from .models import *
from .lichess_api import top_moves_eval, get_next_fen, move_info, legal_moves, STARTING_FEN
def logger(next_move_list=None, next_move_eval=None, fen=None, legal=None,name=''):
    with open('logger.txt', 'a') as f:
        f.write(f'{name}\n'
                f'{fen}\n'
                f'list={len(next_move_list)}  {" ".join(next_move_list)}\n'
                f'eval={len(next_move_eval)}  {" ".join(next_move_eval)}\n'
                f'legal={len(legal)}{" ".join(legal)}\n'
                f'==================\n\n\n')
def logger2(**kwargs):
    pass
def _delete_db():
    # obj = Position.objects.all()
    # obj.delete()
    obj = Training.objects.all()
    obj.delete()
    obj = TrainingStats.objects.all()
    obj.delete()
    # obj = Position(fen=STARTING_FEN)
    # obj.save()
    # obj = Position.objects.filter(fen=STARTING_FEN).get()
    # pos_info = PositionInfo(fen=obj, appearances=861821421)
    # parsed = PositionParsed(fen=obj)
    # pos_info.save()
    # parsed.save()
    x = Move.objects.all()
    print(len(x))
    x = Position.objects.all()
    print(len(x))
    x = Training.objects.all()
    print(len(x))


class Processing:
    def __init__(self, data):
        self.record = data['record']
        self.move_uci = data['move']
        self.initial_fen = data['source_fen']
        self.new_fen = data['fen']
        self.settings = data['settings']
        self.status = 'move'
        self.version2 = data['version2mode']
        self.response_move = None
        self.stats = None

    def _is_move_correct(self):

        training_obj = Training.objects.filter(move__initial_fen__fen=self.initial_fen, move__uci=self.move_uci)
        return len(training_obj) > 0

    def _finish_run(self, success: bool):

        self.status = ['fail', 'success'][success]
        #TODO
        if success:
            obj = TrainingStats.objects.filter(training_obj__move__initial_fen__fen=self.initial_fen).get()
            obj.total_runs += 1
            obj.successful_runs += 1
            obj.save()
        else:
            obj = TrainingStats.objects.filter(training_obj__move__initial_fen__fen=self.initial_fen).get()
            obj.total_runs += 1
            obj.save()

    def _make_move(self):
        move_obj_list = list(Move.objects.filter(initial_fen__fen=self.new_fen))

        pos_info = [p.new_fen.positioninfo.appearances for p in move_obj_list]

        appearances = []
        total = 0
        for appearance_value in pos_info:

            appearances.append(appearance_value or 0)
            total += appearance_value or 0
        nums_to_pop = []
        for num, val in enumerate(appearances):
            if val < total * 0.05:
                nums_to_pop.append(num)

        for i in nums_to_pop[::-1]:
            appearances.pop(i)
            move_obj_list.pop(i)
        total = sum(appearances)
        proba = [appearance_value / total for appearance_value in appearances]
        choice = int(numpy.random.choice(numpy.arange(0, len(move_obj_list)), p=proba,),)

        self.response_move =  move_obj_list[choice].uci

    def _make_certain_move(self):

        move_obj_list = Move.objects.filter(initial_fen__fen=self.new_fen)
        pos_info = [p.new_fen.positioninfo.appearances for p in move_obj_list]

        total = 0
        for appearance_value in pos_info:
            total += appearance_value or 0

        min_appearance = total * 0.05
        move_obj_list = move_obj_list.filter(new_fen__positioninfo__appearances__gt=min_appearance)

        move_obj_list = move_obj_list.order_by('-new_fen__positioninfo__appearances')
        kkk = [(i.uci, i.new_fen.positioninfo.appearances) for i in move_obj_list]
        for p in move_obj_list:
            t = p.uci
            if not Training.objects.filter(move__initial_fen__fen=get_next_fen(self.new_fen, p.uci)).exists():
                self.response_move = p.uci
                break
            else:
                obj = Training.objects.filter(move__initial_fen__fen=get_next_fen(self.new_fen, p.uci)).get()
                tt = obj.move.initial_fen
                tt1 = obj.move.uci

        else:
            self._make_move()


    def _settings_check(self) -> bool:
        #TODO
        x = Position.objects.filter(fen=self.initial_fen,
                                    positionparsed__n_moves__lte=int(self.settings['maxDepth']),)
                                    # positioninfo__cp__range=(int(self.settings['maxCpBlack']), int(self.settings['maxCpWhite'])),
                                    # positioninfo__appearances__gt=int(self.settings['minAppearancePercentTotal']))

        return len(x)>0

    def _update_training(self):

        move = Move.objects.filter(initial_fen__fen=self.initial_fen, uci=self.move_uci).get()

        training_obj, created = Training.objects.get_or_create(move=move)
        if created:
            training_obj.save()
            training_stats_obj = TrainingStats(training_obj=training_obj)
            training_stats_obj.save()

    def _create_children_fens(self):

        pos_obj = Position.objects.filter(fen=self.new_fen).get()

        next_move_list = move_info(self.new_fen)
        next_move_eval = top_moves_eval(self.new_fen)
        logger(next_move_list, next_move_eval, self.new_fen, legal_moves(self.new_fen), name='Proc')
        for move in legal_moves(self.new_fen):
            fen = get_next_fen(self.new_fen, move)
            new_pos_obj, pos_created = Position.objects.get_or_create(fen=fen)

            if pos_created:
                new_pos_obj.save()
                pos_parsed_obj = PositionParsed(fen=new_pos_obj)
                pos_parsed_obj.save()

            move_obj, move_created = Move.objects.get_or_create(initial_fen=pos_obj, uci=move, new_fen=new_pos_obj)
            if move_created: move_obj.save()

            try:
                ww_percent = next_move_list[move]['white'] / next_move_list[move]['times_played']
                bw_percent = next_move_list[move]['black'] / next_move_list[move]['times_played']

            except KeyError:
                ww_percent = None
                bw_percent = None

            pos_info_obj, pos_info_created = PositionInfo.objects.get_or_create(fen=new_pos_obj)

            if pos_info_created:
                try:
                    pos_info_obj.appearances = next_move_list[move]['times_played']

                except KeyError:
                    pos_info_obj.appearances = None

                pos_info_obj.white_win_percent = ww_percent
                pos_info_obj.black_win_percent = bw_percent
                try:
                    pos_info_obj.cp = next_move_eval[move]['Centipawn']
                    pos_info_obj.mate = next_move_eval[move]['Mate']
                except KeyError:
                    pos_info_obj.cp = None
                    pos_info_obj.mate = None
                pos_info_obj.save()

    def _training_handler(self):
        if self._is_move_correct():
            if not self._settings_check():
                self._finish_run(success=True)
            else:
                self._make_certain_move()
                # if Training.objects.filter(move__uci=self.move_uci).exists():
                #     self.status = 'move'
                #     self._make_move()

                obj, created = TrainingStats.objects.filter(
                    training_obj__move__initial_fen__fen=self.initial_fen).get_or_create()
                if created:
                    obj.total_runs = 0
                    obj.successful_runs = 0
                obj.total_runs += 1
                obj.successful_runs += 1
                obj.save()



                next_fen = get_next_fen(self.new_fen, self.response_move)

                if Training.objects.filter(move__initial_fen__fen=next_fen).exists():
                    self.record = False
                    stats = TrainingStats.objects.filter(training_obj__move__initial_fen__fen=next_fen).get()
                    # print(next_fen)
                    self.stats = [stats.successful_runs, stats.total_runs]
                else:
                    self.record = True
                # else:
                #     self._finish_run(success=True)
                #     self.record = True
        else:
            self._finish_run(success=False)

    def _record_handler(self):

        if self._settings_check():
            self._create_children_fens()
            self._update_training()
            self._make_certain_move()

        else:
            self.record = False
            self.status = 'success'
            # move_obj = Training.objects.filter(move__initial_fen__fen=self.initial_fen, move__uci=self.move_uci).get()
            # obj, created = TrainingStats.objects.filter(training_obj=move_obj).get_or_create()
            # if created:
            #     obj.total_runs = 0
            #     obj.successful_runs = 0
            # obj.total_runs += 1
            # obj.successful_runs += 1
            # obj.save()

    def get_response(self):
        if self.new_fen == self.settings['startingFen']:
            self._create_children_fens()
            self._make_certain_move()
            next_fen = get_next_fen(self.new_fen, self.response_move)

            if Training.objects.filter(move__initial_fen__fen=next_fen).exists():
                self.record = False
            else:
                self.record = True

        else:
            if self.record:
                self._record_handler()
            else:
                self._training_handler()


class Suggest:
    def __init__(self, data):
        self.suggestion = []
        self.new_fen = data['fen']
        self.white_move = data['orientation'] == 'white'
    def _create_children_fens(self):
        x = Position.objects.all()
        # print(len(x))
        x = Position.objects.filter(fen=self.new_fen)
        # print(len(x))
        # print(self.new_fen)
        pos_obj, created = Position.objects.filter(fen=self.new_fen).get_or_create()
        if created:
            pos_obj.fen = self.new_fen
            pos_obj.save()
            pos_parsed_obj = PositionParsed(fen=pos_obj)
            pos_parsed_obj.save()
        next_move_list = move_info(self.new_fen)
        next_move_eval = top_moves_eval(self.new_fen)
        logger(next_move_list,next_move_eval,self.new_fen,legal_moves(self.new_fen), name='Suggest')
        for move in legal_moves(self.new_fen):
            fen = get_next_fen(self.new_fen, move)
            new_pos_obj, pos_created = Position.objects.get_or_create(fen=fen)

            if pos_created:
                new_pos_obj.save()
                pos_parsed_obj = PositionParsed(fen=new_pos_obj)
                pos_parsed_obj.save()

            move_obj, move_created = Move.objects.get_or_create(initial_fen=pos_obj, uci=move, new_fen=new_pos_obj)
            if move_created:
                move_obj.save()

            try:
                ww_percent = next_move_list[move]['white'] / next_move_list[move]['times_played']
                bw_percent = next_move_list[move]['black'] / next_move_list[move]['times_played']

            except KeyError:
                ww_percent = None
                bw_percent = None

            pos_info_obj, pos_info_created = PositionInfo.objects.get_or_create(fen=new_pos_obj)

            # if pos_info_created:
            try:
                pos_info_obj.appearances = next_move_list[move]['times_played']

            except KeyError:
                pos_info_obj.appearances = None

            pos_info_obj.white_win_percent = ww_percent
            pos_info_obj.black_win_percent = bw_percent

            try:
                logger2(move=move, added=True)
                pos_info_obj.cp = next_move_eval[move]['Centipawn']
                pos_info_obj.mate = next_move_eval[move]['Mate']
                # print('ok')
            except KeyError:
                # print(next_move_eval)
                logger2(move=move,  added=False)
                pos_info_obj.cp = None
                pos_info_obj.mate = None
            pos_info_obj.save()
    def _create_children_fe1ns(self):


        pos_obj, pos_created = Position.objects.get_or_create(fen=self.new_fen)
        if pos_created:
            pos_obj.save()
            pos_parsed_obj = PositionParsed(fen=pos_obj)
            pos_parsed_obj.save()
        next_move_list = move_info(self.new_fen)
        next_move_eval = top_moves_eval(self.new_fen)

        for move in next_move_list.keys():
            fen = get_next_fen(self.new_fen, move)
            new_pos_obj, new_pos_created = Position.objects.get_or_create(fen=fen)

            if new_pos_created:
                new_pos_obj.save()
                pos_parsed_obj = PositionParsed(fen=new_pos_obj)
                pos_parsed_obj.save()

            move_obj, move_created = Move.objects.get_or_create(initial_fen=pos_obj, uci=move, new_fen=new_pos_obj)
            if move_created:
                move_obj.save()

            ww_percent = next_move_list[move]['white'] / next_move_list[move]['times_played']
            bw_percent = next_move_list[move]['black'] / next_move_list[move]['times_played']
            pos_info_obj, pos_info_created = PositionInfo.objects.get_or_create(fen=new_pos_obj)

            if pos_info_created:
                pos_info_obj.appearances = next_move_list[move]['times_played']
                pos_info_obj.white_win_percent = ww_percent
                pos_info_obj.black_win_percent = bw_percent
                try:
                    pos_info_obj.cp = next_move_eval[move]['Centipawn']
                    pos_info_obj.mate = next_move_eval[move]['Mate']
                except KeyError:
                    pos_info_obj.cp = None
                    pos_info_obj.mate = None
                pos_info_obj.save()

    def create_list(self):
        x = Move.objects.filter(initial_fen__fen=self.new_fen)
        # for i in x:
        #     print(i.new_fen.positioninfo.cp, i.new_fen.positioninfo.appearances, i.new_fen.fen, i.initial_fen.fen, i.uci)
        move_obj = Move.objects.filter(initial_fen__fen=self.new_fen, new_fen__positioninfo__cp__isnull=False )
        self._create_children_fens()

        for move in move_obj:

            self.suggestion.append({'move': move.uci,
                                    'white_win': move.new_fen.positioninfo.white_win_percent,
                                    'black_win':move.new_fen.positioninfo.black_win_percent,
                                    'appearances': move.new_fen.positioninfo.appearances,
                                    'cp': move.new_fen.positioninfo.cp})
        self.suggestion.sort(key=lambda x: x['cp'], reverse=self.white_move)
        # print(len(self.suggestion))
        return self.suggestion[:5]

def self_play():
    count = 0
    while 1:
        count+= 1
        t1 = time.time()
        print(f'game {count}')
        queue = [STARTING_FEN]
        pgn = []
        while queue:

            fen = queue[0]
            queue.pop(0)
            if Training.objects.filter(move__initial_fen__fen=fen).exists():
                move = Training.objects.filter(move__initial_fen__fen=fen).get().move
                pgn.append(move.uci)
                queue.append(move.new_fen.fen)

                continue
            data = {
                'record':'',
            'move':'',
            'source_fen': '',
            'fen':fen,
            'settings':'',
            'version2mode':''
            }
            p = Processing(data)
            p._create_children_fens()
            p._make_certain_move()

            nf = get_next_fen(fen, p.response_move)
            pgn.append(p.response_move)
            if PositionParsed.objects.filter(fen__fen=nf).get().n_moves < 10:
                queue.append(nf)
        t2 = time.time()
        print(round(t2-t1,2))
        print(' '.join(pgn))
        print()