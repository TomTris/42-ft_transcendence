# Generated by Django 4.2.16 on 2024-09-06 20:23

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
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=200)),
                ('game_id', models.IntegerField(null=True)),
                ('send_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reciver_message', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sender_message', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BlockList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blocked', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='blocked', to=settings.AUTH_USER_MODEL)),
                ('blocker', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='blocker', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
