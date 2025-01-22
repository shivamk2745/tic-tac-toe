from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from tictactoe.views import (
    LoginApi,
    RegisterApi,
    GameViewSet
)

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')

urlpatterns = [
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', LoginApi.as_view(), name='login'),
    path('register/', RegisterApi.as_view(), name='register'),
    
    path('', include(router.urls)),
]