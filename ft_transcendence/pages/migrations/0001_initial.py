# Generated by Django 4.2.16 on 2024-09-04 12:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invite_type', models.IntegerField()),
                ('send_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='send_to', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sender_invite', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
