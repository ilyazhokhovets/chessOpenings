from django.db import models


class Position(models.Model):
    fen = models.CharField('fen', unique=True, max_length=255)

    def __str__(self):
        return self.fen

class PositionParsed(models.Model):
    fen = models.OneToOneField(Position, on_delete=models.CASCADE, primary_key=True,)
    pure_pos = models.CharField('pure_pos', max_length=255, default='')
    white_to_move = models.BooleanField('white_to_move', default=True)
    black_castle_qside = models.BooleanField('black_castle_qside', default=True)
    black_castle_kside = models.BooleanField('black_castle_kside', default=True)
    white_castle_qside = models.BooleanField('white_castle_qside', default=True)
    white_castle_kside = models.BooleanField('white_castle_kside', default=True)
    enpassant = models.CharField('enpassant', max_length=7,)
    no_capture_moves = models.IntegerField('no_capture_moves', default='0')
    n_moves  = models.IntegerField('n_moves', default='1')

    def save(self, *args, **kwargs):

        self.pure_pos = self.fen.fen.split()[0]
        self.white_to_move = self.fen.fen.split()[1] == 'w'
        self.black_castle_kside = 'q' in self.fen.fen.split()[2]
        self.black_castle_qside = 'k' in self.fen.fen.split()[2]
        self.white_castle_kside = 'Q' in self.fen.fen.split()[2]
        self.white_castle_qside = 'K' in self.fen.fen.split()[2]
        self.enpassant = self.fen.fen.split()[3]
        self.no_capture_moves = self.fen.fen.split()[4]
        self.n_moves = self.fen.fen.split()[5]

        super(PositionParsed, self).save(*args, **kwargs)


class PositionInfo(models.Model):
    fen = models.OneToOneField(Position, on_delete=models.CASCADE,primary_key=True,)
    cp = models.IntegerField('cp', null=True)
    mate = models.IntegerField('mate', null=True)
    appearances = models.IntegerField('appearances', null=True)
    white_win_percent = models.FloatField('white_win_percent', null=True)
    black_win_percent = models.FloatField('black_win_percent', null=True)


class Move(models.Model):
    initial_fen = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='initial_fen')
    uci = models.CharField('uci', max_length=255, default='')
    san = models.CharField('san', max_length=255, default='')
    new_fen = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='next_fen')

    def __str__(self):
        return self.uci


class User(models.Model):
    name = models.CharField('name', max_length=255)


class Training(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    move = models.ForeignKey(Move, on_delete=models.CASCADE)
    parent = models.ForeignKey('Training', null=True, default=None, on_delete=models.SET_NULL)


class TrainingStats(models.Model):
    training_obj = models.ForeignKey(Training, on_delete=models.CASCADE)
    total_runs = models.IntegerField('total_runs', default=0, )
    successful_runs = models.IntegerField('successful_runs', default=0)
