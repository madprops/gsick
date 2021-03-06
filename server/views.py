# encoding: utf-8

import pdb
import random
import re
import datetime
import string
import json
import itertools
from ipware.ip import get_ip
from unicodedata import normalize
from operator import attrgetter
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.context_processors import csrf
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core import serializers
from django.core.mail import send_mail
from django.utils.encoding import smart_str, smart_unicode
from django.db.models import Avg, Max, Min, Count, Q
from server.models import *
from server.magik import *

admin_list = ('madprops',)
forbidden_channels = ('top', 'new', 'chat', 'settings', 'alerts', 'posts', 'pins', 'random', 'stream')
banned_url = 'http://salmonofcapistrano.com/'

def create_c(request):
	c = {}
	c.update(csrf(request))
	return c

def main(request, mode='start', info=''):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/enter')
	p = get_profile(request.user)
	c = create_c(request)
	if mode == 'start':
		c['mode'] = 'new'
	else:
		c['mode'] = mode
	c['first_time'] = request.GET.get('first_time', 'no')
	c['info'] = info
	c['loggedin'] = 'yes'
	c['username'] = request.user.username
	c['background'] = p.theme_background
	c['text'] = p.theme_text
	c['link'] = p.theme_link
	c['input_background'] = p.theme_input_background
	c['input_text'] = p.theme_input_text
	c['input_border'] = p.theme_input_border
	c['input_placeholder'] = p.theme_input_placeholder
	c['scroll_background'] = p.theme_scroll_background
	c['embed_option'] = p.embed_option
	p.ip = get_ip(request)
	p.last_entrance = datetime.datetime.now()
	p.save()
	return render_to_response('base.html', c, context_instance=RequestContext(request))	

def enter(request):
	auth_logout(request)
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	if request.method == 'POST':
		if 'btnlogin' in request.POST:
			username = request.POST['username'].lower()
			password = request.POST['password']
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					auth_login(request, user)
					return HttpResponseRedirect('/')
			else:
				c = create_c(request)
				c['msg'] = 'wrong username or password'
				return render_to_response('enter.html', c, context_instance=RequestContext(request))
		if 'btnregister' in request.POST:
			status = error_register(request)
			if status != 'ok':
				c = {}
				c.update(csrf(request))
				c['msg'] = status
				return render_to_response('enter.html', c, context_instance=RequestContext(request))
			else:
				username = clean_username(request.POST['register_username']).lower()
				password = request.POST['register_password']
				user = User.objects.create_user(username, 'no@email.com', password)
				p = Profile(user=user)
				p.date_registered = datetime.datetime.now()
				p.save()
				user.backend='django.contrib.auth.backends.ModelBackend'
				auth_login(request, user)
				return HttpResponseRedirect('/?first_time=yes')
	else:
		c = create_c(request)
		return render_to_response('enter.html', c, context_instance=RequestContext(request))

def error_register(request):
	username = request.POST['register_username'].lower()
	password = request.POST['register_password']  
	answer = request.POST['register_answer'].lower()
	if answer not in ['1 hour', '1h', '1 h', 'one hour']:
		return 'wrong answer'
	if username.replace(" ", "") == "":
		return 'username is empty'
	if password.replace(" ", "") == "":
		return 'password is empty'
	if not clean_username(username):
		return 'username may only contain letters and numbers'
	if len(username) > 20:
		return 'username is too long'
	if len(password) > 50:
		return 'password is too long'
	try:
		User.objects.get(username=username)
		return 'username already exists'
	except:
		pass
	return 'ok'

@login_required
def settings(request):
	html = ''
	html = settings_to_html(request)
	data = {'html':html}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def chat(request):
	data = {}
	status = 'ok'
	username = ''
	posts = ''
	s = ''
	try:
		username = request.GET.get('username',0)
		peer = User.objects.get(username=username)
		username = peer.username
		posts = chat_to_html(request, get_chat_history(request, peer))
		p = get_profile(peer)
		if p.theme_background != '' and p.theme_background != 0 and p.theme_background != '0':
			data['has_theme'] = 'yes'
			data['background'] = p.theme_background
			data['text'] = p.theme_text
			data['link'] = p.theme_link
			data['input_background'] = p.theme_input_background
			data['input_text'] = p.theme_input_text
			data['input_border'] = p.theme_input_border
			data['input_placeholder'] = p.theme_input_placeholder
			data['scroll_background'] = p.theme_scroll_background
		else:
			data['has_theme'] = 'no'
		data['posts'] = posts
		data['username'] = username
		data['status'] = status
	except:
		data['status'] = 'error'
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def view_chat(request):
	data = ''
	status = 'error'
	posts = ''
	s = ''
	try:
		last = get_profile(request.user).last_pm_read
		posts = chat_to_html(request, get_chat_messages(request), 'chatall', last)
		status = 'ok'
	except:
		posts = ''
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_alerts(request):
	mode = request.GET['mode']
	if mode == 'all':
		alerts = Alert.objects.filter(user=request.user).order_by('-id')[:20]
	if mode == 'comments':
		alerts = Alert.objects.filter(user=request.user, type='comment').order_by('-id')[:20]
	if mode == 'replies':
		alerts = Alert.objects.filter(user=request.user, type='reply').order_by('-id')[:20]
	if mode == 'likes':
		alerts = Alert.objects.filter(Q(type='pin') | Q(type='comment_like'), user=request.user).order_by('-id')[:20]
	if mode == 'follows':
		alerts = Alert.objects.filter(user=request.user, type='follow').order_by('-id')[:20]
	if mode == 'mentions':
		alerts = Alert.objects.filter(Q(type='mention') | Q(type='mention_post'), user=request.user).order_by('-id')[:20]
	if mode == 'themes':
		alerts = Alert.objects.filter(user=request.user, type='theme').order_by('-id')[:20]
	return alerts

@login_required
def get_more_alerts(request):
	id = request.GET['id']
	mode = request.GET['mode']
	if mode == 'all':
		alerts = Alert.objects.filter(user=request.user, id__lt=id).order_by('-id')[:20]
	if mode == 'comments':
		alerts = Alert.objects.filter(user=request.user, type='comment', id__lt=id).order_by('-id')[:20]
	if mode == 'replies':
		alerts = Alert.objects.filter(user=request.user, type='reply', id__lt=id).order_by('-id')[:20]
	if mode == 'likes':
		alerts = Alert.objects.filter(Q(type='pin') | Q(type='comment_like'), user=request.user, id__lt=id).order_by('-id')[:20]
	if mode == 'follows':
		alerts = Alert.objects.filter(user=request.user, type='follow', id__lt=id).order_by('-id')[:20]
	if mode == 'mentions':
		alerts = Alert.objects.filter(Q(type='mention') | Q(type='mention_post'), user=request.user, id__lt=id).order_by('-id')[:20]
	if mode == 'themes':
		alerts = Alert.objects.filter(user=request.user, type='theme', id__lt=id).order_by('-id')[:20]
	return alerts

