import json
from django.views.generic import ListView, DetailView, TemplateView, View
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from .models import (
    Match,
    Innings,
    BallByBall,
    PlayerMatchInnings,
    BowlerMatchInnings,
    Partnership,
    FallOfWicket,
    Venue,
)
from apps.news.models import NewsArticle
from apps.videos.models import CricketVideo
from apps.photos.models import PhotoAlbum
from apps.players.models import Player
from apps.teams.models import Team
from apps.rankings.models import RankingEntry
from apps.series.models import Series
from apps.matches.services.scoring import record_delivery, undo_last_delivery
from apps.matches.services.statistics import rebuild_points_table


class HomePageView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Local Database Matches
        live_matches = (
            Match.objects.filter(status=Match.Status.LIVE)
            .select_related("team1", "team2", "venue")
            .prefetch_related("innings")[:6]
        )

        upcoming_matches = (
            Match.objects.filter(status=Match.Status.UPCOMING)
            .select_related("team1", "team2", "venue")
            .order_by("start_datetime")[:6]
        )

        recent_results = (
            Match.objects.filter(status=Match.Status.COMPLETED)
            .select_related("team1", "team2", "venue")
            .order_by("-start_datetime")[:6]
        )

        context["hero_live_matches"] = (
            live_matches if live_matches.exists() else upcoming_matches[:4]
        )
        context["live_matches"] = live_matches
        context["upcoming_matches"] = upcoming_matches
        context["recent_results"] = recent_results

        # All match content is managed locally through the database.
        context["local_tournaments"] = Series.objects.filter(
            is_active=True,
        ).prefetch_related("participating_teams")[:6]
        context["featured_series"] = Series.objects.filter(
            is_featured=True,
            is_active=True,
        ).prefetch_related("participating_teams")[:6]

        # 4. News Sections
        context["breaking_news"] = NewsArticle.objects.filter(
            is_breaking=True, is_published=True
        )[:4]
        context["featured_news"] = NewsArticle.objects.filter(
            is_featured=True, is_published=True
        ).first()
        context["top_news"] = NewsArticle.objects.filter(is_published=True).order_by(
            "-published_at"
        )[:6]
        context["trending_stories"] = NewsArticle.objects.filter(
            is_trending=True, is_published=True
        )[:5]

        # 5. Videos
        context["home_videos"] = CricketVideo.objects.filter(
            is_active=True
        ).select_related("category")[:4]

        # 6. Featured Players & Teams
        context["featured_players"] = Player.objects.filter(
            is_featured=True, is_active=True
        ).select_related("primary_team")[:8]
        context["featured_teams"] = Team.objects.filter(
            is_featured=True, is_active=True
        )[:6]

        # 7. ICC Rankings Snippet (Men's Test Batting top 5)
        context["rankings_snippet"] = RankingEntry.objects.filter(
            gender=RankingEntry.Gender.MEN,
            cricket_format=RankingEntry.Format.TEST,
            category=RankingEntry.Category.BATTERS,
        ).order_by("rank")[:5]

        # 8. Photo Gallery Strip
        context["photo_albums"] = PhotoAlbum.objects.filter(is_active=True)[:4]

        return context


class MatchListView(ListView):
    model = Match
    template_name = "matches/match_list.html"
    context_object_name = "matches"
    paginate_by = 12

    def get_queryset(self):
        qs = Match.objects.select_related("team1", "team2", "venue").prefetch_related(
            "innings"
        )
        status_param = self.request.GET.get("status")
        if status_param == "live":
            qs = qs.filter(status=Match.Status.LIVE)
        elif status_param == "upcoming":
            qs = qs.filter(status=Match.Status.UPCOMING)
        elif status_param == "completed":
            qs = qs.filter(status=Match.Status.COMPLETED)

        match_type = self.request.GET.get("type")
        if match_type and match_type in Match.MatchType.values:
            qs = qs.filter(match_type=match_type)

        return qs.order_by("-status", "start_datetime")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_status"] = self.request.GET.get("status", "all")
        context["active_type"] = self.request.GET.get("type", "")
        context["match_types"] = Match.MatchType.choices
        return context


