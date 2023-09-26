from rest_framework import serializers

from .models import *


class PositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Position
        fields = ('fen', 'pure_pos', 'cp',)


class MoveSerializer(serializers.ModelSerializer):

    class Meta:
        model = Move
        fields = '__all__'

