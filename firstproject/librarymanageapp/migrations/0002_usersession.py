# Generated by Django 4.1.7 on 2023-03-21 03:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sessions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('librarymanageapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(max_length=100, null=True)),
                ('session_maneger', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='sessions.session')),
                ('user_acc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]