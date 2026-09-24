from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_contactmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactmessage',
            name='mobile_number',
            field=models.CharField(default='', max_length=30, verbose_name='mobile number'),
        ),
    ]
