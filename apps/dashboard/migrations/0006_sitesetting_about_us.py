from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0005_contactmessage_mobile_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='about_us',
            field=models.TextField(blank=True, default='', verbose_name='about us description'),
        ),
    ]
