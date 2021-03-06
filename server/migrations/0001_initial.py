# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'', max_length=100, null=True)),
                ('info1', models.CharField(default=b'', max_length=100, null=True)),
                ('info2', models.CharField(default=b'', max_length=100, null=True)),
                ('info3', models.CharField(default=b'', max_length=100, null=True)),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 10, 2, 16, 15, 4, 619250))),
                ('user', models.ForeignKey(related_name='alerted', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(default=None, max_length=4000, null=True)),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 10, 2, 16, 15, 4, 612239))),
            ],
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_modified', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 10, 2, 16, 15, 4, 620347))),
                ('followed', models.ForeignKey(related_name='followed', to=settings.AUTH_USER_MODEL)),
                ('follower', models.ForeignKey(related_name='follower', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Info',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('top_posts', models.TextField(max_length=1000)),
                ('top_posts_date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(default=None, max_length=4000, null=True)),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 10, 2, 16, 15, 4, 614434))),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Paste',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(default=None, max_length=100000)),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 10, 2, 16, 15, 4, 622210))),
            ],
        ),
        migrations.CreateModel(
            name='Pin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 10, 2, 16, 15, 4, 613499))),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(default=None, max_length=4000, null=True)),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 10, 2, 16, 15, 4, 611203))),
                ('channel', models.ForeignKey(to='server.Channel')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PrivateMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 10, 2, 16, 15, 4, 615434))),
                ('message', models.TextField(default=None, max_length=4000, null=True)),
                ('hidden', models.BooleanField(default=False)),
                ('info1', models.CharField(default=b'', max_length=100, null=True)),
                ('info2', models.CharField(default=b'', max_length=100, null=True)),
                ('sender', models.ForeignKey(related_name='sender', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='receiver', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('theme_background', models.CharField(default=b'0', max_length=20)),
                ('theme_text', models.CharField(default=b'0', max_length=20)),
                ('theme_link', models.CharField(default=b'0', max_length=20)),
                ('theme_input_background', models.CharField(default=b'0', max_length=20)),
                ('theme_input_text', models.CharField(default=b'0', max_length=20)),
                ('theme_input_border', models.CharField(default=b'0', max_length=20)),
                ('theme_input_placeholder', models.CharField(default=b'0', max_length=20)),
                ('theme_scroll_background', models.CharField(default=b'0', max_length=20)),
                ('embed_option', models.CharField(default=b'embed', max_length=20)),
                ('last_alert_read', models.ForeignKey(to='server.Alert', null=True)),
                ('last_pm_read', models.ForeignKey(to='server.PrivateMessage', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Silenced',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('brat', models.ForeignKey(related_name='who_to_be_silenced', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='who_wants_silence', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Visited',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.CharField(default=b'', max_length=100)),
                ('count', models.IntegerField(default=0)),
                ('user', models.ForeignKey(related_name='user_visiting', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='pin',
            name='post',
            field=models.ForeignKey(to='server.Post'),
        ),
        migrations.AddField(
            model_name='pin',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conversation',
            name='last_message',
            field=models.ForeignKey(to='server.PrivateMessage'),
        ),
        migrations.AddField(
            model_name='conversation',
            name='user1',
            field=models.ForeignKey(related_name='user1', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conversation',
            name='user2',
            field=models.ForeignKey(related_name='user2', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(to='server.Post'),
        ),
        migrations.AddField(
            model_name='comment',
            name='reply',
            field=models.ForeignKey(default=None, to='server.Comment', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
