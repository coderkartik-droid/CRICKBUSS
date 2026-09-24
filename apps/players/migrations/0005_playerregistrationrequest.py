import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0004_merge_20260923_2157'),
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerRegistrationRequest',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('full_name',     models.CharField(max_length=120, verbose_name='full name')),
                ('mobile_number', models.CharField(max_length=20,  verbose_name='mobile number')),
                ('email_address', models.EmailField(blank=True,    verbose_name='email address')),
                ('full_address',  models.TextField(blank=True,     verbose_name='full address')),
                ('date_of_birth', models.DateField(null=True, blank=True, verbose_name='date of birth')),
                ('jersey_number', models.PositiveIntegerField(null=True, blank=True, verbose_name='jersey number')),
                ('photo',         models.ImageField(
                    blank=True, null=True,
                    upload_to='player_requests/photos/',
                    verbose_name='player photo',
                )),
                ('country',       models.CharField(blank=True, max_length=80,  verbose_name='country')),
                ('state',         models.CharField(blank=True, max_length=100, verbose_name='state / province')),
                ('city',          models.CharField(blank=True, max_length=100, verbose_name='city')),
                ('playing_role',  models.CharField(
                    choices=[
                        ('batter',      'Top-order Batter'),
                        ('wicketkeeper','Wicketkeeper Batter'),
                        ('all_rounder', 'All-Rounder'),
                        ('bowler',      'Bowler'),
                    ],
                    default='batter', max_length=30,
                    verbose_name='playing role',
                )),
                ('batting_style', models.CharField(
                    choices=[
                        ('right_hand', 'Right Handed Bat'),
                        ('left_hand',  'Left Handed Bat'),
                    ],
                    default='right_hand', max_length=30,
                    verbose_name='batting style',
                )),
                ('bowling_style', models.CharField(
                    choices=[
                        ('right_fast',    'Right-arm Fast'),
                        ('right_medium',  'Right-arm Medium'),
                        ('right_off_spin','Right-arm Offbreak'),
                        ('right_leg_spin','Right-arm Legbreak'),
                        ('left_fast',     'Left-arm Fast'),
                        ('left_medium',   'Left-arm Medium'),
                        ('left_orthodox', 'Slow Left-arm Orthodox'),
                        ('left_chinaman', 'Left-arm Unorthodox (Chinaman)'),
                        ('none',          'None / Non-Bowler'),
                    ],
                    default='none', max_length=30,
                    verbose_name='bowling style',
                )),
                ('team_name_raw', models.CharField(blank=True, max_length=120, verbose_name='team name (text)')),
                ('short_bio',     models.TextField(blank=True, verbose_name='short bio')),
                ('status', models.CharField(
                    choices=[
                        ('pending',  'Pending'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected'),
                    ],
                    db_index=True, default='pending',
                    max_length=20, verbose_name='status',
                )),
                ('rejection_date', models.DateTimeField(blank=True, null=True, verbose_name='rejection date')),
                ('submitted_at',   models.DateTimeField(auto_now_add=True, verbose_name='submitted at')),
                ('updated_at',     models.DateTimeField(auto_now=True,     verbose_name='updated at')),
                ('team', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='player_requests',
                    to='teams.team',
                    verbose_name='team',
                )),
                ('approved_player', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='registration_request',
                    to='players.player',
                    verbose_name='approved player',
                )),
            ],
            options={
                'verbose_name':        'Player Registration Request',
                'verbose_name_plural': 'Player Registration Requests',
                'ordering':            ['-submitted_at'],
            },
        ),
        migrations.AddIndex(
            model_name='playerregistrationrequest',
            index=models.Index(fields=['status'],       name='players_req_status_idx'),
        ),
        migrations.AddIndex(
            model_name='playerregistrationrequest',
            index=models.Index(fields=['submitted_at'], name='players_req_submitted_idx'),
        ),
    ]