@login_required
def view_alerts(request):
	data = ''
	status = 'error'
	alerts = ''
	xalerts = get_alerts(request)
	if len(xalerts) > 0:
		p = get_profile(request.user)
		alerts = alerts_to_html(request, xalerts, p.last_alert_read)
		lalerts = list(xalerts)
		if request.GET['mode'] == 'all':
			p.last_alert_read = lalerts[0].id
			p.save()
		status = 'ok'
	data = {'alerts':alerts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_chat_history(request, peer, last_pm_id=None):
	if last_pm_id:
		pmr = PrivateMessage.objects.filter(user=request.user, sender=peer, id__lt=last_pm_id)
		pms = PrivateMessage.objects.filter(sender=request.user, user=peer, id__lt=last_pm_id)
		pmx = sorted(itertools.chain(pmr, pms), key=attrgetter('id'), reverse=True)[:20]
	else:
		pmr = PrivateMessage.objects.filter(user=request.user, sender=peer)
		pms = PrivateMessage.objects.filter(sender=request.user, user=peer)
		pmx = sorted(itertools.chain(pmr, pms), key=attrgetter('id'), reverse=True)[:20]
	return pmx

@login_required
def refresh_channel(request):
	id = request.GET.get('id',0)
	channel_name = request.GET.get('channel_name',0)
	channel = Channel.objects.get(name=channel_name)
	posts = Post.objects.filter(channel=channel, id__gt=id).order_by('-id')
	posts = posts_to_html(request,posts)
	status = 'ok'
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def refresh_user(request):
	id = request.GET.get('id',0)
	username = request.GET.get('username',0)
	if id == 0:
		user = User.objects.get(username=username)
		posts = Post.objects.filter(user=user, id__gt=id).order_by('-id')
	else:
		post = Post.objects.get(id=id)
		posts = Post.objects.filter(user=post.user, id__gt=id).order_by('-id')
	posts = posts_to_html(request,posts,'user')
	status = 'ok'
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def refresh_chat(request):
	data = ''
	status = ''
	username = request.GET['username']
	first_chat_id = request.GET.get('first_chat_id',0)
	peer = User.objects.get(username=username)
	pmr = PrivateMessage.objects.filter(user=request.user, sender=peer, id__gt=first_chat_id)
	pms = PrivateMessage.objects.filter(sender=request.user, user=peer, id__gt=first_chat_id)
	pmx = sorted(itertools.chain(pmr, pms), key=attrgetter('date'), reverse=True)
	p = get_profile(request.user)
	last_pm_read = p.last_pm_read
	for x in pmr:
		if x.id > last_pm_read:
			last_pm_read = x.id
	p.last_pm_read = last_pm_read
	p.save()
	posts = chat_to_html(request, pmx)
	status = 'ok'
	data = {'posts':posts, 'username':username, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def refresh_chatall(request):
	data = ''
	status = ''
	first_chat_id = request.GET.get('first_chat_id', 0)
	original_last_chatall_id = request.GET['original_last_chatall_id']
	convs = Conversation.objects.filter(Q(user1=request.user) | Q(user2=request.user), last_message_id__gt=first_chat_id).order_by('-date_modified')[:20]
	msgs = []
	for conv in convs:
		msgs.append(conv.last_message)
	if len(msgs) > 0:
		p = get_profile(request.user)
		p.last_pm_read = msgs[0].id
		p.save()
	messages = chat_to_html(request, msgs, 'chatall', original_last_chatall_id)
	status = 'ok'
	data = {'messages':messages, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

def find_mentions(request, input):
	l = []
	words = input.split()
	for w in words:
		if w.startswith('@'):
			w = w[1:].replace(',', '').replace('.', '').lower()
			if "'" in w:
				w = w.split("'")[0]
			l.append(w)
	return l

def linkify_mentions(text):
	p = re.compile(ur'(?:(?<=^)|(?<=\s))@([a-z0-9]+\b)')
	subst = "<span class='mention_link' onclick='change_user(\"" + r"\1" + "\"); return false'>@" + r"\1" + "</span>"
	result = re.sub(p, subst, text)
	return result

@login_required
def post_comment(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	id = request.POST.get('id', 0)
	content = stripper(request.POST.get('content', 0).strip())
	status = error_comment(request,content,id)
	cname = ''
	if status == 'ok':
		post = Post.objects.get(id=id)
		cname = post.channel.name
		comment = Comment(user=request.user, content=content, date=datetime.datetime.now(), post=post)
		comment.save()
		post.date_modified = datetime.datetime.now()
		post.num_comments += 1
		if post.num_comments < 101:
			post.date_bumped = post.date_modified
		post.save()
		mentions = find_mentions(request, content)
		for m in mentions:
			try:
				auser = User.objects.get(username=m)
				alert = Alert(user=auser, type='mention', user2=request.user, post1=post, comment1=comment, date=datetime.datetime.now())
				alert.save()
			except:
				continue
		if post.user != request.user:
			if post.user.username not in mentions:
				alert = Alert(user=post.user, type='comment', user2=request.user, post1=post, comment1=comment, date=datetime.datetime.now())
				alert.save()
	data = {'status':status, 'cname':cname}
	return HttpResponse(json.dumps(data), content_type="application/json")	

def error_comment(request, content, id):
	post = Post.objects.get(id=id)
	if content == '':
		return 'empty'
	if len(content) > 4000:
		return 'toobig'
	if Comment.objects.filter(user=request.user, date__gt=datetime.datetime.now() - datetime.timedelta(minutes=10)).count() >= 20:
		return 'toomuch'
	return 'ok'

@login_required
def edit_comment(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	id = request.POST['id']
	content = stripper(request.POST['content'].strip())
	comment = Comment.objects.get(id=id)
	try:
		CommentLike.objects.filter(comment=comment)[0]
		status = 'liked'
		data = {'status':status, 'content':content}
		return HttpResponse(json.dumps(data), content_type="application/json")
	except:
		pass
	try:
		Comment.objects.filter(reply=comment)[0]
		status = 'replied'
		data = {'status':status, 'content':content}
		return HttpResponse(json.dumps(data), content_type="application/json")
	except:
		pass
	if len(content) < 1:
		status = 'empty'
	elif len(content) > 4000:
		status = 'toolong'
	else:
		comment.content = content
		comment.save()
		content = linkify_mentions(urlize_inline(comment.content))
		mentions = find_mentions(request, comment.content)
		mentioned = Alert.objects.filter(type='mention', user2=request.user, post1=comment.post, comment1=comment)
		for a in mentioned:
			if a.user not in mentions:
				a.delete()
		for m in mentions:
			try:
				auser = User.objects.get(username=m)
				try:
					Alert.objects.get(user=auser, type='mention', user2=request.user, post1=comment.post, comment1=comment)
				except:
					alert = Alert(user=auser, type='mention', user2=request.user, post1=comment.post, comment1=comment, date=datetime.datetime.now())
					alert.save()
			except:
				continue
		status = 'ok'
	data = {'status':status, 'content':content}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def edit_post(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	id = request.POST['id']
	cname = request.POST['cname']
	if cname != '--noedit--':
		cname = slugify(cname)
	content = correctify(stripper(request.POST['content']))
	post = Post.objects.get(id=id)
	try:
		Pin.objects.filter(post=post)[0]
		status = 'liked'
		data = {'status':status, 'content':content}
		return HttpResponse(json.dumps(data), content_type="application/json")
	except:
		pass
	try:
		Comment.objects.filter(post=post)[0]
		status = 'commented'
		data = {'status':status, 'content':content}
		return HttpResponse(json.dumps(data), content_type="application/json")
	except:
		pass
	if len(cname) < 1:
		status = 'empty_cname'
	elif cname in forbidden_channels:
		status = 'forbidden_channel'
	elif len(content) < 1:
		status = 'empty'
	elif len(content) > 4000:
		status = 'toolong'
	else:
		if cname != '--noedit--':
			try:
				channel = Channel.objects.get(name=cname)
			except:
				channel = Channel(name=cname)
				channel.save()
			post.channel = channel
		post.content = content
		post.info = gather_info(content)
		post.save()
		eo = get_embed_option(request.user)
		if eo == 'embed':
			content = linkify_mentions(ultralize(post.content, info=post.info))
		else:
			content = linkify_mentions(urlize(post.content))
		mentions = find_mentions(request, post.content)
		mentioned = Alert.objects.filter(type='mention_post', user2=request.user, post1=post)
		for a in mentioned:
			if a.user not in mentions:
				a.delete()
		for m in mentions:
			try:
				auser = User.objects.get(username=m)
				try:
					Alert.objects.get(user=auser, type='mention_post', user2=request.user, post1=post)
				except:
					alert = Alert(user=auser, type='mention_post', user2=request.user, post1=post, date=datetime.datetime.now())
					alert.save()
			except:
				continue
		status = 'ok'
	if cname != '--noedit--':
		cname_html = "<span class='post_cname_holder'> <a onClick='goto(\"" + cname + "\");return false;' href=\"#\"><span class='post_cname'>" + cname + "</span></a></span>"
	else:
		cname_html = ''
	data = {'status':status, 'content':content, 'cname_html':cname_html}
	return HttpResponse(json.dumps(data), content_type="application/json")

def get_post_content(request):
	id = request.GET['id']
	post = Post.objects.get(id=id)
	status = 'ok'
	data = {'status':status, 'content':post.content}
	return HttpResponse(json.dumps(data), content_type="application/json")

def get_comment_content(request):
	id = request.GET['id']
	comment = Comment.objects.get(id=id)
	status = 'ok'
	data = {'status':status, 'content':comment.content}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def open_post(request, id=None):
	if not id:
		id = request.GET.get('id',0)
	post = Post.objects.get(id=id)
	cname = post.channel.name
	comments = Comment.objects.filter(post=post).order_by('id')[:50]
	post = post_to_html(request, post)
	comments = comments_to_html(request,comments)
	status = 'ok'
	data = {'post':post, 'comments':comments, 'status':status, 'cname':cname}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def top_posts(request):
	posts = ''
	status = ''
	try:
		posts = get_top_posts(request)
		posts = posts_to_html(request, posts, 'new')
		status = 'ok'
	except:
		pass
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_top_posts(request):
	posts = get_more_top_posts(request)
	posts = posts_to_html(request, posts, 'new')
	status = 'ok'
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required		
def get_top_posts(request):
	# as the site grows bigger num_likes and days must change
	num_likes = 1
	days = 10
	mode = request.GET['mode']
	if mode == 'all':
		posts = Post.objects.filter(num_likes__gte=num_likes, date__gte=(datetime.datetime.now() - datetime.timedelta(days=days))).order_by('-num_likes', '-date')[:10]
	if mode == 'subscriptions':
		channels = get_sub_channels(request)
		posts = Post.objects.filter(channel__in=channels, num_likes__gte=num_likes, date__gte=(datetime.datetime.now() - datetime.timedelta(days=days))).order_by('-num_likes', '-date')[:10]
	return posts

@login_required
def get_more_top_posts(request):
	# as the site grows bigger num_likes and days must change
	num_likes = 1
	days = 10
	mode = request.GET['mode']
	ids = request.GET.get('ids', 0).split(',')
	if mode == 'all':
		posts = Post.objects.filter(num_likes__gte=num_likes, date__gte=(datetime.datetime.now() - datetime.timedelta(days=days))).exclude(id__in=ids).order_by('-num_likes', '-date')[:10]
	if mode == 'subscriptions':
		channels = get_sub_channels(request)
		posts = Post.objects.filter(channel__in=channels, num_likes__gte=num_likes, date__gte=(datetime.datetime.now() - datetime.timedelta(days=days))).exclude(id__in=ids).order_by('-num_likes', '-date')[:10]
	return posts

def get_channel_posts_by_user(request, user, channel):
	posts = Post.objects.filter(user=user, channel=channel).order_by('-id')[:10]
	return posts

@login_required
def user_on_channel(request):
	data = {}
	try:
		input = request.GET['input']
		words = input.split()
		uname = words[0]
		cname = words[2]
		user = User.objects.get(username=uname)
		channel = Channel.objects.get(name=cname)
		posts = get_channel_posts_by_user(request, user, channel)
		posts = posts_to_html(request, posts)
		status = 'ok'
		p = get_profile(user)
		if p.theme_background != '' and p.theme_background != 0 and p.theme_background != '0':
			data['has_theme'] = 'yes'
			data['background'] = p.theme_background
			data['text'] = p.theme_text
			data['link'] = p.theme_link
			data['input_background'] = p.theme_input_background
			data['input_text'] = p.theme_input_text
			data['input_border'] = p.theme_input_border
			data['input_placeholder'] = p.theme_input_placeholder
			data['scroll_background'] = p.theme_scroll_background
		else:
			data['has_theme'] = 'no'
		data['posts'] = posts
		data['status'] = status
		data['uname'] = uname
		data['cname'] = cname
	except:
		data['status'] = 'error'
		pass
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def new_posts(request):
	posts = ''
	posts = get_new_posts(request)
	posts = posts_to_html(request, posts, 'new')
	status = 'ok'
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_new(request):
	posts = get_more_new_posts(request)
	posts = posts_to_html(request, posts, 'new')
	status = 'ok'
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_alerts(request):
	original_last_alerts_id = request.GET['original_last_alerts_id']
	xalerts = get_more_alerts(request)
	alerts = alerts_to_html(request, xalerts, original_last_alerts_id)
	status = 'ok'
	data = {'alerts':alerts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_comments(request):
	comments = ''
	status = ''
	id = request.GET.get('id', 0)
	last_id = request.GET.get('last_id', 0)
	post = Post.objects.get(id=id)
	comments = Comment.objects.filter(post=post, id__gt=last_id).order_by('id')[:50]
	comments = comments_to_html(request, comments)
	status = 'ok'
	data = {'comments':comments, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def reply_to_comment(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	status = 'error'
	comment_id = request.POST['comment_id']
	content = stripper(request.POST['msg'].strip())
	comment_replied = Comment.objects.get(id=comment_id)
	status = error_comment(request, content, comment_replied.post.id)
	if status == 'ok':
		post = comment_replied.post
		comment = Comment(user=request.user, content=content, post=post, reply=comment_replied, date=datetime.datetime.now())
		comment.save()
		post.date_modified = datetime.datetime.now()
		post.num_comments += 1
		if post.num_comments < 101:
			post.date_bumped = post.date_modified
		post.save()
		if request.user != comment_replied.user:
			alert = Alert(user=comment_replied.user, type='reply', user2=request.user, post1=post, comment1=comment, date=datetime.datetime.now())
			alert.save()
		status = 'ok'
	data = {'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_sub_channels(request):
	subs = Subscription.objects.filter(user=request.user)
	channels = []
	for s in subs:
		channels.append(s.channel)
	return channels

@login_required
def get_new_posts(request):
	mode = request.GET['mode']
	if mode == 'all':
		posts = Post.objects.all().order_by('-id')[:10]
	if mode == 'subscriptions':
		channels = get_sub_channels(request)
		posts = Post.objects.filter(channel__in=channels).order_by('-id')[:10]
	return posts

@login_required
def get_more_new_posts(request):
	mode = request.GET['mode']
	id = request.GET.get('id', 0)
	if mode == 'all':
		posts = Post.objects.filter(id__lt=id).order_by('-id')[:10]
	if mode == 'subscriptions':
		channels = get_sub_channels(request)
		posts = Post.objects.filter(channel__in=channels, id__lt=id).order_by('-id')[:10]
	return posts

def get_users():
	return User.objects.all()

@login_required
def get_user(request):
	uname = request.GET['uname']
	post = ''
	data = {}
	status = 'ok'
	try:
		user = User.objects.get(username=uname)
	except:
		status = 'doesntexist'
		data = {'status':status, 'uname': '', 'posts':'', 'following': ''}
		return HttpResponse(json.dumps(data), content_type="application/json")
	posts = get_user_posts(request, user)
	posts = posts_to_html(request,posts,'user')
	try:
		f = Follow.objects.get(followed=User.objects.get(username=uname), follower=request.user)
		following = 'unfollow'
	except:
		following = 'follow'
	p = get_profile(user)
	if p.theme_background != '' and p.theme_background != 0 and p.theme_background != '0':
		data['has_theme'] = 'yes'
		data['background'] = p.theme_background
		data['text'] = p.theme_text
		data['link'] = p.theme_link
		data['input_background'] = p.theme_input_background
		data['input_text'] = p.theme_input_text
		data['input_border'] = p.theme_input_border
		data['input_placeholder'] = p.theme_input_placeholder
		data['scroll_background'] = p.theme_scroll_background
	else:
		data['has_theme'] = 'no'
	data['status'] = status
	data['uname'] = user.username
	data['posts'] = posts
	data['following'] = following
	return HttpResponse(json.dumps(data), content_type="application/json")

def get_user_posts(request, user):
	posts = Post.objects.filter(user=user).order_by('-id')[:10]
	return posts

@login_required
def toggle_follow(request):
	status = ''
	if request.user.is_authenticated():
		followed = User.objects.get(username=request.POST['uname'])
		try:
			f = Follow.objects.get(followed=followed, follower=request.user)
			f.delete()
			status = 'unfollowed'
		except:
			if Follow.objects.filter(follower=request.user, date__gt=datetime.datetime.now() - datetime.timedelta(minutes=10)).count() >= 10:
				data = {'status':'toomuch'}
				return HttpResponse(json.dumps(data), content_type="application/json")
			f = Follow(followed=followed, follower=request.user, date=datetime.datetime.now())
			f.save()
			try:
				a = Alert.objects.get(user=followed, type='follow', user2=request.user)
			except:
				alert = Alert(user=followed, type='follow', user2=request.user, date=datetime.datetime.now())
				alert.save()
			status = 'followed'
	data = {'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def toggle_subscribe(request):
	if Subscription.objects.filter(user=request.user, date__gt=datetime.datetime.now() - datetime.timedelta(minutes=10)).count() >= 10:
		data = {'status':'toomuch'}
		return HttpResponse(json.dumps(data), content_type="application/json")
	cname = request.POST['cname']
	try:
		channel = Channel.objects.get(name=cname)
	except:
		channel = Channel(name=cname)
		channel.save()
	try:
		sub = Subscription.objects.get(user=request.user, channel=channel)
		sub.delete()
		action = 'subscribe'
	except:
		sub = Subscription(user=request.user, channel=channel, date=datetime.datetime.now())
		sub.save()
		action = 'unsubscribe'
	data = {'status':'ok', 'action':action}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_stream(request):
	posts = ''
	if request.user.is_authenticated():
		followed = []
		for f in Follow.objects.filter(follower=request.user):
			followed.append(f.followed)
		posts = Post.objects.filter(user__in=followed).order_by('-date_bumped')[:10]
		posts = posts_to_html(request, posts, 'stream')
	if posts == '':
		posts = '<center>follow people to see their posts here</center>'
	data = {'posts':posts}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_stream(request):
	posts = ''
	status = ''
	try:
		ids = request.GET.get('ids', 0).split(',')
		followed = []
		for f in Follow.objects.filter(follower=request.user):
			followed.append(f.followed)
		posts = Post.objects.filter(user__in=followed).exclude(id__in=ids).order_by('-date_bumped')[:10]
		posts = posts_to_html(request, posts, 'stream')
		status = 'ok'
	except:
		pass
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")
	
def error_channel(cname):
	if cname.replace(" ","") == "":
		return True
	if len(cname) > 111:
		return True
	return False

@login_required
def check_new_pms(request):
	status = 'no'
	id = ''
	uname = ''
	num = 0
	p = get_profile(request.user)
	try:
		last_pm = PrivateMessage.objects.filter(user=request.user).order_by('-id')[0]
		num = PrivateMessage.objects.filter(user=request.user, id__gt=p.last_pm_read).order_by('-id').count()
		if last_pm.id > p.last_pm_read:
			status = 'yes'
			id = last_pm.id
			uname = last_pm.sender.username
	except:
		pass
	data = {'status': status, 'id':id, 'uname':uname, 'num':num}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def check_new_alerts(request):
	status = 'no'
	id = ''
	uname = ''
	num = 0
	try:
		p = get_profile(request.user)
		last_alert = Alert.objects.filter(user=request.user).order_by('-id')[0]
		num = Alert.objects.filter(user=request.user, id__gt=p.last_alert_read).order_by('-id').count()
		if last_alert.id > p.last_alert_read:
			status = 'yes'
			id = last_alert.id
	except:
		pass
	data = {'status': status, 'id':id, 'num':num}
	return HttpResponse(json.dumps(data), content_type="application/json")

def remove_duplicate_senders(request, pmr, welcome=True):
	l = []
	a = False
	for p in pmr:
		a = True
		if welcome:
			if p.sender.username in ['note']:
				l.append(p)
				continue
		else:
			if p.sender.username in ['note']:
				l.append(p)
				continue	
		for px in l:
			if (p.sender.username == px.sender.username and p.sender.username != request.user.username) or (p.sender.username == request.user.username and p.user == px.user):
				a = False
				break
		if a:
			l.append(p)
	return l

def get_senders_list(request, l):
	bl = []
	for x in l:
		u = x.sender.username
		if u in (['note'] + bl):
			continue
		else:
			bl.append(u)
	return bl

def get_receivers_list(request, l):
	bl = []
	for x in l:
		u = x.user.username
		if u in ([request.user.username,''] + bl):
			continue
		else:
			bl.append(u)
	return bl

def get_chat_messages(request, last_pm_id=None):
	if last_pm_id != None:
		convs = Conversation.objects.filter(Q(user1=request.user) | Q(user2=request.user), last_message_id__lt=last_pm_id).order_by('-date_modified')[:20]
	else:
		convs = Conversation.objects.filter(Q(user1=request.user) | Q(user2=request.user)).order_by('-date_modified')[:20]
	msgs = []
	for conv in convs:
		msgs.append(conv.last_message)
	if len(msgs) > 0:
		p = get_profile(request.user)
		p.last_pm_read = msgs[0].id
		p.save()
	return msgs

@login_required
def post_to_channel(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	data = ''
	post = ''
	status = ''
	id = ''
	status = error_post(request)
	if status == 'ok':
		cname = request.POST['channel'].lower()
		cname = request.POST['channel'].replace('_', '')
		try:
			channel = Channel.objects.get(name=cname)
		except:
			channel = Channel(name=cname)
			channel.save()
		content = correctify(stripper(request.POST['content']))
		info = gather_info(content)
		post = Post(content=content, channel=channel, user=request.user, date=datetime.datetime.now(), date_modified=datetime.datetime.now(), date_bumped=datetime.datetime.now(), info=info)
		post.save()
		id = post.id
		mentions = find_mentions(request, content)
		for m in mentions:
			try:
				auser = User.objects.get(username=m)
				alert = Alert(user=auser, type='mention_post', user2=request.user, post1=post, date=datetime.datetime.now())
				alert.save()
			except:
				continue
	data = {'status':status, 'id':id}
	return HttpResponse(json.dumps(data), content_type="application/json") 

def error_post(request):
	cname = request.POST['channel'].lower()
	cname = request.POST['channel'].replace('_', '')
	content = correctify(stripper(request.POST['content']))
	if cname in forbidden_channels:
		return 'forbiddenchannel'
	if content == "":
		return 'empty'
	if len(content) > 4000:
		return 'toobig'
	if Post.objects.filter(user=request.user, date__gt=datetime.datetime.now() - datetime.timedelta(minutes=10)).count() >= 5:
		return 'toomuch'
	return 'ok'

@login_required
def send_message(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	data = ''
	username = ''
	status = ''
	try:
		message = correctify(stripper(request.POST['msg']))
		receiver_username = request.POST['receiver']
	except:
		return HttpResponse(data)
	status = error_message(request, receiver_username, message)
	if status =='ok':
		receiver = User.objects.get(username=receiver_username)
		info = gather_info(message)
		pm = PrivateMessage(user=receiver, sender=request.user, date=datetime.datetime.now(), message=message, info=info)
		pm.save()
		if receiver_username < request.user.username:
			user1 = receiver;
			user2 = request.user
		else:
			user1 = request.user
			user2 = receiver
		try:
			conv = Conversation.objects.get(user1=user1, user2=user2)
			conv.last_message = pm
			conv.date_modified = datetime.datetime.now()
			conv.save()
		except:
			conv = Conversation(user1=user1, user2=user2, last_message=pm, date_modified=datetime.datetime.now())
			conv.save()
	data = {'username':receiver_username, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json") 
	
def error_message(request, receiver_username, message):
	not_allowed = ['root', 'global']
	if not request.user.is_authenticated():
		return 'nologin'
	if message.replace(" ", "") == "":
		return 'empty'
	if len(message) > 4000:
		return 'toobig'
	if receiver_username == "":
		return 'empty'
	if message == "":
		return 'empty'
	try:
		User.objects.get(username=receiver_username)
	except:
		return 'noreceiver'
	if receiver_username == request.user.username:
		return 'sameuser'
	if receiver_username in not_allowed:
		return 'notallowed'
	if PrivateMessage.objects.filter(sender=request.user, date__gt=datetime.datetime.now() - datetime.timedelta(minutes=10)).count() >= 30:
		return 'toomuch'
	return 'ok'

def get_inbox_match(content):
	match = re.search('^@([^ ]+)\s(.*)', content)
	return match

def get_new_pms(request):
	sender = request.GET['sender']
	pmu = User.objects.get(username=sender)
	pms = PrivateMessage.objects.filter(user=request.user, sender=pmu, read=False)
	for pm in pms:
		if pm.user == request.user and not pm.read:
			pm.read = True
			pm.save()
	if pms:
		return HttpResponse(pm_posts_to_html(request, pms))
	else:
		return HttpResponse()

def logout(request):
	data = ''
	auth_logout(request)
	return HttpResponse(json.dumps(data), content_type="application/json")

def get_first_channel_post(request, cname):
	ch = Channel.objects.get(name=cname)
	post = Post.objects.filter(channel=ch).order_by('-date')[0]
	return posts_to_html(request, post)
	
def get_first_channel_post_raw(request, cname):
	ch = Channel.objects.get(name=cname)
	post = Post.objects.filter(channel=ch).order_by('-date')[0]
	return post

def random_post(request):
	post = Post.objects.all().order_by('?')[0]
	return open_post(request, id=post.id)

def random_channel(request):
	current = request.GET.get('current',0)
	while True:		
		cname = random_channel_name()
		if cname != current:
			break
	return get_channel(request, cname)

def random_channel_name():
	while True:
		random = Channel.objects.order_by('?')[0].name
		if random not in forbidden_channels:
			break
	return random

def get_post(idPost):
	return Post.objects.get(id=idPost)

def show_user_on_channel(request, uname, cname):
	return main(request, mode='user_on_channel', info=uname +' on ' + cname)

def show_pins(request, uname):
	return main(request, mode='pins', info=uname)

def show_alerts(request):
	return main(request, mode='alerts')

def show_random(request):
	return main(request, mode='random')

def show_stream(request):
	return main(request, mode='stream')

def show_channel(request, channel):
	return main(request, mode='channel', info=channel)

def show_user(request, id):
	return main(request, mode='user', info=id)

def show_new(request):
	return main(request, mode='new')

def show_chat(request, uname):
	return main(request, mode='chat', info=uname)

def show_chatall(request):
	return main(request, mode='chatall')

def show_help(request):
	return main(request, mode='help')

def show_settings(request):
	return main(request, mode='settings')

def show_post(request, id):
	return main(request, mode='post', info=id)

def show_top(request):
	return main(request, mode='top')

@login_required
def show_last_comments(request):
	id = request.GET.get('id', 0)
	post = Post.objects.get(id=id)
	cname = post.channel.name
	comments = Comment.objects.filter(post=post).order_by('-id')[:50]
	length = comments.count()
	comments = reversed(list(comments))
	c = comments_to_html(request,comments)
	p = "<input type=\"hidden\" value=\"" + str(post.id) + "\" class=\"post_id\">"
	if length < 50:
		p = post_to_html(request,post)
	comments = p + c
	data = {'comments':comments,'cname':cname}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def show_older_comments(request):
	id = request.GET.get('id', 0)
	post_visible = int(request.GET['post_visible'])
	comment = Comment.objects.get(id=id)
	comments = Comment.objects.filter(post=comment.post, id__lt=id).order_by('-id')[:50]
	length = comments.count()
	comments = reversed(list(comments))
	c = comments_to_html(request, comments)
	p = "<input type=\"hidden\" value=\"" + str(comment.post.id) + "\" class=\"post_id\">"
	if length < 50 and post_visible == 0:
		p = post_to_html(request, comment.post)
	comments = p + c
	data = {'comments':comments}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def pin_post(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	status = ''
	id = request.POST.get('id', 0)
	post = Post.objects.get(id=id)
	if post.user == request.user:
		data = {'status':'sameuser'}
		return HttpResponse(json.dumps(data), content_type="application/json")
	if Pin.objects.filter(user=request.user, date__gt=datetime.datetime.now() - datetime.timedelta(minutes=10)).count() >= 30:
		data = {'status':'toomuch'}
		return HttpResponse(json.dumps(data), content_type="application/json")
	try:
		pin = Pin.objects.get(user=request.user, post=post)
	except:
		pin = Pin(user=request.user, post=post, date=datetime.datetime.now())
		pin.save()
		post.num_likes += 1
		post.save()
		alert = Alert(user=post.user, type='pin', user2=request.user, post1=post, date=datetime.datetime.now())
		alert.save()
	num_pins = post.num_likes
	status = 'ok'
	data = {'status':status, 'num_pins':num_pins}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_pins(request):
	status = ''
	uname = ''
	try:
		uname = request.GET['uname']
		user = User.objects.get(username=uname)
		pins = Pin.objects.filter(user=user).order_by('-id')[:10]
		posts = []
		for p in pins:
			posts.append(p.post)
		pins = posts_to_html(request, posts, 'new')
		status = 'ok'
		data = {}
		p = get_profile(user)
		if p.theme_background != '' and p.theme_background != 0 and p.theme_background != '0':
			data['has_theme'] = 'yes'
			data['background'] = p.theme_background
			data['text'] = p.theme_text
			data['link'] = p.theme_link
			data['input_background'] = p.theme_input_background
			data['input_text'] = p.theme_input_text
			data['input_border'] = p.theme_input_border
			data['input_placeholder'] = p.theme_input_placeholder
			data['scroll_background'] = p.theme_scroll_background
		else:
			data['has_theme'] = 'no'
		data['status'] = status
		data['pins'] = pins 
		data['uname'] = uname 
		return HttpResponse(json.dumps(data), content_type="application/json")
	except:
		data = {}
		data['status'] = 'error'
		return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def like_comment(request):
	id = request.POST['id']
	comment = Comment.objects.get(id=id)
	if comment.user == request.user:
		data = {'status':'sameuser'}
		return HttpResponse(json.dumps(data), content_type="application/json")
	if CommentLike.objects.filter(user=request.user, date__gt=datetime.datetime.now() - datetime.timedelta(minutes=10)).count() >= 30:
		data = {'status':'toomuch'}
		return HttpResponse(json.dumps(data), content_type="application/json")
	try:
		CommentLike.objects.get(comment=comment, user=request.user)
	except:	
		cl = CommentLike(comment=comment, user=request.user, date=datetime.datetime.now())
		cl.save()
		comment.num_likes += 1
		comment.save()
		alert = Alert(user=comment.user, type='comment_like', user2=request.user, comment1=comment, date=datetime.datetime.now())
		alert.save()
	num_likes = comment.num_likes
	status = 'ok'
	data = {'status':status, 'num_likes':num_likes}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_post_likes(request):
	id = request.GET['id']
	post = Post.objects.get(id=id)
	likes = Pin.objects.filter(post=post).order_by('date')[:100]
	likes = likes_to_html(likes)
	status = 'ok'
	data = {'status':status, 'likes':likes}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_comment_likes(request):
	id = request.GET['id']
	comment = Comment.objects.get(id=id)
	likes = CommentLike.objects.filter(comment=comment).order_by('date')[:100]
	likes = likes_to_html(likes)
	status = 'ok'
	data = {'status':status, 'likes':likes}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_quote(request):
	id = request.GET['id']
	reply = int(request.GET['reply'])
	c = Comment.objects.get(id=id)
	html = "<a class='info_link' onClick='change_user(\"" + c.user.username + "\");hide_overlay();return false;' href=\"#\">" + c.user.username + "</a>"
	if reply == 1:
		html += "<a class='info_link' onClick='reply_to("+str(c.id)+");hide_overlay();return false;'href='#' style='float:right'>reply</a>"
	html += "<time datetime='" + c.date.isoformat()+"-00:00" + "' class='timeago date'>"+ str(radtime(c.date)) +"</time>"
	html += "<span class='info_link'>" + linkify_mentions(urlize_inline(c.content)) + "</span>"
	data = {'html':html}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_welcome(request):
	welcome = welcome_to_html()
	data = {'status':'ok', 'welcome':welcome}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def open_new_post(request):
	status = ''
	post = ''
	cname = ''
	arrows = ''
	try:
		post_id = request.GET['post_id']
		post = Post.objects.filter(id=post_id)[0]
		arrows = get_new_arrows(request, post)
		cname = 'new'
		post = posts_to_html(request, post, 'new')
		status = 'ok'
	except:
		pass
	data = {'post':post, 'cname':cname, 'arrows':arrows, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def open_top_post(request):
	status = ''
	post = ''
	cname = ''
	arrows = ''
	try:
		post_id = request.GET['post_id']
		post = Post.objects.filter(id=post_id)[0]
		arrows = get_top_arrows(request,post)
		cname = 'top'
		post = posts_to_html(request,post,'top')
		status = 'ok'
	except:
		pass
	data = {'post':post, 'cname':cname, 'arrows':arrows, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def open_user_post(request):
	status = ''
	post = ''
	cname = ''
	arrows = ''
	try:
		post_id = request.GET['post_id']
		post = Post.objects.filter(id=post_id)[0]
		arrows = get_user_arrows(post)
		cname = post.user.username
		post = posts_to_html(request,post,'user')
		status = 'ok'
	except:
		pass
	data = {'post':post, 'cname':cname, 'arrows':arrows, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def get_channel(request, cname=''):
	if cname == '':
		cname = slugify(request.GET['cname'])
	if cname in forbidden_channels:
		cname = random_channel_name()
	posts = ''
	status = 'ok'
	try:
		v = Visited.objects.get(user=request.user, channel=cname)
		v.count = v.count + 1
		v.date = datetime.datetime.now()
		v.save()
	except:
		v = Visited(user=request.user, channel=cname, count=1, date=datetime.datetime.now())
		v.save()
	try:
		channel = Channel.objects.get(name=cname)
		posts = get_channel_posts(request, channel)
	except:
		pass
	if cname.strip() == '':
		status = 'empty'
	try:
		Subscription.objects.get(user=request.user, channel=channel)
		subscribed = 'yes'
	except:
		subscribed = 'no'
	data = {'cname': cname, 'posts':posts, 'status':status, 'subscribed':subscribed}
	return HttpResponse(json.dumps(data), content_type="application/json")

def get_channel_posts(request, channel):
	posts = Post.objects.filter(channel=channel).order_by('-date_bumped')[:10]
	return posts_to_html(request, posts)

@login_required
def get_channel_list(request):
	status = 'ok'
	channels = channel_list_to_html(request)
	data = {'status':status, 'channels': channels}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_pms(request):
	data = ''
	last_pm_id = request.GET.get('last_pm_id',0)
	ss = Silenced.objects.filter(user=request.user)
	n = 20
	bl = []
	senders = []
	while True:
		pmr = PrivateMessage.objects.filter(user=request.user,hidden=False,id__lt=last_pm_id).exclude(sender__username__in=[s.brat for s in ss] + senders).order_by('-id')[:n]
		pms = PrivateMessage.objects.filter(sender=request.user, hidden=False, id__lt=last_pm_id).order_by('-id')[:n]
		pmx = sorted(itertools.chain(pmr, pms), key=attrgetter('date'), reverse=True)[:n]
		l = list(pmx)
		bl = bl + l
		bl = remove_duplicate_senders(request, bl)
		senders = get_senders_list(request,bl)
		last_pm_id = bl[-1].id
		if len(bl) >= 20 or pmr.count() == 0:
			break
	pms = pm_to_html(request, bl)
	status = 'ok'
	data = {'pms':pms, 'status':status,'count':len(bl)}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_chatall(request):
	data = ''
	messages = ''
	status = 'error'
	last_pm_id = request.GET.get('last_pm_id', 0)
	original_last_chatall_id = request.GET['original_last_chatall_id'];
	if last_pm_id != 0:
		messages = get_chat_messages(request, last_pm_id)
		messages = chat_to_html(request, messages, 'chatall', original_last_chatall_id)
		status = 'ok'
	data = {'messages':messages, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_channel(request):
	data = ''
	messages = ''
	status = 'error'
	ids = request.GET.get('ids', 0).split(',')
	post = Post.objects.get(id=ids[0])
	posts = Post.objects.filter(channel=post.channel).exclude(id__in=ids).order_by('-date_bumped')[:10]
	posts = posts_to_html(request,posts)
	if posts != '':
		status = 'ok'
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_user_on_channel(request):
	data = ''
	messages = ''
	status = 'error'
	id = request.GET.get('id', 0)
	post = Post.objects.get(id=id)
	posts = Post.objects.filter(user=post.user,channel=post.channel, id__lt=post.id).order_by('-id')[:10]
	posts = posts_to_html(request,posts)
	if posts != '':
		status = 'ok'
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_user(request):
	data = ''
	messages = ''
	status = 'error'
	id = request.GET.get('id', 0)
	post = Post.objects.get(id=id)
	posts = Post.objects.filter(user=post.user, id__lt=id).order_by('-id')[:10]
	posts = posts_to_html(request,posts,'user')
	if posts != '':
		status = 'ok'
	data = {'posts':posts, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_pins(request):
	status = 'error'
	id = request.GET['id']
	uname = request.GET['uname']
	user = User.objects.get(username=uname)
	pin = Pin.objects.get(user=user, post__id=id)
	pins = Pin.objects.filter(user=user, id__lt=pin.id).order_by('-id')[:10]
	posts = []
	for p in pins:
		posts.append(p.post)
	pins = posts_to_html(request, posts, 'new')
	status = 'ok'
	data = {'pins':pins, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def load_more_chat(request):
	data = ''
	messages = ''
	status = 'error'
	last_pm_id = request.GET.get('last_pm_id',0)
	if last_pm_id != 0:
		pm = PrivateMessage.objects.get(id=last_pm_id)
		if pm.user.username == request.user.username:
			peer = pm.sender
		else:
			peer = pm.user
		messages = get_chat_history(request, peer, last_pm_id)
		messages = chat_to_html(request,messages)
		status = 'ok'
	data = {'messages':messages, 'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def set_theme(request):
	background = request.POST['theme_background']
	text = request.POST['theme_text']
	link = request.POST['theme_link']
	input_background = request.POST['theme_input_background']
	input_text = request.POST['theme_input_text']
	input_border = request.POST['theme_input_border']
	input_placeholder = request.POST['theme_input_placeholder']
	scroll_background = request.POST['theme_scroll_background']
	embed_option = request.POST['embed_option']
	p = get_profile(request.user)
	p.theme_background = background
	p.theme_text = text
	p.theme_link = link
	p.theme_input_background = input_background
	p.theme_input_text = input_text
	p.theme_input_border = input_border
	p.theme_input_placeholder = input_placeholder
	p.theme_scroll_background = scroll_background
	p.embed_option = embed_option
	p.save()
	status = 'ok'
	data = {'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")
	
def slugify(name):
	name = name.strip(' ')
	name = name[0:25]
	name = name.lower()
	name = re.sub('[^a-z0-9ñ]', '', name.encode('utf8'))
	return name
	
def clean_username(username):
	try:
		p = re.compile(r"[a-zA-Z0-9]+")
		strlist = p.findall(username)
		if strlist:
			s = ''.join(strlist)
			if s == username:
				return s
			else:
				return False
		return False
	except:
		return False

def stripper(value):
	return value.replace("<", "")

@login_required
def admin_users(request):
	if request.user.username in admin_list:
		if request.method == 'POST':
			delete_list = request.POST.getlist('delete_list')
			for uname in delete_list:
				u = User.objects.get(username=uname)
				u.delete()
			return HttpResponseRedirect('.') 
		else:
			c = create_c(request)
			c['users'] = get_users()
			return render_to_response('admin_users.html', c, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect('/') 

@login_required
def delete_user(request, uname):
	if uname == 'madprops':
		return HttpResponse('nope')
	if request.user.username in admin_list:
		u = User.objects.get(username=uname)
		u.delete()
	return HttpResponse('ok')

def user_is_banned(request):
	bans1 = []
	if request.user.is_authenticated():
		bans1 = Ban.objects.filter(username=request.user.username)
	bans2 = Ban.objects.filter(ip=get_ip(request))
	bans = itertools.chain(bans1, bans2)
	for b in bans:
		if b.exp_date > datetime.datetime.now():
			return True
		else:
			b.delete()
	return False

@login_required
def ban_user(request):
	cmd = request.POST['cmd']
	username = cmd.split('ban user ')[1].strip()
	try:
		user = User.objects.get(username=username)
	except:
		status = "user doesn't exist"
		data = {'status':status}
		return HttpResponse(json.dumps(data), content_type="application/json")
	if request.user.username not in admin_list or user.username == 'madprops':
		data = {'status':'nope'}
		return HttpResponse(json.dumps(data), content_type="application/json")
	p = get_profile(user)
	ban = Ban(username=user.username, ip=p.ip, exp_date=datetime.datetime.now() + datetime.timedelta(days=60))
	ban.save()
	status = user.username + ' has been banned'
	data = {'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def unban_user(request):
	cmd = request.POST['cmd']
	username = cmd.split('ban user ')[1].strip()
	if request.user.username not in admin_list:
		data = {'status':'nope'}
		return HttpResponse(json.dumps(data), content_type="application/json")
	bans = Ban.objects.filter(username=username)
	for b in bans:
		b.delete()
	status = username + ' has been unbanned'
	data = {'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def change_username(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	status = ''
	cmd = request.POST['cmd'].lower().strip()
	username = cmd.split('change username to ')[1].strip()
	uname = '#same'
	if not clean_username(username):
		status = 'wrong username format'
		data = {'status':status, 'uname':uname}
		return HttpResponse(json.dumps(data), content_type="application/json")
	if username.replace(" ", "") == "":
		status = 'you must type a username'
		data = {'status':status, 'uname':uname}
		return HttpResponse(json.dumps(data), content_type="application/json")
	if len(username) > 20:
		status = 'username is too long'
		data = {'status':status, 'uname':uname}
		return HttpResponse(json.dumps(data), content_type="application/json")
	try:
		User.objects.get(username=username)
		status = 'username already exists'
		data = {'status':status, 'uname':uname}
		return HttpResponse(json.dumps(data), content_type="application/json")
	except:
		pass
	request.user.username = username
	request.user.save()
	uname = username
	status = 'username changed succesfully'
	data = {'status':status, 'uname':uname}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def change_password(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	status = ''
	cmd = request.POST['cmd'].lower().strip()
	password = cmd[19:]
	if password.replace(" ", "") == "":
		status = 'you must type a password'
		data = {'status':status, 'csrf_token':'no'}
		return HttpResponse(json.dumps(data), content_type="application/json")
	if len(password) > 50:
		status = 'password is too long'
		data = {'status':status, 'csrf_token':'no'}
		return HttpResponse(json.dumps(data), content_type="application/json")
	request.user.set_password(password)
	request.user.save()
	request.user.backend='django.contrib.auth.backends.ModelBackend'
	auth_login(request, request.user)
	csrf_token = unicode(csrf(request)['csrf_token'])
	status = 'password changed succesfully'
	data = {'status':status, 'csrf_token':csrf_token}
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def use_theme(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	status = ''
	cmd = request.POST['cmd'].lower().strip()
	username = cmd.split('use theme by ')[1].strip()
	try:
		user = User.objects.get(username=username)
	except:
		status = "user doesn't exist"
		data = {'status':status}
		return HttpResponse(json.dumps(data), content_type="application/json")
	p = get_profile(request.user)
	p2 = get_profile(user)
	data = {}
	if p2.theme_background != '0' and p2.theme_background != '':
		p.theme_background = p2.theme_background
		p.theme_text = p2.theme_text
		p.theme_link = p2.theme_link
		p.theme_input_background = p2.theme_input_background
		p.theme_input_text = p2.theme_input_text
		p.theme_input_border = p2.theme_input_border
		p.theme_input_placeholder = p2.theme_input_placeholder
		p.theme_scroll_background = p2.theme_scroll_background
		p.save()
		if not Alert.objects.filter(user=user, type='theme', user2=request.user, date__gt=datetime.datetime.now() - datetime.timedelta(hours=1)).count() >= 1:
			alert = Alert(user=user, type='theme', user2=request.user, date=datetime.datetime.now())
			alert.save()
		data['theme_background'] = p.theme_background 
		data['theme_text'] = p.theme_text 
		data['theme_link'] = p.theme_link 
		data['theme_input_background'] = p.theme_input_background 
		data['theme_input_text'] = p.theme_input_text 
		data['theme_input_border'] = p.theme_input_border 
		data['theme_input_placeholder'] = p.theme_input_placeholder 
		data['theme_scroll_background'] = p.theme_scroll_background 
		data['status'] = 'theme applied'
	else:
		status = "user doesn't have a theme"
		data = {'status':status}
		return HttpResponse(json.dumps(data), content_type="application/json")
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def delete_channel(request):
	data = ''
	if request.user.username in admin_list:
		cname = request.GET['cname']
		channel = Channel.objects.get(name=cname)
		channel.delete()
		data = random_channel_name()
	return HttpResponse(json.dumps(data), content_type="application/json")

@login_required
def delete_post(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	status = 'ok'
	post_id = request.POST['id']
	post = Post.objects.get(id=post_id)
	channel = post.channel
	if post.user.username == 'madprops' and request.user.username != 'madprops':
		data = {'status':status}
		return HttpResponse(json.dumps(data), content_type="application/json") 
	if request.user.username in admin_list or request.user == post.user:
		if request.user.username in admin_list:
			try:
				post.delete()
				if Post.objects.filter(channel=channel).count() <= 0:
					channel.delete()
				status = 'ok'
			except:
				pass
		else:	
			try:
				Comment.objects.filter(post=post)[0]
				status = 'commented'
			except:
				try:
					post.delete()
					if Post.objects.filter(channel=channel).count() <= 0:
						channel.delete()
					status = 'ok'
				except:
					pass
	data = {'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json") 

@login_required
def delete_comment(request):
	if user_is_banned(request):
		return HttpResponseRedirect(banned_url)
	status = 'ok'
	comment_id = request.POST['id']
	comment = Comment.objects.get(id=comment_id)
	if comment.user.username == 'madprops' and request.user.username != 'madprops':
		data = {'status':status}
		return HttpResponse(json.dumps(data), content_type="application/json")
	if request.user.username in admin_list or request.user == comment.user:
		if request.user.username in admin_list:
			try:
				if comment == Comment.objects.filter(post=comment.post).last():
					if(len(Comment.objects.filter(post=comment.post)) > 1):
						comment.post.date_modified = Comment.objects.filter(post=comment.post, id__lt=comment.id).last().date
					else:
						comment.post.date_modified = comment.post.date
				comment.delete()
				comment.post.num_comments = len(Comment.objects.filter(post=comment.post))
				if comment.post.num_comments < 101:
					comment.post.date_bumped = comment.post.date_modified
				comment.post.save()
				status = 'ok'
			except:
				pass
		else:
			try:
				Comment.objects.filter(reply=comment)[0]
				status = 'replied'
			except:
				try:
					if comment == Comment.objects.filter(post=comment.post).last():
						if(len(Comment.objects.filter(post=comment.post)) > 1):
							comment.post.date_modified = Comment.objects.filter(post=comment.post, id__lt=comment.id).last().date
						else:
							comment.post.date_modified = comment.post.date
					comment.delete()
					comment.post.num_comments -= 1
					if comment.post.num_comments < 101:
						comment.post.date_bumped = comment.post.date_modified
					comment.post.save()
					status = 'ok'
				except:
					pass
	data = {'status':status}
	return HttpResponse(json.dumps(data), content_type="application/json") 

def error(request):
	return render_to_response('error.html')

def get_profile(user):
	return Profile.objects.get(user=user)

def get_embed_option(user):
	try:
		return get_profile(user).embed_option
	except:
		return 'embed'

def post_to_html(request, post):
	s = ""
	eo = get_embed_option(request.user)
	s = s + "<div class='post_shell post_parent' id='post_" + str(post.id) + "'>"
	s = s + 	"<div class='container'>"
	s = s + 	    "<input type=\"hidden\" value=\"" + str(post.id) + "\" class=\"post_id\">"

	num_pins = post.num_likes

	if Pin.objects.filter(post=post, user=request.user).count() > 0:
		pins = "<a class='pins_status' onClick='pin(\""+str(post.id)+"\"); return false;' href='#'>liked</a>" + "<a class='num_likes' onClick='show_post_likes(\""+str(post.id)+"\"); return false;' href='#'> (" + str(num_pins) + ")</a>&nbsp;&nbsp;&nbsp;"
	else:
		pins = "<a class='pins_status' onClick='pin(\""+str(post.id)+"\"); return false;' href='#'>like</a>" + "<a class='num_likes' onClick='show_post_likes(\""+str(post.id)+"\"); return false;' href='#'> (" + str(num_pins) + ")</a>&nbsp;&nbsp;&nbsp;"
	
	if post.user == request.user:
		edit = "<a class='edit_post' onClick='edit_post(\""+str(post.id)+"\"); return false;' href='#'>edit</a>&nbsp;&nbsp;&nbsp;"
	else:
		edit = ''

	if request.user.username in admin_list or request.user == post.user:
		s = s + 	    "<div style='width:100%;display:table'><div style='text-align:left;display:table-cell'><a onClick='change_user(\"" + post.user.username + "\");return false;' href=\"#\">" + post.user.username + "</a></div><div style='text-align:right;display:table-cell'>" + edit + "<a id='delete_post_" + str(post.id) + "' onClick='delete_post(\""+str(post.id)+"\");return false;' href='#'>delete</a>&nbsp;&nbsp;&nbsp;" + pins + "<a onClick='go_to_bottom();return false;'href='#'>bottom</a></div></div>"
	else:
		s = s + 	    "<div style='width:100%;display:table'><div style='text-align:left;display:table-cell'><a onClick='change_user(\"" + post.user.username + "\");return false;' href=\"#\">" + post.user.username + "</a></div><div style='text-align:right;display:table-cell'>" + pins + "<a onClick='go_to_bottom();return false;'href='#'>bottom</a></div></div>"
	s = s + 	    "<time datetime='" + post.date.isoformat()+"-00:00" + "' class='timeago date'>"+ str(radtime(post.date)) +"</time>"
	if eo == 'embed':
		s = s + 		"<div class='post_content text1'>" + linkify_mentions(ultralize(post.content, info=post.info)) + "</div>"
	else:
		s = s + 		"<div class='post_content text1'>" + linkify_mentions(urlize(post.content)) + "</div>"
	s = s + 	"</div>"
	s = s + "</div>"
	s = s + "<div style='padding-bottom:40px'></div>"
	return s

def posts_to_html(request, posts, mode="channel"):
	s = ''
	eo = get_embed_option(request.user)
	for p in posts:

		num_comments = p.num_comments

		post = ""

		if request.user.username in admin_list or request.user == p.user:
			delete = "<a id='delete_post_" + str(p.id) + "' onClick='delete_post(\""+str(p.id)+"\");return false;' href='#'>delete</a>&nbsp;&nbsp;&nbsp;"
		else:
			delete = ""

		num_pins = p.num_likes

		if Pin.objects.filter(post=p, user=request.user).count() > 0:
			pins = "<a class='pins_status' onClick='pin(\""+str(p.id)+"\"); return false;' href='#'>liked</a>" + "<a class='num_likes' onClick='show_post_likes(\""+str(p.id)+"\"); return false;' href='#'> (" + str(num_pins) + ")</a>&nbsp;&nbsp;&nbsp;"
		else:
			pins = "<a class='pins_status' onClick='pin(\""+str(p.id)+"\"); return false;' href='#'>like</a>" + "<a class='num_likes' onClick='show_post_likes(\""+str(p.id)+"\"); return false;' href='#'> (" + str(num_pins) + ")</a>&nbsp;&nbsp;&nbsp;"

		if p.user == request.user:
			edit = "<a class='edit_post' onClick='edit_post(\""+str(p.id)+"\"); return false;' href='#'>edit</a>&nbsp;&nbsp;&nbsp;"
		else:
			edit = ''

		if mode == "channel":
			nav_link = "<div style='width:100%;display:table'><div style='text-align:left;display:table-cell'><a onClick='change_user(\"" + p.user.username + "\");return false;' href=\"#\">" + p.user.username + "</a></div><div style='text-align:right;display:table-cell'>" + edit + delete + pins + "<a onClick='open_post(\""+str(p.id)+"\");return false' href='#'>comments (" + str(num_comments) + ")</a></div></div>"
		elif mode == "new":
			nav_link = "<div style='width:100%;display:table'><div style='text-align:left;display:table-cell'><a onClick='change_user(\"" + p.user.username + "\");return false;' href=\"#\">" + p.user.username + "</a> &nbsp;on&nbsp; <span class='post_cname_holder'> <a onClick='goto(\"" + p.channel.name + "\");return false;' href=\"#\"><span class='post_cname'>" + p.channel.name + "</span></a></span></div><div style='text-align:right;display:table-cell'>" + edit + delete + pins + "<a class='commentslink' id='cl_" + str(p.id) + "' onClick='open_post(\""+str(p.id)+"\");return false' href='#'>comments (" + str(num_comments) + ")</a></div></div>"
		else:
			nav_link = "<div style='width:100%;display:table'><div style='text-align:left;display:table-cell'><a onClick='change_user(\"" + p.user.username + "\");return false;' href=\"#\">" + p.user.username + "</a> &nbsp;on&nbsp; <span class='post_cname_holder'> <a onClick='goto(\"" + p.channel.name + "\");return false;' href=\"#\"><span class='post_cname'>" + p.channel.name + "</span></a></span></div><div style='text-align:right;display:table-cell'>" + edit + delete + pins + "<a class='commentslink' id='cl_" + str(p.id) + "' onClick='open_post(\""+str(p.id)+"\");return false' href='#'>comments (" + str(num_comments) + ")</a></div></div>"
		date = "<time datetime='" + p.date.isoformat() +"-00:00" +  "' class='timeago date'>"+ str(radtime(p.date)) +"</time>"
		post = post + "<div class='post_shell post_parent' id='post_" + str(p.id) + "'>"
		post = post + 	"<div class='post_container'>"
		post = post + 		  "<div style='width:100%'>"
		post = post + 		  "<input type=\"hidden\" value=\"" + str(p.id) + "\" id='channel_post' class=\"post_id\">"
		post = post + 		  "<div style='padding-bottom:0px' class='details' id='details'>" + nav_link + date + "</div>"
		post = post + 		  "<input type='hidden' value='" + p.user.username + "' class='username'>"
		post = post + 		  "</div>"
		if eo == 'embed':
			post = post + 		  "<div class='post_content text1'>" + linkify_mentions(ultralize(p.content, info=p.info)) + "</div>"
		else:
			post = post + 		  "<div class='post_content text1'>" + linkify_mentions(urlize(p.content)) + "</div>"
		post = post + 	"</div>"
		post = post + "</div>"
		s = s + post
		s = s + "<div style='padding-bottom:40px'></div>"
	return s

def comments_to_html(request, comments):
	s = ""
	for c in comments:
		s = s + "<div class='post_parent' id='comment_" + str(c.id) + "'>"
		s = s +  "<div class='container'>"
		s = s +   "<input type=\"hidden\" value=\"" + str(c.id) + "\" class=\"comment_id\">"

		num_likes = c.num_likes

		if CommentLike.objects.filter(comment=c, user=request.user).count() > 0:
			likes = "<a class='comment_like_status' onClick='like_comment(\""+str(c.id)+"\"); return false;' href='#'>liked</a>" + "<a class='num_likes' onClick='show_comment_likes(\""+str(c.id)+"\"); return false;' href='#'> (" + str(num_likes) + ")</a>&nbsp;&nbsp;&nbsp;"
		else:
			likes = "<a class='comment_like_status' onClick='like_comment(\""+str(c.id)+"\"); return false;' href='#'>like</a>" + "<a class='num_likes' onClick='show_comment_likes(\""+str(c.id)+"\"); return false;' href='#'> (" + str(num_likes) + ")</a>&nbsp;&nbsp;&nbsp;"

		if c.user == request.user:
			edit = "<a class='edit_comment' onClick='edit_comment(\""+str(c.id)+"\"); return false;' href='#'>edit</a>&nbsp;&nbsp;&nbsp;"
		else:
			edit = ''

		if request.user.username in admin_list or request.user == c.user:
			s = s +   "<div style='width:100%;display:table'><div style='text-align:left;display:table-cell'><a onClick='change_user(\"" + c.user.username + "\");return false;' href=\"#\">" + c.user.username + "</a></div><div style='text-align:right;display:table-cell'>" + edit + "<a id='delete_comment_" + str(c.id) + "' onClick='delete_comment(\""+str(c.id)+"\");return false;' href='#'>delete</a>&nbsp;&nbsp;&nbsp;" + likes + "<a onClick='reply_to("+str(c.id)+");return false;'href='#'>reply</a></div></div>"
		else:
			s = s +   "<div style='width:100%;display:table'><div style='text-align:left;display:table-cell'><a onClick='change_user(\"" + c.user.username + "\");return false;' href=\"#\">" + c.user.username + "</a></div><div style='text-align:right;display:table-cell'>" + likes + "<a onClick='reply_to("+str(c.id)+");return false;'href='#'>reply</a></div></div>"
		s = s +   "<time datetime='" + c.date.isoformat()+"-00:00" + "' class='timeago date'>"+ str(radtime(c.date)) +"</time>"
		if c.reply:
			s = s + "<div class='quote_body'>"
			s = s + "<a class='quote_username' onclick='show_quote(" + str(c.reply.id) + ",1);return false' href='#'>quote</a>" + " by <a class='quote_username' onClick='change_user(\"" + c.reply.user.username + "\");return false;' href=\"#\">" + c.reply.user.username + "</a>"
			s = s + "<div style='width:100%' class='comment_content reply'>" + linkify_mentions(urlize_inline(c.reply.content[:300])) + "</div>"
			s = s + "</div>"
			s = s + "<div style='padding-bottom:8px'></div>"
		s = s +   "<div class='comment_content text2'>" + linkify_mentions(urlize_inline(c.content)) + "</div>"
		s = s +  "</div>"
		s = s + "</div>"
		s = s + "<div style='padding-bottom:40px'></div>"
	return s

def chat_to_html(request, posts, mode='default', last=None):
	s = ""
	eo = get_embed_option(request.user)
	if last != None:
		if mode == 'chatall':
			s = s + "<input class='original_last_chatall_id' type='hidden' value=" + str(last) + ">"
	for p in posts:
		s = s + "<div class='post_shell post_parent' id='post_" + str(p.id) + "'>"
		s = s + "<div class='chat_container'>"
		if p.sender.username == 'note':
			s = s + "<div class='details_note'>"
			s = s + "<a onClick='"
		else:
			s = s + "<div class='details'>"
			if mode=='sent':
				s = s + "<a onClick='chat(\"" + p.user.username + "\");"
			elif mode=='inbox':
				s = s + "<a onClick='chat(\"" + p.sender.username + "\");"
			elif mode=='chatall':
				if p.sender == request.user:
					s = s + "<a onClick='chat(\"" + p.user.username + "\");"
				else:
					if last != None:
						if p.id > int(last):
							s = s + "<div class='new_label'> new </div>"
					s = s + "<a onClick='chat(\"" + p.sender.username + "\");"
			else:
				s = s + "<a onClick='change_user(\"" + p.sender.username + "\");"
		s = s + "return false;' href=\"#\">"
		if mode in ['sent','chatall']:
			if p.sender.username == request.user.username:
				s = s + 'sent to ' + p.user.username
			else:
				s = s + 'chat with ' + p.sender.username
		else:
			s = s + p.sender.username 
		s = s + "</a></div>"
		s = s + "<time datetime='" + p.date.isoformat()+"-00:00" + "' class='timeago date'>"+ str(radtime(p.date)) +"</time>"
		if eo == 'embed':
			s = s + "<div class='post_content text1'>" + linkify_mentions(ultralize(p.message, info=p.info)) + "</div>"
		else:
			s = s + "<div class='post_content text1'>" + linkify_mentions(urlize(p.message)) + "</div>"
		s = s + "<input type='hidden' value='" + str(p.id) + "' class='post_id'>"
		s = s + "<input type='hidden' value='" + p.sender.username + "' class='username'>"
		s = s + "<input type='hidden' value='" + p.user.username + "' class='receiver'>"
		s = s + "</div>"
		s = s + "</div>"
		s = s + "<div style='padding-bottom:40px'></div>"
	return s

def settings_to_html(request):
	s = "<center>"
	s = s + "<select id='embed_select'><option value='embed'>embed links</option><option value='noembed'>don't embed links (faster)</option></select><br><br>"
	s = s + '<div id="background_picker" class="theme_picker unselectable">background color</div>'
	s = s + '<div id="text_picker" class="theme_picker unselectable">text color</div>'
	s = s + '<div id="link_picker" class="theme_picker unselectable">link color</div>'
	s = s + '<div id="input_background_picker" class="theme_picker unselectable">textbox background color</div>'
	s = s + '<div id="input_text_picker" class="theme_picker unselectable">textbox text color</div>'
	s = s + '<div id="input_border_picker" class="theme_picker unselectable">textbox border color</div>'
	s = s + '<div id="input_placeholder_picker" class="theme_picker unselectable">textbox placeholder color</div>'
	s = s + '<div id="input_scroll_background_picker" class="theme_picker unselectable">scrollbar color</div>'
	s = s + "<br><br> <a href='#' style='font-size:20px' onclick='set_default_theme();return false'> default theme </a>"
	s = s + "<br><br><br><br> <a href='#' style='font-size:20px' onclick='show_advanced();return false'> advanced </a>"
	s = s + advanced_to_html()
	s = s + "<br><br><br><br> <a href='#' style='font-size:20px' onclick='login();return false'> logout </a> <br><br><br><br>"
	s = s + "</center>"
	return s

def advanced_to_html():
	s = ""
	s = s + "<div id='advanced_instructions'>"
	s = s + "<br><br><br><br>"
	s = s + "type these commands in the goto box <br><br>"
	s = s + "to change your username: change username to [newusername] <br><br>"
	s = s + "to change your password: change password to [newpassword] <br><br>"
	s = s + "to use someone elses theme: use theme by [username] <br><br>"
	s = s + "to see posts by someone made on a specific channel: [username] on [channel] <br><br>"
	s = s + "to go to a user profile: user [username] <br><br>"
	s = s + "to chat with a user: chat with [username] <br><br>"
	s = s + "to see what a user has liked: likes by [username] <br><br>"
	s = s + "to do a math calculation: calc [operation]"
	s = s + "</div>"
	return s
	
def alerts_to_html(request, alerts, last=None):
	ss = ''
	if last != None:
		ss = ss + "<input class='original_last_alerts_id' type='hidden' value=" + str(last) + ">"
	for a in alerts:
		s = ''
		try:
			s = s + "<div class='post_parent'>"
			s = s + '<div class="alert">'
			s = s + "<input type='hidden' value='" + str(a.id) + "' class='alert_id'>"
			if last != None:
				if a.id > int(last):
					s = s + "<div class='new_label' style='margin-bottom: -4px'> new </div>"
			s = s + "<time style='padding-bottom:6px' datetime='" + a.date.isoformat()+"-00:00" + "' class='timeago alertdate'>"+ str(radtime(a.date)) +"</time>"
			if a.type == 'pin':	
				s = s + '<a onClick="change_user(\''+ str(a.user2.username) + '\'); return false;" href="#">' + str(a.user2.username) + '</a>'
				s = s + ' liked your '
				s = s + '<a onClick="open_post('+ str(a.post1.id) + '); return false;" href="#">post on ' + a.post1.channel.name + '</a>'
				s = s + '<div class="text2" style="padding-top:5px">' + a.post1.content[:300] + '</div>'
			if a.type == 'comment_like':	
				s = s + '<a onClick="change_user(\''+ str(a.user2.username) + '\'); return false;" href="#">' + str(a.user2.username) + '</a>'
				s = s + ' liked your comment on a '
				s = s + '<a onClick="open_post('+ str(a.comment1.post.id) + '); return false;" href="#">post on ' + a.comment1.post.channel.name + '</a>'
				s = s + '<div class="text2" style="padding-top:5px">' + a.comment1.content[:300] + '</div>'	
			if a.type == 'follow':	
				s = s + '<a onClick="change_user(\''+ str(a.user2.username) + '\'); return false;" href="#">' + str(a.user2.username) + '</a>'
				s = s + ' started following you'
			if a.type == 'comment':
				s = s + '<a onClick="change_user(\''+ str(a.user2) + '\'); return false;" href="#">' + str(a.user2) + '</a>'
				s = s + ' commented on your '
				s = s + '<a onClick="open_post('+ str(a.post1.id) + '); return false;" href="#">post on ' + a.post1.channel.name + '</a>'		
				s = s + '<div class="text2" style="padding-top:5px">' + linkify_mentions(urlize_inline(a.comment1.content)) + '</div>'	
				s = s + "<div style='padding-top:10px'></div>"
				ph = 'reply'
				try:
					Comment.objects.filter(reply=a.comment1, user=request.user)[0]
					ph = 'you already replied to this'
				except:
					pass
				s = s + "<textarea rows=1 placeholder='" + ph + "' type='text' class='alert_reply_input' onkeydown='if(event.keyCode == 13){reply_to_comment(this.value, " + str(a.comment1.id) + ",false);$(this).attr(\"placeholder\", \"you already replied to this\")}'></textarea>"	
				like = 'like'
				try:
					CommentLike.objects.get(user=request.user, comment=a.comment1)
					like = 'liked'
				except:
					pass
				s = s + "<div style='padding-top:10px'></div>"
				s = s + "<a class='alert_like' onclick='like_comment(" + str(a.comment1.id) + ");$(this).html(\"liked\"); return false' href='#'>" + like + "</a>"
			if a.type == 'mention':
				s = s + '<a onClick="change_user(\''+ str(a.user2) + '\'); return false;" href="#">' + str(a.user2) + '</a>'
				s = s + ' mentioned you in a '
				s = s + '<a onClick="open_post('+ str(a.post1.id) + '); return false;" href="#">post on ' + a.post1.channel.name + '</a>'
				s = s + '<div class="text2" style="padding-top:5px">' + linkify_mentions(urlize_inline(a.comment1.content)) + '</div>'
				s = s + "<div style='padding-top:10px'></div>"
				ph = 'reply'
				try:
					Comment.objects.filter(reply=a.comment1, user=request.user)[0]
					ph = 'you already replied to this'
				except:
					pass
				s = s + "<textarea rows=1 placeholder='" + ph + "' type='text' class='alert_reply_input' onkeydown='if(event.keyCode == 13){reply_to_comment(this.value, " + str(a.comment1.id) + ",false);$(this).attr(\"placeholder\", \"you already replied to this\")}'></textarea>"	
				like = 'like'
				try:
					CommentLike.objects.get(user=request.user, comment=a.comment1)
					like = 'liked'
				except:
					pass
				s = s + "<div style='padding-top:10px'></div>"
				s = s + "<a class='alert_like' onclick='like_comment(" + str(a.comment1.id) + ");$(this).html(\"liked\"); return false' href='#'>" + like + "</a>"
			if a.type == 'mention_post':
				s = s + '<a onClick="change_user(\''+ str(a.user2) + '\'); return false;" href="#">' + str(a.user2) + '</a>'
				s = s + ' mentioned you in a '
				s = s + '<a onClick="open_post('+ str(a.post1.id) + '); return false;" href="#">post on ' + a.post1.channel.name + '</a>'
				s = s + '<div class="text2" style="padding-top:5px">' + linkify_mentions(urlize_inline(a.post1.content)) + '</div>'
				s = s + "<div style='padding-top:10px'></div>"
				ph = 'comment'
				try:
					Comment.objects.filter(post=a.post1, user=request.user)[0]
					ph = 'you already commented on this'
				except:
					pass
				s = s + "<textarea rows=1 placeholder='" + ph + "' type='text' class='alert_reply_input' onkeydown='if(event.keyCode == 13){reply_to_post(this.value, " + str(a.post1.id) + ",false);$(this).attr(\"placeholder\", \"you already commented on this\")}'></textarea>"	
				like = 'like'
				try:
					Pin.objects.get(user=request.user, post=a.post1)
					like = 'liked'
				except:
					pass
				s = s + "<div style='padding-top:10px'></div>"
				s = s + "<a class='alert_like' onclick='pin(" + str(a.post1.id) + ");$(this).html(\"liked\"); return false' href='#'>" + like + "</a>"
			if a.type == 'reply':
				s = s + '<a onClick="change_user(\''+ str(a.user2) + '\'); return false;" href="#">' + str(a.user2) + '</a>'
				s = s + ' replied to you in a '
				s = s + '<a onClick="open_post('+ str(a.post1.id) + '); return false;" href="#">post on ' + a.post1.channel.name + '</a>'
				s = s + "<div style='padding-top:8px'></div>"
				s = s + "<div class='quote_body'>"
				s = s + "<div style='width:100%' class='comment_content reply'><div><a class='quote_username' onclick='show_quote(" + str(a.comment1.reply.id) + ",0);return false' href='#'>quote</a>" + " by you </div>"
				s = s + linkify_mentions(urlize_inline(a.comment1.reply.content[:300])) + "</div>"
				s = s + "</div>"
				s = s + "<div style='padding-bottom:8px'></div>"
				s = s + "<div style='padding-bottom:4px'></div>"
				s = s + "<div class='text2' style=''>" + linkify_mentions(urlize_inline(a.comment1.content)) + "</div>"
				s = s + "<div style='padding-top:10px'></div>"
				ph = 'reply'
				try:
					Comment.objects.filter(reply=a.comment1, user=request.user)[0]
					ph = 'you already replied to this'
				except:
					pass
				s = s + "<textarea rows=1 placeholder='" + ph + "' type='text' class='alert_reply_input' onkeydown='if(event.keyCode == 13){reply_to_comment(this.value, " + str(a.comment1.id) + ",false);$(this).attr(\"placeholder\", \"you already replied to this\")}'></textarea>"	
				like = 'like'
				try:
					CommentLike.objects.get(user=request.user, comment=a.comment1)
					like = 'liked'
				except:
					pass
				s = s + "<div style='padding-top:10px'></div>"
				s = s + "<a class='alert_like' onclick='like_comment(" + str(a.comment1.id) + ");$(this).html(\"liked\"); return false' href='#'>" + like + "</a>"
			if a.type == 'theme':	
				s = s + '<a onClick="change_user(\''+ str(a.user2.username) + '\'); return false;" href="#">' + str(a.user2.username) + '</a>'
				s = s + ' is using your theme'
			s = s + '</div>'
			s = s + '</div>'
			s = s + "<div style='padding-bottom:40px'></div>"
			ss = ss + s
		except:
			continue
	return ss

def channel_list_to_html(request):
	s = ""
	visited = Visited.objects.filter(user=request.user).order_by('-date').distinct()[:25]
	count = visited.count()
	for v in visited:
		s = s + "<a href='#' onclick='hide_overlay();goto(\"" + v.channel + "\");return false;'class='channels_item'>" + v.channel + "</a>"
	diff = 50 - count
	if visited:
		vlist = []
		for vis in visited:
			vlist.append(vis.channel)
		channels = Channel.objects.all().exclude(name__in=vlist).order_by('?')[:diff]
	else:
		channels = Channel.objects.all().order_by('?')[:diff]
	for c in channels:
		s = s + "<a href='#' onclick='hide_overlay();goto(\"" + c.name + "\");return false;'class='channels_item'>" + c.name + "</a>"
	return s

def likes_to_html(likes):
	s = ""
	s += "<div class='show_likes_header'> people who liked this </div>"
	for like in likes:
		s += "<a class='show_likes_link' onClick='hide_overlay(); change_user(\"" + like.user.username + "\");return false;' href=\"#\">" + like.user.username + "</a>"
	return s

@csrf_exempt
def paste_form(request):
	if request.method == 'POST':
		text = request.POST['text']
		if len(text) > 100000 or len(text.strip()) < 1:
			c = create_c(request)
			return render_to_response('paste_form.html', c, context_instance=RequestContext(request))	
		paste = Paste(content=text, date=datetime.datetime.now())
		paste.save()
		return HttpResponseRedirect('/paste/' + str(paste.id))
	else:
		c = create_c(request)
		return render_to_response('paste_form.html', c, context_instance=RequestContext(request))

def show_paste(request, id):
	c = create_c(request)
	paste = Paste.objects.get(id=id)
	c['paste'] = paste
	return render_to_response('paste.html', c, context_instance=RequestContext(request))