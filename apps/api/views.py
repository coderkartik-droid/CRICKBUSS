from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Q

from apps.accounts.serializers import UserSerializer, UserRegistrationSerializer
from apps.matches.models import Match
from apps.matches.serializers import MatchSerializer
from apps.teams.models import Team
from apps.teams.serializers import TeamSerializer, TeamSimpleSerializer
from apps.players.models import Player
from apps.players.serializers import PlayerSerializer, PlayerSimpleSerializer
from apps.series.models import Series, PointsTableEntry
from apps.series.serializers import SeriesSerializer, PointsTableEntrySerializer
from apps.rankings.models import RankingEntry
from apps.rankings.serializers import RankingEntrySerializer
from apps.news.models import NewsArticle
from apps.news.serializers import NewsArticleSerializer, NewsArticleSimpleSerializer
from apps.videos.models import CricketVideo
from apps.videos.serializers import CricketVideoSerializer

User = get_user_model()

# ================= AUTHENTICATION APIS =================

class APIRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Registration successful.',
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)


class APILoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Email/username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful.',
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })


class APIUserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ================= DATA VIEWSETS =================

class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Match.objects.select_related('team1', 'team2', 'venue').prefetch_related('innings__batters', 'innings__bowlers').all()
    serializer_class = MatchSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class LiveMatchesAPIView(generics.ListAPIView):
    serializer_class = MatchSerializer

    def get_queryset(self):
        return Match.objects.filter(status=Match.Status.LIVE).select_related('team1', 'team2', 'venue').prefetch_related('innings')


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.filter(is_active=True)
    serializer_class = TeamSerializer
    lookup_field = 'slug'


class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Player.objects.filter(
        is_active=True,
        registration_status=Player.RegistrationStatus.APPROVED,
    ).select_related('primary_team').prefetch_related('batting_stats', 'bowling_stats')
    serializer_class = PlayerSerializer
    lookup_field = 'slug'


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Series.objects.filter(is_active=True).prefetch_related('participating_teams', 'points_table')
    serializer_class = SeriesSerializer
    lookup_field = 'slug'


class RankingListAPIView(generics.ListAPIView):
    serializer_class = RankingEntrySerializer

    def get_queryset(self):
        gender = self.request.query_params.get('gender', RankingEntry.Gender.MEN)
        fmt = self.request.query_params.get('format', RankingEntry.Format.TEST)
        category = self.request.query_params.get('category', RankingEntry.Category.BATTERS)

        return RankingEntry.objects.filter(
            gender=gender,
            cricket_format=fmt,
            category=category
        ).order_by('rank')


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NewsArticle.objects.filter(is_published=True).select_related('category')
    serializer_class = NewsArticleSerializer
    lookup_field = 'slug'


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CricketVideo.objects.filter(is_active=True).select_related('category')
    serializer_class = CricketVideoSerializer
    lookup_field = 'slug'


class APIGlobalSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response({'matches': [], 'teams': [], 'players': [], 'news': []})

        matches = Match.objects.filter(Q(title__icontains=q) | Q(team1__name__icontains=q) | Q(team2__name__icontains=q))[:5]
        teams = Team.objects.filter(Q(name__icontains=q) | Q(short_name__icontains=q))[:5]
        players = Player.objects.filter(Q(name__icontains=q) | Q(nickname__icontains=q))[:6]
        news = NewsArticle.objects.filter(Q(title__icontains=q), is_published=True)[:5]

        return Response({
            'matches': MatchSerializer(matches, many=True).data,
            'teams': TeamSimpleSerializer(teams, many=True).data,
            'players': PlayerSimpleSerializer(players, many=True).data,
            'news': NewsArticleSimpleSerializer(news, many=True).data
        })
