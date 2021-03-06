
import datetime
from django.db import models
from django.contrib.auth.models import User


class Channel(models.Model):
    name = models.CharField(max_length=200, unique=True)

class Post(models.Model):
    user = models.ForeignKey(User)
    channel = models.ForeignKey(Channel)
    content = models.TextField(max_length=4000, default=None, null=True)
    num_likes = models.IntegerField(default=0)
    num_comments = models.IntegerField(default=0)
    date = models.DateTimeField(default=datetime.datetime.now())
    date_modified = models.DateTimeField(default=datetime.datetime.now())
    date_bumped = models.DateTimeField(default=datetime.datetime.now())
    info = models.CharField(max_length=100, default='', null=True)

class Comment(models.Model):
    user = models.ForeignKey(User)
    post = models.ForeignKey(Post)
    content = models.TextField(max_length=4000, default=None, null=True)
    reply = models.ForeignKey('self', default=None, null=True)
    num_likes = models.IntegerField(default=0)
    date = models.DateTimeField(default=datetime.datetime.now())

class Pin(models.Model):
    user = models.ForeignKey(User)
    post = models.ForeignKey(Post)
    date = models.DateTimeField(default=datetime.datetime.now())

class PrivateMessage(models.Model):
    user = models.ForeignKey(User, related_name='receiver')
    sender = models.ForeignKey(User, related_name='sender')
    date = models.DateTimeField(default=datetime.datetime.now())
    message = models.TextField(max_length=4000, default=None, null=True)
    hidden = models.BooleanField(default=False)
    info = models.CharField(max_length=100, default='', null=True)

class Conversation(models.Model):
    user1 = models.ForeignKey(User, related_name='user1')
    user2 = models.ForeignKey(User, related_name='user2')
    last_message = models.ForeignKey(PrivateMessage)
    date_modified = models.DateTimeField()

class Alert(models.Model):
    type = models.CharField(max_length=100, default='', null=True)
    user = models.ForeignKey(User, related_name='alerted')
    user2 = models.ForeignKey(User, related_name='alert_user_2', null=True)
    post1 = models.ForeignKey(Post, related_name='post_1', null=True)
    post2 = models.ForeignKey(Post, related_name='post_2', null=True)
    comment1 = models.ForeignKey(Comment, related_name='comment_1', null=True)
    comment2 = models.ForeignKey(Comment, related_name='comment_2', null=True)
    date = models.DateTimeField(default=datetime.datetime.now())

class Follow(models.Model):
    followed = models.ForeignKey(User, related_name='followed')
    follower = models.ForeignKey(User, related_name='follower')
    date = models.DateTimeField(default=datetime.datetime.now())

class Visited(models.Model):
    user = models.ForeignKey(User, related_name='user_visiting')
    channel = models.CharField(max_length=100, default='')
    count = models.IntegerField(default=0)
    date = models.DateTimeField(default=datetime.datetime.now())

class Paste(models.Model):
    content = models.TextField(max_length=100000, default=None, null=False) 
    date = models.DateTimeField(default=datetime.datetime.now())

class Ban(models.Model):
    username = models.CharField(max_length=30)
    ip = models.CharField(max_length=50, default=0)
    exp_date = models.DateTimeField(default=datetime.datetime.now())

class CommentLike(models.Model):
    user = models.ForeignKey(User)
    comment = models.ForeignKey(Comment)
    date = models.DateTimeField(default=datetime.datetime.now())

class Subscription(models.Model):
    user = models.ForeignKey(User)
    channel = models.ForeignKey(Channel)
    date = models.DateTimeField(default=datetime.datetime.now())
    
class Profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    date_registered = models.DateTimeField(default=datetime.datetime.now())
    last_entrance = models.DateTimeField(default=datetime.datetime.now())
    theme_background = models.CharField(max_length=20, default='0')
    theme_text = models.CharField(max_length=20, default='0')
    theme_link = models.CharField(max_length=20, default='0')
    theme_input_background = models.CharField(max_length=20, default='0')
    theme_input_text = models.CharField(max_length=20, default='0')
    theme_input_border = models.CharField(max_length=20, default='0')
    theme_input_placeholder = models.CharField(max_length=20, default='0')
    theme_scroll_background = models.CharField(max_length=20, default='0')
    embed_option = models.CharField(max_length=20, default='embed')
    last_pm_read = models.IntegerField(default=0)
    last_alert_read = models.IntegerField(default=0)
    ip = models.CharField(max_length=50, default=0)