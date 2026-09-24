import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_delete_cricketapisetting'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('full_name', models.CharField(max_length=120, verbose_name='full name')),
                ('email', models.EmailField(max_length=254, verbose_name='email address')),
                ('subject', models.CharField(max_length=200, verbose_name='subject')),
                ('message', models.TextField(verbose_name='message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('is_read', models.BooleanField(default=False, verbose_name='read')),
                ('is_replied', models.BooleanField(default=False, verbose_name='replied')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='deleted')),
            ],
            options={
                'verbose_name': 'Contact Message',
                'verbose_name_plural': 'Contact Messages',
                'ordering': ['-created_at'],
            },
        ),
    ]
