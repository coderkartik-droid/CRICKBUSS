from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='country',
            field=models.CharField(blank=True, max_length=80, verbose_name='country'),
        ),
        migrations.AddField(
            model_name='player',
            name='registration_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                ],
                db_index=True,
                default='approved',
                max_length=20,
                verbose_name='registration status',
            ),
        ),
        migrations.AddIndex(
            model_name='player',
            index=models.Index(fields=['registration_status'], name='players_pla_reg_sta_idx'),
        ),
    ]