class MatchDetailView(DetailView):
    model = Match
    template_name = "matches/match_detail.html"
    context_object_name = "match"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object

        # Innings list
        innings_list = (
            match.innings.select_related("batting_team", "bowling_team")
            .prefetch_related(
                "batters__player",
                "bowlers__player",
                "fall_of_wickets",
                "partnerships__batter1",
                "partnerships__batter2",
            )
            .all()
        )
        context["innings_list"] = innings_list

        current_inn = match.current_innings or innings_list.first()
        context["current_inn"] = current_inn

        # Current batters and bowler on crease (if match is live or recent innings)
        if current_inn:
            context["crease_batters"] = current_inn.batters.filter(
                dismissal=PlayerMatchInnings.DismissalType.NOT_OUT
            )[:2]
            context["current_bowler"] = current_inn.bowlers.order_by(
                "-overs", "-balls"
            ).first()
            context["recent_balls"] = current_inn.ball_deliveries.order_by(
                "-timestamp"
            )[:12]
            context["all_balls"] = current_inn.ball_deliveries.select_related(
                "batter", "bowler"
            ).order_by("-over_number", "-ball_number")[:40]
        else:
            context["crease_batters"] = []
            context["current_bowler"] = None
            context["recent_balls"] = []
            context["all_balls"] = []

        # Playing XIs
        context["team1_xi"] = match.team1_playing_xi.all()
        context["team2_xi"] = match.team2_playing_xi.all()

        # Head to Head Record
        h2h_matches = Match.objects.filter(
            Q(team1=match.team1, team2=match.team2)
            | Q(team1=match.team2, team2=match.team1),
            status=Match.Status.COMPLETED,
        ).exclude(id=match.id)

        t1_wins = h2h_matches.filter(winning_team=match.team1).count()
        t2_wins = h2h_matches.filter(winning_team=match.team2).count()
        context["h2h_total"] = h2h_matches.count()
        context["h2h_team1_wins"] = t1_wins
        context["h2h_team2_wins"] = t2_wins
        context["h2h_recent"] = h2h_matches.order_by("-start_datetime")[:5]

        # Active Tab (live, scorecard, commentary, playing_xi, graphs, info)
        context["active_tab"] = self.request.GET.get("tab", "live")

        # Check if saved by current user
        if self.request.user.is_authenticated:
            from apps.dashboard.models import SavedMatch

            context["is_saved"] = SavedMatch.objects.filter(
                user=self.request.user, match=match
            ).exists()
        else:
            context["is_saved"] = False

        return context


class MatchLiveScoreJsonView(View):
    """AJAX polling fallback returning live scores in JSON format."""

    def get(self, request, slug):
        match = get_object_or_404(Match, slug=slug)
        curr_inn = match.current_innings

        data = {
            "status": match.get_status_display(),
            "result": match.result_text,
            "is_live": match.status == Match.Status.LIVE,
            "current_innings": None,
        }

        if curr_inn:
            data["current_innings"] = {
                "team": curr_inn.batting_team.short_name,
                "runs": curr_inn.runs,
                "wickets": curr_inn.wickets,
                "overs": curr_inn.overs_formatted,
                "crr": curr_inn.current_run_rate,
                "recent_balls": [
                    {
                        "over": b.over_number,
                        "ball": b.ball_number,
                        "runs": b.runs_off_bat + b.extra_runs,
                        "is_wicket": b.is_wicket,
                        "is_four": b.is_four,
                        "is_six": b.is_six,
                        "commentary": b.commentary,
                    }
                    for b in curr_inn.ball_deliveries.order_by("-timestamp")[:6]
                ],
            }

        return JsonResponse(data)


