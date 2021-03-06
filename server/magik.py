
# encoding: utf-8

import os
import random
import datetime
from gettext import gettext as _
import locale
import re
import string
import unicodedata
from django import template
from django.conf import settings
from django.utils import formats
from django.utils.encoding import force_unicode, iri_to_uri
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe, SafeData
from django.template.defaultfilters import stringfilter
from django.utils.translation import ugettext, ungettext
from django.utils.dateformat import format
from django.utils.safestring import SafeData, mark_safe
from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy
from django.utils.http import urlquote

register = template.Library()

root = os.path.dirname(os.path.dirname(__file__))

def log(s):
	with open(root + 'log', 'a') as log:
		log.write(str(s) + '\n\n')

def random_string(n):
	return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(n))
	
def ultralize(text, trim_url_limit=None, nofollow=False, autoescape=False, info=False): 
	trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
	safe_input = isinstance(text, SafeData)
	words = word_split_re.split(force_unicode(text))
	nofollow_attr = nofollow and ' rel="nofollow"' or ''
	has_stuff = False
	for i, word in enumerate(words):
		match = None
		if '.' in word or '@' in word or ':' in word:
			match = punctuation_re.match(word)
		if match:
			lead, middle, trail = match.groups()
			# Make URL we want to point to.
			url = None
			if middle.startswith('http://') or middle.startswith('https://'):
				url = urlquote(middle, safe='/&=:;#?+*')
			elif middle.startswith('www.') or ('@' not in middle and \
					middle and middle[0] in string.ascii_letters + string.digits and \
					(middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
				url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
			elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
				url = 'mailto:%s' % middle
				nofollow_attr = ''
			# Make link.
			if url:
				if has_stuff:
					middle = ''
				else:
					try:
						trimmed = trim_url(middle)
						ytregex = re.compile(r"v=(?P<id>[A-Za-z0-9\-=_]{11})")
						ytregex2 = re.compile(r"^(https?://)?(www\.)?(youtu\.be/)(?P<id>[A-Za-z0-9\-=_]{11})")
						vimeoregex = re.compile(r"^(https?://)?(www\.)?(vimeo\.com/)(?P<id>\d+)")
						dmregex = re.compile(r"^(http://)?(www\.)?(dailymotion\.com/video/)(?P<id>[A-Za-z0-9]+)")
						sctrackregex = re.compile(r"^(https?://)?(www\.)?(soundcloud\.com)[/][\w\-_]+[/][\w\-_]+(?:\?.*)?$")
						scplaylistregex = re.compile(r"^(https?://)?(www\.)?(soundcloud\.com)[/][\w\-_]+[/](sets)[/][\w\-_]+(?:\?.*)?$")
						imguregex = re.compile(r"^(https?://)?(www\.)?(imgur\.com)[/](?P<id>[A-Za-z0-9]{7})$")
						imgurgifvregex = re.compile(r"^(https?://)?(www\.)?(i\.imgur\.com)[/](?P<id>[A-Za-z0-9]{7})(\.gifv)$")
						ytmatch = ytregex.search(middle)
						ytmatch2 = ytregex2.match(middle)
						vimeomatch = vimeoregex.match(middle)
						dmmatch = dmregex.match(middle)
						sctrackmatch = sctrackregex.match(middle)
						scplaylistmatch = scplaylistregex.match(middle)
						imgurmatch = imguregex.match(middle)
						imgurgifvmatch = imgurgifvregex.match(middle)

						if ytmatch:
							video_id = ytmatch.group('id')
						elif ytmatch2:
							video_id = ytmatch2.group('id')
						elif vimeomatch:
							video_id = vimeomatch.group('id')
						elif dmmatch:
							video_id = dmmatch.group('id')
						elif sctrackmatch:
							track_url = sctrackmatch.group(0)
						elif scplaylistmatch:
							playlist_url = scplaylistmatch.group(0)

						if ytmatch or ytmatch2:
							yt_time = None
							timeregex = re.compile(r".*t\=(?P<time>\d+).*")
							timematch = timeregex.match(middle)
							if timematch:
								yt_time = timematch.group('time')

						if autoescape and not safe_input:
							lead, trail = escape(lead), escape(trail)
							url, trimmed = escape(url), escape(trimmed)

						if any(s in middle for s in ['.jpg', '.JPG', '.gif', '.GIF', '.bmp', '.BMP', '.png', '.PNG', '.jpeg', '.JPEG', 'gstatic.com/images']) and not imgurgifvmatch:
							middle = '<div class="image_parent"><a target=_blank href="%s"><img class="contentimg" style="padding-top:10px;display:block; width:100%%" src="%s"></a></div>' % (url, url)
							has_stuff = True

						elif imgurmatch:
							middle = '<div class="image_parent"><a target=_blank href="%s.jpg"><img class="contentimg" style="padding-top:10px;display:block; width:100%%" src="%s.jpg"></a></div>' % (url, url)
							has_stuff = True

						elif ytmatch or ytmatch2:
							yt_id = random_string(20)
							if yt_time != None:
								middle = "<iframe id=yt_" + str(yt_id) + " style=\"z-index:-1000;padding-top:10px;display:block;margin-bottom:3px\" title=\"YouTube video player\" width=\"600\" height=\"365\" src=\"https://www.youtube.com/embed/%s\" frameborder=\"0\" allowfullscreen></iframe>" % (video_id + "?enablejsapi=1&version=3&wmode=opaque&autohide=1&disablekb=1&rel=0&start=" + yt_time)
							else:
								middle = "<iframe id=yt_" + str(yt_id) + " style=\"z-index:-1000;padding-top:10px;display:block;margin-bottom:3px\" title=\"YouTube video player\" width=\"600\" height=\"365\" src=\"https://www.youtube.com/embed/%s\" frameborder=\"0\" allowfullscreen></iframe>" % (video_id + "?enablejsapi=1&version=3&wmode=opaque&autohide=1&disablekb=1&rel=0")
							has_stuff = True

						elif vimeomatch:
							vimeo_id = random_string(20)
							svimeo = "vimeo_" + str(vimeo_id)
							middle = "<iframe id=vimeo_" + str(vimeo_id) + " style='padding-top:10px;display:block;'src=\"http://player.vimeo.com/video/%s?api=1&amp;player_id=%s&amp;playertitle=0&amp;byline=0&amp;portrait=0\" width=\"600\" height=\"405\" frameborder=\"0\"></iframe>" % (video_id, svimeo)
							has_stuff = True

						elif dmmatch:
							middle = "<iframe style='padding-top:10px' frameborder='0' width='560' height='315' src='http://www.dailymotion.com/embed/video/%s?width=560'></iframe>" % (video_id)
							has_stuff = True

						elif sctrackmatch:
							sc_id = random_string(20)
							middle = '<iframe id=sc_' + str(sc_id) + ' style="padding-top:10px" width="600" height="300" scrolling="no" frameborder="no" src="https://w.soundcloud.com/player/?url=https://api.soundcloud.com/tracks/' + info + '&amp;auto_play=false&amp;hide_related=false&amp;show_comments=true&amp;show_user=true&amp;show_reposts=false&amp;visual=true"></iframe>'
							has_stuff = True

						elif scplaylistmatch:
							sc_id = random_string(20)
							middle = '<iframe id=sc_' + str(sc_id) + ' style="padding-top:10px" width="600" height="350" scrolling="no" frameborder="no" src="https://w.soundcloud.com/player/?url=https://api.soundcloud.com/playlists/' + info + '&amp;auto_play=false&amp;hide_related=false&amp;show_comments=true&amp;show_user=true&amp;show_reposts=false&amp;visual=true"></iframe>'
							has_stuff = True

						elif middle.endswith(".ogg") or middle.endswith(".mp3"):
							audio_id = random_string(20)
							middle = "<audio id=audio_" + str(audio_id) + " style=\"max-width:100%%;display:block;margin-bottom:10px;padding-top:10px\" src=\"%s\" controls=\"controls\" preload=\"none\"></audio>" % (url)
							has_stuff = True

						elif middle.endswith(".webm") or middle.endswith(".mp4"):
							video_id = random_string(20)
							middle = "<video id=video_" + str(video_id) + " style=\"width:100%%;display:block;margin-bottom:10px;padding-top:10px\" src=\"%s\" controls=\"controls\" preload=\"metadata\"></video>" % (url)
							has_stuff = True

						elif imgurgifvmatch:
							new_url = url.replace('.gifv', '.webm')
							video_id = random_string(20)
							middle = "<video id=video_" + str(video_id) + " style=\"width:100%%;display:block;margin-bottom:10px;padding-top:10px\" src=\"%s\" controls=\"controls\" preload=\"metadata\"></video>" % (new_url)
							has_stuff = True

						else:
							middle = "<a style='padding-top:5px;display:block;' target='_blank' href='%s'%s>%s</a>" % (url, nofollow_attr, trimmed)
							has_stuff = True

					except:
						middle = "<a style='padding-top:5px;display:block;' target='_blank' href='%s'%s>%s</a>" % (url, nofollow_attr, trimmed)
						has_stuff = True

				words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
				
			else:
				if safe_input:
					words[i] = mark_safe(word)
				elif autoescape:
					words[i] = escape(word)
		elif safe_input:
			words[i] = mark_safe(word)
		elif autoescape:
			words[i] = escape(word)
	return mark_safe(u''.join(words))

def gather_info(text, trim_url_limit=None, nofollow=False, autoescape=False): 
	
	trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
	safe_input = isinstance(text, SafeData)
	words = word_split_re.split(force_unicode(text))
	nofollow_attr = nofollow and ' rel="nofollow"' or ''
	has_stuff = False
	for i, word in enumerate(words):
		match = None
		if '.' in word or '@' in word or ':' in word:
			match = punctuation_re.match(word)
		if match:
			lead, middle, trail = match.groups()
			# Make URL we want to point to.
			url = None
			if middle.startswith('http://') or middle.startswith('https://'):
				url = urlquote(middle, safe='/&=:;#?+*')
			elif middle.startswith('www.') or ('@' not in middle and \
					middle and middle[0] in string.ascii_letters + string.digits and \
					(middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
				url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
			elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
				url = 'mailto:%s' % middle
				nofollow_attr = ''

			if url:

				try:

					sctrackregex = re.compile(r"^(https?://)?(www\.)?(soundcloud\.com)[/][\w\-_]+[/][\w\-_]+(?:\?.*)?$")
					scplaylistregex = re.compile(r"^(https?://)?(www\.)?(soundcloud\.com)[/][\w\-_]+[/](sets)[/][\w\-_]+(?:\?.*)?$")

					sctrackmatch = sctrackregex.match(middle)
					scplaylistmatch = scplaylistregex.match(middle)

					if sctrackmatch:
						import soundcloud
						track_url = sctrackmatch.group(0)
						client = soundcloud.Client(client_id='9cde624283128d4dbe80f3c3aaf31c7a')
						track = client.get('/resolve', url=track_url)
						return str(track.id)

					elif scplaylistmatch:
						import soundcloud
						playlist_url = scplaylistmatch.group(0)
						client = soundcloud.Client(client_id='9cde624283128d4dbe80f3c3aaf31c7a')
						playlist = client.get('/resolve', url=playlist_url)
						return str(playlist.id)

				except:
					pass

	return ''

def urlize(text, trim_url_limit=None, nofollow=False, autoescape=False):
	trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
	safe_input = isinstance(text, SafeData)
	words = word_split_re.split(force_unicode(text))
	nofollow_attr = nofollow and ' rel="nofollow"' or ''
	has_stuff = False
	for i, word in enumerate(words):
		match = None
		if '.' in word or '@' in word or ':' in word:
			match = punctuation_re.match(word)
		if match:
			lead, middle, trail = match.groups()
			# Make URL we want to point to.
			url = None
			if middle.startswith('http://') or middle.startswith('https://'):
				url = urlquote(middle, safe='/&=:;#?+*')
			elif middle.startswith('www.') or ('@' not in middle and \
					middle and middle[0] in string.ascii_letters + string.digits and \
					(middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
				url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
			elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
				url = 'mailto:%s' % middle
				nofollow_attr = ''
			# Make link.
			if url:
				trimmed = trim_url(middle)
				middle = "<a style='padding-top:5px;display:block;' target='_blank' href='%s'%s>%s</a>" % (url, nofollow_attr, trimmed)
				words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
			else:
				if safe_input:
					words[i] = mark_safe(word)
				elif autoescape:
					words[i] = escape(word)
		elif safe_input:
			words[i] = mark_safe(word)
		elif autoescape:
			words[i] = escape(word)
	return mark_safe(u''.join(words))

def urlize_inline(text, trim_url_limit=None, nofollow=False, autoescape=False):
	trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
	safe_input = isinstance(text, SafeData)
	words = word_split_re.split(force_unicode(text))
	nofollow_attr = nofollow and ' rel="nofollow"' or ''
	has_stuff = False
	for i, word in enumerate(words):
		match = None
		if '.' in word or '@' in word or ':' in word:
			match = punctuation_re.match(word)
		if match:
			lead, middle, trail = match.groups()
			# Make URL we want to point to.
			url = None
			if middle.startswith('http://') or middle.startswith('https://'):
				url = urlquote(middle, safe='/&=:;#?+*')
			elif middle.startswith('www.') or ('@' not in middle and \
					middle and middle[0] in string.ascii_letters + string.digits and \
					(middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
				url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
			elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
				url = 'mailto:%s' % middle
				nofollow_attr = ''
			# Make link.
			if url:
				trimmed = trim_url(middle)
				middle = "<a style='display:inline-block;' target='_blank' href='%s'%s>%s</a>" % (url, nofollow_attr, trimmed)
				words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
			else:
				if safe_input:
					words[i] = mark_safe(word)
				elif autoescape:
					words[i] = escape(word)
		elif safe_input:
			words[i] = mark_safe(word)
		elif autoescape:
			words[i] = escape(word)
	return mark_safe(u''.join(words))

def correctify(text, trim_url_limit=None, nofollow=False, autoescape=False):
	txt = ""
	link = ""
	trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
	safe_input = isinstance(text, SafeData)
	words = word_split_re.split(force_unicode(text))
	nofollow_attr = nofollow and ' rel="nofollow"' or ''
	for i, word in enumerate(words):
		match = None
		matched_url = False
		if '.' in word or '@' in word or ':' in word:
			match = punctuation_re.match(word)
		if match:
			lead, middle, trail = match.groups()
			# Make URL we want to point to.
			url = None
			if middle.startswith('http://') or middle.startswith('https://'):
				url = urlquote(middle, safe='/&=:;#?+*')
			elif middle.startswith('www.') or ('@' not in middle and \
					middle and middle[0] in string.ascii_letters + string.digits and \
					(middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
				url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
			elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
				url = 'mailto:%s' % middle
				nofollow_attr = ''
			# Make link.
			if url:
				matched_url = True
				if link == "":
					link = middle
		if not matched_url:
			txt += word

	if link == "":
		corr = txt
	else:
		corr = txt + " " + link

	corr = corr.strip()
	corr = ' '.join(corr.split())

	return corr

def has_url(text, trim_url_limit=None, nofollow=False, autoescape=False):
	middle = 'nope'
	trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
	safe_input = isinstance(text, SafeData)
	words = word_split_re.split(force_unicode(text))
	nofollow_attr = nofollow and ' rel="nofollow"' or ''
	for i, word in enumerate(words):
		match = None
		if '.' in word or '@' in word or ':' in word:
			match = punctuation_re.match(word)
		if match:
			lead, middle, trail = match.groups()
			url = None
			if middle.startswith('http://') or middle.startswith('https://'):
				url = urlquote(middle, safe='/&=:;#?+*')
			elif middle.startswith('www.') or ('@' not in middle and \
					middle and middle[0] in string.ascii_letters + string.digits and \
					(middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
				url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
			elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
				url = 'mailto:%s' % middle
				nofollow_attr = ''
			if url:
				return True
	return False

@register.filter
def datemate(value):
	hoy = datetime.date.today()
	if value.year == hoy.year:
		fecha = format(value, "d F").replace(' 0', ' ')
	else:
		fecha = format(value, "d F Y").replace(' 0', ' ')
	ayer = hoy - datetime.timedelta(1)
	hora = format(value, "g:i A").lower()
	if value.year == hoy.year and value.month == hoy.month and value.day == hoy.day:
		fecha = "today"
	if value.year == ayer.year and value.month == ayer.month and value.day == ayer.day:
		fecha = "yesterday"
	return fecha + " " + "at" + " " + hora
	
@register.filter
def radtime(time):
	now = datetime.datetime.now()
	if type(time) is int:
		diff = now - datetime.datetime.fromtimestamp(time)
	elif isinstance(time,datetime.datetime):
		diff = now - time 
	elif not time:
		diff = now - now
	second_diff = diff.seconds
	day_diff = diff.days
	if day_diff < 0:
		return ''
	if day_diff == 0:
		if second_diff < 60:
			return "less than a minute ago"
		if second_diff < 120:
			return  "1 minute ago"
		if second_diff < 3600:
			return str( second_diff / 60 ) + " minutes ago"
		if second_diff < 7200:
			return "1 hour ago"
		if second_diff < 86400:
			return str( second_diff / 3600 ) + " hours ago"
	if day_diff == 1:
		return "1 day ago"
	if day_diff < 7:
		return str(day_diff) + " days ago"
	if day_diff < 31:
		if day_diff/7 == 1:
			ago = " week ago"
		else:
			ago = " weeks ago"
		return str(day_diff/7) + ago
	if day_diff < 365:
		if day_diff/30 == 1:
			ago = " month ago"
		else:
			ago = " months ago"
		return str(day_diff/30) + ago
	if day_diff/365 == 1:
		ago = " year ago"
	else:
		ago = " years ago"
	return str(day_diff/365) + ago

@register.filter
def happy_time(value):
	time = datetime.datetime.now()
	return format(time, "g:i A").lower()
























################################################
################################################

"""HTML utilities suitable for global use."""

################################################
################################################

# Configuration for urlize() function.
LEADING_PUNCTUATION  = ['(', '<', '&lt;']
TRAILING_PUNCTUATION = ['.', ',', ')', '>', '\n', '&gt;']

# List of possible strings used for bullets in bulleted lists.
DOTS = ['&middot;', '*', '\xe2\x80\xa2', '&#149;', '&bull;', '&#8226;']

unencoded_ampersands_re = re.compile(r'&(?!(\w+|#\d+);)')
word_split_re = re.compile(r'(\s+)')
punctuation_re = re.compile('^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % \
	('|'.join([re.escape(x) for x in LEADING_PUNCTUATION]),
	'|'.join([re.escape(x) for x in TRAILING_PUNCTUATION])))
simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')
link_target_attribute_re = re.compile(r'(<a [^>]*?)target=[^\s>]+')
html_gunk_re = re.compile(r'(?:<br clear="all">|<i><\/i>|<b><\/b>|<em><\/em>|<strong><\/strong>|<\/?smallcaps>|<\/?uppercase>)', re.IGNORECASE)
hard_coded_bullets_re = re.compile(r'((?:<p>(?:%s).*?[a-zA-Z].*?</p>\s*)+)' % '|'.join([re.escape(x) for x in DOTS]), re.DOTALL)
trailing_empty_content_re = re.compile(r'(?:<p>(?:&nbsp;|\s|<br \/>)*?</p>\s*)+\Z')
del x # Temporary variable

def escape(html):
	"""
	Returns the given HTML with ampersands, quotes and angle brackets encoded.
	"""
	return mark_safe(force_unicode(html).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;'))
escape = allow_lazy(escape, unicode)

_base_js_escapes = (
	('\\', r'\u005C'),
	('\'', r'\u0027'),
	('"', r'\u0022'),
	('>', r'\u003E'),
	('<', r'\u003C'),
	('&', r'\u0026'),
	('=', r'\u003D'),
	('-', r'\u002D'),
	(';', r'\u003B'),
	(u'\u2028', r'\u2028'),
	(u'\u2029', r'\u2029')
)

# Escape every ASCII character with a value less than 32.
_js_escapes = (_base_js_escapes +
			   tuple([('%c' % z, '\\u%04X' % z) for z in range(32)]))

def escapejs(value):
	"""Hex encodes characters for use in JavaScript strings."""
	for bad, good in _js_escapes:
		value = mark_safe(force_unicode(value).replace(bad, good))
	return value
escapejs = allow_lazy(escapejs, unicode)

def conditional_escape(html):
	"""
	Similar to escape(), except that it doesn't operate on pre-escaped strings.
	"""
	if isinstance(html, SafeData):
		return html
	else:
		return escape(html)

def linebreaks(value, autoescape=False):
	"""Converts newlines into <p> and <br />s."""
	value = re.sub(r'\r\n|\r|\n', '\n', force_unicode(value)) # normalize newlines
	paras = re.split('\n{2,}', value)
	if autoescape:
		paras = [u'%s' % escape(p).replace('\n', '<br />') for p in paras]
	else:
		paras = [u'%s' % p.replace('\n', '<br />') for p in paras]
	return u'\n\n'.join(paras)
linebreaks = allow_lazy(linebreaks, unicode)

def strip_tags(value):
	"""Returns the given HTML with all tags stripped."""
	return re.sub(r'<[^>]*?>', '', force_unicode(value))
strip_tags = allow_lazy(strip_tags)

def strip_spaces_between_tags(value):
	"""Returns the given HTML with spaces between tags removed."""
	return re.sub(r'>\s+<', '><', force_unicode(value))
strip_spaces_between_tags = allow_lazy(strip_spaces_between_tags, unicode)

def strip_entities(value):
	"""Returns the given HTML with all entities (&something;) stripped."""
	return re.sub(r'&(?:\w+|#\d+);', '', force_unicode(value))
strip_entities = allow_lazy(strip_entities, unicode)

def fix_ampersands(value):
	"""Returns the given HTML with all unencoded ampersands encoded correctly."""
	return unencoded_ampersands_re.sub('&amp;', force_unicode(value))
fix_ampersands = allow_lazy(fix_ampersands, unicode)



def clean_html(text):
	"""
	Clean the given HTML.  Specifically, do the following:
		* Convert <b> and <i> to <strong> and <em>.
		* Encode all ampersands correctly.
		* Remove all "target" attributes from <a> tags.
		* Remove extraneous HTML, such as presentational tags that open and
		  immediately close and <br clear="all">.
		* Convert hard-coded bullets into HTML unordered lists.
		* Remove stuff like "<p>&nbsp;&nbsp;</p>", but only if it's at the
		  bottom of the text.
	"""
	from django.utils.text import normalize_newlines
	text = normalize_newlines(force_unicode(text))
	text = re.sub(r'<(/?)\s*b\s*>', '<\\1strong>', text)
	text = re.sub(r'<(/?)\s*i\s*>', '<\\1em>', text)
	text = fix_ampersands(text)
	# Remove all target="" attributes from <a> tags.
	text = link_target_attribute_re.sub('\\1', text)
	# Trim stupid HTML such as <br clear="all">.
	text = html_gunk_re.sub('', text)
	# Convert hard-coded bullets into HTML unordered lists.
	def replace_p_tags(match):
		s = match.group().replace('</p>', '</li>')
		for d in DOTS:
			s = s.replace('<p>%s' % d, '<li>')
		return u'<ul>\n%s\n</ul>' % s
	text = hard_coded_bullets_re.sub(replace_p_tags, text)
	# Remove stuff like "<p>&nbsp;&nbsp;</p>", but only if it's at the bottom
	# of the text.
	text = trailing_empty_content_re.sub('', text)
	return text
clean_html = allow_lazy(clean_html, unicode)
