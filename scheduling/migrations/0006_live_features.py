from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0005_matchstats'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add 'live' to Match.status choices (no schema change needed - CharField)
        # Add PlayerMatchStats model
        migrations.CreateModel(
            name='PlayerMatchStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strikes', models.IntegerField(default=0, help_text='Successful attacks/strikes')),
                ('blocks', models.IntegerField(default=0, help_text='Successful blocks')),
                ('service_aces', models.IntegerField(default=0, help_text='Service aces')),
                ('errors', models.IntegerField(default=0, help_text='Unforced errors')),
                ('digs', models.IntegerField(default=0, help_text='Successful digs')),
                ('assists', models.IntegerField(default=0, help_text='Assists')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player_stats', to='scheduling.match')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='match_stats', to=settings.AUTH_USER_MODEL)),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_stats', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['player__username'],
                'unique_together': {('match', 'player')},
            },
        ),
        # Add SessionAttendance model
        migrations.CreateModel(
            name='SessionAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('present', 'Present'), ('absent', 'Absent'), ('excused', 'Excused')], default='absent', max_length=10)),
                ('recorded_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='scheduling.trainingsession')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to=settings.AUTH_USER_MODEL)),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_attendance', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['player__username'],
                'unique_together': {('session', 'player')},
            },
        ),
    ]