class MatchGraphsDataJsonView(View):
    """
    Returns Run Rate (Manhattan), Worm Graph, Partnership, and Win Probability data for Chart.js.
    """

    def get(self, request, slug):
        match = get_object_or_404(Match, slug=slug)
        innings = match.innings.all().order_by("innings_number")

        worm_datasets = []
        manhattan_datasets = []
        max_overs = 20 if match.match_type == Match.MatchType.T20 else 50
        overs_labels = [f"Ov {i}" for i in range(1, max_overs + 1)]

        colors = ["#10b981", "#f59e0b", "#3b82f6", "#ef4444"]

        for idx, inn in enumerate(innings):
            balls = inn.ball_deliveries.all().order_by("over_number", "ball_number")
            over_cum_runs = []
            over_runs = {}
            running_total = 0

            for b in balls:
                running_total += b.runs_off_bat + b.extra_runs
                ov = b.over_number
                over_runs[ov] = over_runs.get(ov, 0) + (b.runs_off_bat + b.extra_runs)
                if b.ball_number == 6 or b.is_wicket:
                    over_cum_runs.append(running_total)

            worm_datasets.append(
                {
                    "label": f"{inn.batting_team.short_name} Innings",
                    "data": over_cum_runs if over_cum_runs else [inn.runs],
                    "borderColor": colors[idx % len(colors)],
                    "backgroundColor": "transparent",
                    "tension": 0.3,
                }
            )

            per_over_data = [over_runs.get(i, 0) for i in range(1, max_overs + 1)]
            # Trim trailing zeroes past actual overs
            actual_overs_count = inn.overs if inn.overs > 0 else 1
            manhattan_datasets.append(
                {
                    "label": f"{inn.batting_team.short_name} Over Runs",
                    "data": per_over_data[:actual_overs_count],
                    "backgroundColor": colors[idx % len(colors)],
                    "borderRadius": 4,
                }
            )

        # Win Probability Calculation (Heuristic Model)
        curr_inn = match.current_innings
        team1_prob = 50
        team2_prob = 50

        if match.status == Match.Status.COMPLETED:
            if match.winning_team == match.team1:
                team1_prob, team2_prob = 100, 0
            elif match.winning_team == match.team2:
                team1_prob, team2_prob = 0, 100
        elif match.status == Match.Status.LIVE and curr_inn:
            # If 2nd innings chasing
            if curr_inn.innings_number >= 2 and innings.count() >= 2:
                target = innings.first().runs + 1
                needed = max(target - curr_inn.runs, 0)
                wickets_left = 10 - curr_inn.wickets
                overs_left = max(max_overs - curr_inn.overs, 1)
                req_rate = needed / overs_left

                # Probability calculation
                if req_rate < 6:
                    chasing_prob = min(85 + (wickets_left * 1.5), 98)
                elif req_rate < 8.5:
                    chasing_prob = min(50 + (wickets_left * 3), 85)
                elif req_rate < 12:
                    chasing_prob = max(15 + (wickets_left * 2.5), 10)
                else:
                    chasing_prob = max(5, wickets_left * 1.5)

                if curr_inn.batting_team == match.team1:
                    team1_prob = int(chasing_prob)
                    team2_prob = 100 - team1_prob
                else:
                    team2_prob = int(chasing_prob)
                    team1_prob = 100 - team2_prob
            else:
                # 1st innings
                team1_prob = 55
                team2_prob = 45

        return JsonResponse(
            {
                "labels": (
                    overs_labels[: max(len(d["data"]) for d in worm_datasets)]
                    if worm_datasets
                    else overs_labels[:10]
                ),
                "datasets": worm_datasets,
                "manhattan_datasets": manhattan_datasets,
                "win_probability": {
                    "team1_name": match.team1.short_name,
                    "team1_prob": team1_prob,
                    "team2_name": match.team2.short_name,
                    "team2_prob": team2_prob,
                },
            }
        )


class GlobalSearchView(View):
    template_name = "pages/search.html"

    def get(self, request):
        query = request.GET.get("q", "").strip()
        context = {"query": query}

        if query:
            context["matches"] = Match.objects.filter(
                Q(title__icontains=query)
                | Q(team1__name__icontains=query)
                | Q(team2__name__icontains=query)
            ).select_related("team1", "team2", "venue")[:6]

            context["teams"] = Team.objects.filter(
                Q(name__icontains=query)
                | Q(short_name__icontains=query)
                | Q(country__icontains=query)
            )[:6]

            context["players"] = Player.objects.filter(
                Q(name__icontains=query) | Q(nickname__icontains=query)
            ).select_related("primary_team")[:8]

            context["news"] = NewsArticle.objects.filter(
                Q(title__icontains=query) | Q(excerpt__icontains=query),
                is_published=True,
            )[:6]

            context["videos"] = CricketVideo.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query),
                is_active=True,
            )[:6]
            context["series"] = Series.objects.filter(
                Q(name__icontains=query) | Q(short_name__icontains=query)
            )[:6]
        else:
            context["matches"] = []
            context["teams"] = []
            context["players"] = []
            context["news"] = []
            context["videos"] = []
            context["series"] = []

        return render(request, self.template_name, context)


