from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_alter_customuser_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='otp_hash',
            field=models.CharField(
                blank=True,
                max_length=128,
                verbose_name='verification OTP hash',
            ),
        ),
    ]
