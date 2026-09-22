import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class LiveMatchConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer handling real-time ball-by-ball, score updates,
    and commentary broadcasts for a specific cricket match.
    """

    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'live_match_{self.match_id}'

        # Join match room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial live snapshot
        match_data = await self.get_match_snapshot()
        await self.send(text_data=json.dumps({
            'type': 'initial_snapshot',
            'data': match_data
        }))

    async def disconnect(self, close_code):
        # Leave match room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Clients can ping or request refresh
        try:
            payload = json.loads(text_data)
            action = payload.get('action')
            if action == 'refresh':
                data = await self.get_match_snapshot()
                await self.send(text_data=json.dumps({
                    'type': 'match_update',
                    'data': data
                }))
        except Exception:
            pass

    async def score_update(self, event):
        """
        Handler for score_update events sent from Django views/tasks.
        """
        await self.send(text_data=json.dumps({
            'type': 'score_update',
            'data': event['data']
        }))

    async def ball_commentary(self, event):
        """
        Handler for newly delivered ball commentary.
        """
        await self.send(text_data=json.dumps({
            'type': 'new_ball',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_match_snapshot(self):
        from .models import Match
        try:
            match = Match.objects.select_related('team1', 'team2', 'venue').get(id=self.match_id)
            current_inn = match.current_innings

            snapshot = {
                'match_id': str(match.id),
                'title': match.title,
                'status': match.get_status_display(),
                'team1': match.team1.short_name,
                'team2': match.team2.short_name,
                'result': match.result_text,
            }

            if current_inn:
                snapshot.update({
                    'batting_team': current_inn.batting_team.short_name,
                    'runs': current_inn.runs,
                    'wickets': current_inn.wickets,
                    'overs': current_inn.overs_formatted,
                    'crr': current_inn.current_run_rate,
                })

            return snapshot
        except Exception as e:
            return {'error': str(e)}