class SearchSuggestJsonView(View):
    """
    Real-time autocomplete suggestion endpoint for teams, players, matches and series.
    """

    def get(self, request):
        query = request.GET.get("q", "").strip()
        trending = ["India", "Australia", "Virat Kohli", "Jasprit Bumrah", "IPL 2026"]
        if not query or len(query) < 2:
            return JsonResponse({"suggestions": [], "trending": trending})

        suggestions = []

        # Teams
        teams = Team.objects.filter(
            Q(name__icontains=query) | Q(short_name__icontains=query)
        )[:3]
        for t in teams:
            suggestions.append(
                {
                    "type": "Team",
                    "title": t.name,
                    "subtitle": t.country,
                    "url": t.get_absolute_url(),
                    "icon": "fa-solid fa-shield-halved",
                }
            )

        # Players
        players = Player.objects.filter(
            Q(name__icontains=query) | Q(nickname__icontains=query)
        ).select_related("primary_team")[:4]
        for p in players:
            team_label = p.primary_team.short_name if p.primary_team else ""
            suggestions.append(
                {
                    "type": "Player",
                    "title": p.name,
                    "subtitle": (
                        f"{p.get_role_display()} ({team_label})"
                        if team_label
                        else p.get_role_display()
                    ),
                    "url": p.get_absolute_url(),
                    "icon": "fa-solid fa-user",
                }
            )

        # Matches
        matches = Match.objects.filter(
            Q(title__icontains=query)
            | Q(team1__name__icontains=query)
            | Q(team2__name__icontains=query)
        ).select_related("team1", "team2")[:3]
        for m in matches:
            suggestions.append(
                {
                    "type": "Match",
                    "title": m.title,
                    "subtitle": f"{m.match_type} • {m.get_status_display()}",
                    "url": m.get_absolute_url(),
                    "icon": "fa-solid fa-baseball-bat-ball",
                }
            )

        return JsonResponse({"suggestions": suggestions, "trending": trending})


class NewsletterSubscribeView(View):
    def post(self, request):
        email = request.POST.get("email", "").strip()
        if email:
            messages.success(
                request,
                "Thank you! You are now subscribed to CrickScore Live newsletters.",
            )
        else:
            messages.error(request, "Please enter a valid email address.")
        return redirect(request.META.get("HTTP_REFERER", "home"))


# ================= REAL-TIME SCORER OPERATIONS =================

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


def broadcast_live_match(match_id, payload):
    try:
        layer = get_channel_layer()
        if layer:
            async_to_sync(layer.group_send)(
                f"live_match_{match_id}", {"type": "score_update", "data": payload}
            )
    except Exception:
        pass


