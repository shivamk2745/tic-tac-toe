from rest_framework import serializers
from .models import UserModel,Game,UserGameStats


class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = UserModel
        fields = ['email', 'username', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'username': {'required': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({'password': 'Passwords must match'})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        return UserModel.objects.create_user(**validated_data)



class LoginSerializer(serializers.Serializer):
    email=serializers.EmailField()
    password=serializers.CharField(write_only=True)

    def validate(self,attrs):
        email=attrs.get('email')
        password=attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Email and Password is required')
        
        return attrs




class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'player1', 'player2', 'board', 'current_turn', 'winner', 'is_complete', 'created_at']
        read_only_fields = ['board', 'current_turn', 'winner', 'is_complete']


class UserGameStatsSerializer(serializers.ModelSerializer):
    win_rate = serializers.SerializerMethodField()

    class Meta:
        model = UserGameStats
        fields = ['total_games', 'wins', 'losses', 'draws', 'win_rate']

    def get_win_rate(self, obj):
        if obj.total_games == 0:
            return 0
        return round((obj.wins / obj.total_games) * 100, 2)        