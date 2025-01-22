from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response 
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.contrib.auth import authenticate
from .serializer import LoginSerializer, RegisterSerializer,GameSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Game,UserModel
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

class LoginApi(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(request, username=email, password=password)

            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': "Login Successful",
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class RegisterApi(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User registered successfully',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    


class GameViewSet(viewsets.ModelViewSet):
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Game.objects.filter(Q(player1=user) | Q(player2=user))

    def create(self, request):
        player2_id = request.data.get('player2')
        try:
            player2 = UserModel.objects.get(id=player2_id)
        except UserModel.DoesNotExist:
            return Response({'error': 'Player 2 not found'}, status=status.HTTP_404_NOT_FOUND)
        
        game = Game.objects.create(
            player1=request.user,
            player2=player2,
            current_turn=request.user,
        )
        return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def make_move(self, request, pk=None):
        game = self.get_object()
        position = request.data.get('position')
        
        if not isinstance(position, int) or position < 0 or position > 8:
            return Response({'error': 'Invalid position'}, status=status.HTTP_400_BAD_REQUEST)
            
        if game.is_complete:
            return Response({'error': 'Game is already complete'}, status=status.HTTP_400_BAD_REQUEST)
            
        if game.current_turn != request.user:
            return Response({'error': 'Not your turn'}, status=status.HTTP_400_BAD_REQUEST)
            
        if game.board[position] != '-':
            return Response({'error': 'Position already taken'}, status=status.HTTP_400_BAD_REQUEST)

        board_list = list(game.board)
        symbol = 'X' if request.user == game.player1 else 'O'
        board_list[position] = symbol
        game.board = ''.join(board_list)

       
        combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], 
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  
            [0, 4, 8], [2, 4, 6]  
        ]

        for combo in combinations:
            if all(game.board[i] == symbol for i in combo):
                game.winner = request.user
                game.is_complete = True
                break

        if not game.is_complete and '-' not in game.board:
            game.is_complete = True

        if not game.is_complete:
            game.current_turn = game.player2 if request.user == game.player1 else game.player1

        game.save()
        return Response(GameSerializer(game).data)

    @action(detail=False, methods=['get'], url_path='stats')
    def get_stats(self, request):
        user = request.user
        
        games = Game.objects.filter(Q(player1=user) | Q(player2=user))
        total_games = games.count()
        wins = games.filter(winner=user).count()
        completed_games = games.filter(is_complete=True)
        losses = completed_games.filter(winner__isnull=False).exclude(winner=user).count()
        draws = completed_games.filter(winner__isnull=True).count()

        stats = {
            'total_games': total_games,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': round((wins / total_games * 100), 2) if total_games > 0 else 0
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        users = UserModel.objects.all()
        leaderboard_data = []
        
        for user in users:
            games = Game.objects.filter(Q(player1=user) | Q(player2=user))
            wins = games.filter(winner=user).count()
            total_games = games.count()
            
            if total_games > 0:
                leaderboard_data.append({
                    'username': user.username,
                    'wins': wins,
                    'total_games': total_games,
                    'win_rate': round((wins / total_games * 100), 2)
                })
        
        leaderboard_data = sorted(leaderboard_data, key=lambda x: x['wins'], reverse=True)
        return Response(leaderboard_data[:10])