class LiveScorerPanelView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Match
    template_name = "matches/scorer_panel.html"
    context_object_name = "match"
    slug_url_kwarg = "slug"

    def test_func(self):
        u = self.request.user
        if u.is_superuser or getattr(u, "role", "") == "admin":
            return True
        return (
            getattr(u, "role", "") == "scorer"
            and self.get_object().assigned_scorers.filter(pk=u.pk).exists()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object

        innings_list = match.innings.all().order_by("innings_number")
        current_inn = match.current_innings or innings_list.first()

        context["innings_list"] = innings_list
        context["current_inn"] = current_inn
        context["team1_players"] = match.team1.players.filter(is_active=True)
        context["team2_players"] = match.team2.players.filter(is_active=True)

        if current_inn:
            context["batting_team_players"] = current_inn.batting_team.players.filter(is_active=True)
            context["bowling_team_players"] = current_inn.bowling_team.players.filter(is_active=True)
            context["active_batters"] = current_inn.batters.filter(
                dismissal=PlayerMatchInnings.DismissalType.NOT_OUT
            )
            context["active_bowler"] = current_inn.bowlers.order_by(
                "-overs", "-balls"
            ).first()
            context["recent_deliveries"] = current_inn.ball_deliveries.order_by(
                "-timestamp"
            )[:12]
        else:
            context["batting_team_players"] = context["team1_players"]
            context["bowling_team_players"] = context["team2_players"]
        return context


class LiveScorerActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Handles live ball logging, scoring increments, and triggers WebSocket broadcasts.
    """

    def test_func(self):
        u = self.request.user
        if u.is_superuser or getattr(u, "role", "") == "admin":
            return True
        match = Match.objects.filter(slug=self.kwargs.get("slug")).first()
        return (
            getattr(u, "role", "") == "scorer"
            and match is not None
            and match.assigned_scorers.filter(pk=u.pk).exists()
        )

    def post(self, request, slug):
        match = get_object_or_404(Match, slug=slug)
        current_inn = match.current_innings
        if not current_inn:
            return JsonResponse(
                {"success": False, "message": "No active innings configured."},
                status=400,
            )

        action = request.POST.get("action")

        if action == "record_ball":
            try:
                extra_type_raw = request.POST.get("extra_type", "")
                extra_type = extra_type_raw if extra_type_raw in ("wide", "no_ball", "bye", "leg_bye") else ""
                runs_off_bat_raw = request.POST.get("runs_off_bat", 0)
                try:
                    runs_off_bat_val = int(runs_off_bat_raw)
                except (TypeError, ValueError):
                    runs_off_bat_val = 0
                is_wicket_val = request.POST.get("is_wicket") == "true"

                if is_wicket_val and extra_type not in ("wide", "no_ball"):
                    runs_off_bat_val = 0

                extra_runs_val = 0
                if extra_type == "wide":
                    extra_runs_val = 1
                    runs_off_bat_val = 0
                elif extra_type == "no_ball":
                    extra_runs_val = 1
                elif extra_type == "bye" or extra_type == "leg_bye":
                    extra_runs_val = runs_off_bat_val
                    runs_off_bat_val = 0

                delivery, current_inn = record_delivery(
                    match.id,
                    batter_id=request.POST.get("batter_id") or None,
                    bowler_id=request.POST.get("bowler_id") or None,
                    runs_off_bat=runs_off_bat_val,
                    extra_runs=extra_runs_val,
                    extra_type=extra_type,
                    is_wicket=is_wicket_val,
                    commentary=request.POST.get("commentary", "").strip(),
                    is_free_hit=request.POST.get("is_free_hit") == "true",
                )
            except (
                TypeError,
                ValueError,
                Match.DoesNotExist,
                Innings.DoesNotExist,
            ) as exc:
                return JsonResponse(
                    {"success": False, "message": f"Invalid delivery: {exc}"},
                    status=400,
                )
            payload = {
                "match_id": str(match.id),
                "status": match.get_status_display(),
                "runs": current_inn.runs,
                "wickets": current_inn.wickets,
                "overs": current_inn.overs_formatted,
                "crr": current_inn.current_run_rate,
                "last_ball": {
                    "over": delivery.over_number,
                    "ball": delivery.ball_number,
                    "runs": delivery.runs_off_bat + delivery.extra_runs,
                    "is_wicket": delivery.is_wicket,
                    "commentary": delivery.commentary,
                },
            }
            broadcast_live_match(str(match.id), payload)

            return JsonResponse(
                {
                    "success": True,
                    "score": f"{current_inn.runs}/{current_inn.wickets}",
                    "overs": current_inn.overs_formatted,
                    "crr": current_inn.current_run_rate,
                    "commentary": delivery.commentary,
                    "runs": current_inn.runs,
                    "wickets": current_inn.wickets,
                }
            )

        elif action == "undo_last_ball":
            delivery, current_inn = undo_last_delivery(match.id)
            if not delivery:
                return JsonResponse(
                    {"success": False, "message": "There are no deliveries to undo."},
                    status=400,
                )
            payload = {
                "match_id": str(match.id),
                "status": match.get_status_display(),
                "runs": current_inn.runs,
                "wickets": current_inn.wickets,
                "overs": current_inn.overs_formatted,
                "crr": current_inn.current_run_rate,
                "last_ball": None,
            }
            broadcast_live_match(str(match.id), payload)
            return JsonResponse(
                {
                    "success": True,
                    "score": f"{current_inn.runs}/{current_inn.wickets}",
                    "overs": current_inn.overs_formatted,
                    "crr": current_inn.current_run_rate,
                    "runs": current_inn.runs,
                    "wickets": current_inn.wickets,
                    "message": "Last delivery was undone.",
                }
            )

        elif action == "update_toss":
            team_id = request.POST.get("toss_winner_id")
            decision = request.POST.get("toss_decision", "bat")
            winner = Team.objects.filter(id=team_id).first()
            if winner:
                match.toss_winner = winner
                match.toss_decision = decision
                match.save(update_fields=["toss_winner", "toss_decision"])
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Toss updated: {winner.name} chose to {decision}.",
                    }
                )
            return JsonResponse(
                {"success": False, "message": "Invalid team selected."}, status=400
            )

        elif action == "update_last_delivery":
            try:
                extra_type_raw = request.POST.get("extra_type", "")
                extra_type = extra_type_raw if extra_type_raw in ("wide", "no_ball", "bye", "leg_bye") else ""
                runs_off_bat_raw = request.POST.get("runs_off_bat", 0)
                try:
                    runs_off_bat_val = int(runs_off_bat_raw)
                except (TypeError, ValueError):
                    runs_off_bat_val = 0
                is_wicket_val = request.POST.get("is_wicket") == "true"

                if is_wicket_val and extra_type not in ("wide", "no_ball"):
                    runs_off_bat_val = 0

                extra_runs_val = 0
                if extra_type == "wide":
                    extra_runs_val = 1
                    runs_off_bat_val = 0
                elif extra_type == "no_ball":
                    extra_runs_val = 1
                elif extra_type == "bye" or extra_type == "leg_bye":
                    extra_runs_val = runs_off_bat_val
                    runs_off_bat_val = 0

                last_delivery = current_inn.ball_deliveries.order_by(
                    "-timestamp", "-over_number", "-ball_number"
                ).first()
                if not last_delivery:
                    return JsonResponse(
                        {"success": False, "message": "No delivery recorded yet to update."},
                        status=400,
                    )

                last_delivery.runs_off_bat = runs_off_bat_val
                last_delivery.extra_runs = extra_runs_val
                last_delivery.extra_type = extra_type
                last_delivery.is_four = runs_off_bat_val == 4 and extra_type == ""
                last_delivery.is_six = runs_off_bat_val == 6 and extra_type == ""
                last_delivery.is_wicket = is_wicket_val
                last_delivery.is_wide = extra_type == "wide"
                last_delivery.is_no_ball = extra_type == "no_ball"
                last_delivery.is_bye = extra_type == "bye"
                last_delivery.is_leg_bye = extra_type == "leg_bye"

                batter_id = request.POST.get("batter_id") or None
                bowler_id = request.POST.get("bowler_id") or None
                if batter_id:
                    last_delivery.batter_id = batter_id
                if bowler_id:
                    last_delivery.bowler_id = bowler_id

                commentary = request.POST.get("commentary", "").strip()
                if commentary:
                    last_delivery.commentary = commentary
                else:
                    total = runs_off_bat_val + extra_runs_val
                    last_delivery.commentary = (
                        'Wicket! ' if is_wicket_val else
                        'FOUR! ' if last_delivery.is_four else
                        'SIX! ' if last_delivery.is_six else ''
                    ) + (f'{total} run{"s" if total != 1 else ""} scored.' if total else 'Dot ball.')

                last_delivery.save()

                from apps.matches.services.scoring import recalculate_innings
                recalculate_innings(current_inn)

                if current_inn.is_completed:
                    if current_inn.innings_number == 1:
                        from apps.matches.models import Innings as InningsModel
                        next_inn, _ = InningsModel.objects.get_or_create(
                            match=match, innings_number=2,
                            defaults={
                                'batting_team': current_inn.bowling_team,
                                'bowling_team': current_inn.batting_team,
                                'target_runs': current_inn.runs + 1,
                            },
                        )
                        match.current_innings_number = 2
                        match.status = Match.Status.INNINGS_BREAK
                        match.save(update_fields=['current_innings_number', 'status', 'updated_at'])
                    else:
                        match.status = Match.Status.COMPLETED
                        match.save(update_fields=['status', 'updated_at'])
                else:
                    match.status = Match.Status.LIVE
                    match.save(update_fields=['status', 'updated_at'])

            except (TypeError, ValueError) as exc:
                return JsonResponse(
                    {"success": False, "message": f"Invalid update: {exc}"},
                    status=400,
                )

            payload = {
                "match_id": str(match.id),
                "status": match.get_status_display(),
                "runs": current_inn.runs,
                "wickets": current_inn.wickets,
                "overs": current_inn.overs_formatted,
                "crr": current_inn.current_run_rate,
                "last_ball": {
                    "over": last_delivery.over_number,
                    "ball": last_delivery.ball_number,
                    "runs": last_delivery.runs_off_bat + last_delivery.extra_runs,
                    "is_wicket": last_delivery.is_wicket,
                    "commentary": last_delivery.commentary,
                },
            }
            broadcast_live_match(str(match.id), payload)

            return JsonResponse(
                {
                    "success": True,
                    "score": f"{current_inn.runs}/{current_inn.wickets}",
                    "overs": current_inn.overs_formatted,
                    "crr": current_inn.current_run_rate,
                    "runs": current_inn.runs,
                    "wickets": current_inn.wickets,
                    "commentary": last_delivery.commentary,
                    "message": "Last delivery updated successfully.",
                }
            )

        elif action == "update_score":
            try:
                runs_total = int(request.POST.get("runs_total", current_inn.runs))
                wickets = int(request.POST.get("wickets", current_inn.wickets))
                overs = int(request.POST.get("overs", current_inn.overs))
                balls = int(request.POST.get("balls", current_inn.balls))
                wides = int(request.POST.get("wides", current_inn.wides))
                no_balls = int(request.POST.get("no_balls", current_inn.no_balls))
                byes = int(request.POST.get("byes", current_inn.byes))
                leg_byes = int(request.POST.get("leg_byes", current_inn.leg_byes))
                target_runs = request.POST.get("target_runs")
                if target_runs:
                    target_runs = int(target_runs)
                else:
                    target_runs = current_inn.target_runs
            except ValueError as exc:
                return JsonResponse(
                    {"success": False, "message": f"Invalid numeric value: {exc}"},
                    status=400,
                )

            current_inn.runs = runs_total
            current_inn.wickets = wickets
            current_inn.overs = overs
            current_inn.balls = balls
            current_inn.wides = wides
            current_inn.no_balls = no_balls
            current_inn.byes = byes
            current_inn.leg_byes = leg_byes
            current_inn.target_runs = target_runs
            current_inn.is_completed = current_inn.wickets >= 10 or (
                match.overs_limit and current_inn.overs >= match.overs_limit
            ) or (current_inn.target_runs is not None and current_inn.runs >= current_inn.target_runs)
            current_inn.save(
                update_fields=[
                    "runs", "wickets", "overs", "balls", "wides", "no_balls",
                    "byes", "leg_byes", "target_runs", "is_completed",
                ]
            )

            from apps.matches.services.scoring import recalculate_innings
            recalculate_innings(current_inn)

            if current_inn.is_completed:
                if current_inn.innings_number == 1:
                    from apps.matches.models import Innings as InningsModel
                    next_inn, _ = InningsModel.objects.get_or_create(
                        match=match, innings_number=2,
                        defaults={
                            'batting_team': current_inn.bowling_team,
                            'bowling_team': current_inn.batting_team,
                            'target_runs': current_inn.runs + 1,
                        },
                    )
                    match.current_innings_number = 2
                    match.status = Match.Status.INNINGS_BREAK
                else:
                    match.status = Match.Status.COMPLETED
            else:
                match.status = Match.Status.LIVE
            match.save(update_fields=['status', 'current_innings_number', 'updated_at'])

            payload = {
                "match_id": str(match.id),
                "status": match.get_status_display(),
                "runs": current_inn.runs,
                "wickets": current_inn.wickets,
                "overs": current_inn.overs_formatted,
                "crr": current_inn.current_run_rate,
                "last_ball": None,
            }
            broadcast_live_match(str(match.id), payload)
            return JsonResponse(
                {
                    "success": True,
                    "score": f"{current_inn.runs}/{current_inn.wickets}",
                    "overs": current_inn.overs_formatted,
                    "crr": current_inn.current_run_rate,
                    "runs": current_inn.runs,
                    "wickets": current_inn.wickets,
                    "message": "Score updated successfully.",
                }
            )

        elif action == "set_result":
            result_text = request.POST.get("result_text", "").strip()
            winning_team_id = request.POST.get("winning_team_id")
            mom_id = request.POST.get("man_of_match_id")

            match.status = Match.Status.COMPLETED
            match.result_text = result_text
            if winning_team_id:
                match.winning_team = Team.objects.filter(id=winning_team_id).first()
                if match.winning_team not in (match.team1, match.team2):
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Winning team must be a participant.",
                        },
                        status=400,
                    )
            if mom_id:
                match.man_of_match = Player.objects.filter(id=mom_id).first()

            match.save(
                update_fields=["status", "result_text", "winning_team", "man_of_match"]
            )
            if match.series_id:
                rebuild_points_table(match.series)
            return JsonResponse(
                {"success": True, "message": f"Match concluded: {result_text}"}
            )

        return JsonResponse(
            {"success": False, "message": "Unknown scoring action."}, status=400
        )
