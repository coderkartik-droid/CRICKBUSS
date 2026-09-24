from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0002_player_registration_status_player_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='mobile_number',
            field=models.CharField(
                blank=True,
                max_length=20,
                verbose_name='mobile number',
            ),
        ),
        migrations.AddField(
            model_name='player',
            name='email_address',
            field=models.EmailField(
                blank=True,
                max_length=254,
                verbose_name='email address',
            ),
        ),
        migrations.AddField(
            model_name='player',
            name='full_address',
            field=models.TextField(
                blank=True,
                verbose_name='full address',
            ),
        ),
        migrations.AddField(
            model_name='player',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[
                    ('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other'),
                    ('prefer_not', 'Prefer not to say'),
                ],
                max_length=20,
                verbose_name='gender',
            ),
        ),
        migrations.AddField(
            model_name='player',
            name='state',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='state / province',
            ),
        ),
        migrations.AddField(
            model_name='player',
            name='city',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='city',
            ),
        ),
        migrations.AddField(
            model_name='player',
            name='cricket_experience',
            field=models.TextField(
                blank=True,
                verbose_name='cricket experience',
            ),
        ),
        migrations.AddField(
            model_name='player',
            name='preferred_position',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='preferred playing position',
            ),
        ),
    ]
