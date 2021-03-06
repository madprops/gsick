import os
from django.conf.urls import *

handler404 = 'server.views.redirect'

handler500 = 'server.views.error'

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

urlpatterns = patterns('',
	(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root':os.path.join(BASE_DIR, 'media')}),
    (r'^enter/$', 'server.views.enter'),
    (r'^logout/$', 'server.views.logout'),
    (r'^check_login/$', 'server.views.check_login'),
    (r'^admin_users/$', 'server.views.admin_users'),
    (r'^new_posts/$', 'server.views.new_posts'),
    (r'^top_posts/$', 'server.views.top_posts'),
    (r'^top/$', 'server.views.show_top'),
    (r'^random_channel/$', 'server.views.random_channel'),
    (r'^get_channel/$', 'server.views.get_channel'),
    (r'^get_channel_list/$', 'server.views.get_channel_list'),
    (r'^get_settings/$', 'server.views.settings'),
    (r'^post_to_channel/$', 'server.views.post_to_channel'),
    (r'^doggo_post_to_channel/$', 'server.views.doggo_post_to_channel'),
    (r'^doggo_post_to_channel$', 'server.views.doggo_post_to_channel'),
    (r'^send_message/$', 'server.views.send_message'),
    (r'^whoami/$', 'server.views.whoami'),
    (r'^seen/$', 'server.views.seen'),
    (r'^note/$', 'server.views.note'),
    (r'^chat_with/$', 'server.views.chat'),
    (r'^refresh_chat/$', 'server.views.refresh_chat'),
    (r'^refresh_channel/$', 'server.views.refresh_channel'),
    (r'^refresh_user/$', 'server.views.refresh_user'),
    (r'^get_help/$', 'server.views.get_help'),
    (r'^prev_channel_post/$', 'server.views.prev_channel_post'),
    (r'^next_channel_post/$', 'server.views.next_channel_post'),
    (r'^prev_user_post/$', 'server.views.prev_user_post'),
    (r'^next_user_post/$', 'server.views.next_user_post'),
    (r'^register/$', 'server.views.register'),
    (r'^send_global_pm/$', 'server.views.send_global_pm'),
    (r'^get_user/$', 'server.views.get_user'),
    (r'^delete_user/(?P<uname>\w+)/$', 'server.views.delete_user'),
    (r'^delete_channel/$', 'server.views.delete_channel'),
    (r'^delete_post/$', 'server.views.delete_post'),
    (r'^delete_comment/$', 'server.views.delete_comment'),
    (r'^delete_note/$', 'server.views.delete_note'),
    (r'^silence/$', 'server.views.silence'),
    (r'^unsilence/$', 'server.views.unsilence'),
    (r'^silenced/$', 'server.views.silenced'),
    (r'^post/(?P<id>\w+)/$', 'server.views.show_post'),
    (r'^new/$', 'server.views.show_new'),
    (r'^user/(?P<id>\w+)/$', 'server.views.show_user'),
    (r'^user/(?P<uname>\w+)/likes$', 'server.views.show_pins'),
    (r'^chat/$', 'server.views.show_chatall'),
    (r'^chat/(?P<uname>\w+)/$', 'server.views.show_chat'),
    (r'^notes/$', 'server.views.show_notes'),
    (r'^help/$', 'server.views.show_help'),
    (r'^random_post/$', 'server.views.random_post'),
    (r'^random/$', 'server.views.show_random'),
    (r'^stream/$', 'server.views.show_stream'),
    (r'^get_stream/$', 'server.views.get_stream'),
    (r'^load_more_pms/$', 'server.views.load_more_pms'),
    (r'^view_inbox/$', 'server.views.view_inbox'),
    (r'^sent_messages/$', 'server.views.sent_messages'),
    (r'^inbox/$', 'server.views.show_inbox'),
    (r'^sent/$', 'server.views.show_sent'),
    (r'^settings/$', 'server.views.show_settings'),
    (r'^view_chat/$', 'server.views.view_chat'),
    (r'^load_more_channel/$', 'server.views.load_more_channel'),
    (r'^load_more_user/$', 'server.views.load_more_user'),
    (r'^load_more_chatall/$', 'server.views.load_more_chatall'),
    (r'^load_more_chat/$', 'server.views.load_more_chat'),
    (r'^load_more_inbox/$', 'server.views.load_more_inbox'),
    (r'^load_more_sent/$', 'server.views.load_more_sent'),
    (r'^load_more_notes/$', 'server.views.load_more_notes'),
    (r'^load_more_top/$', 'server.views.load_more_top_posts'),
    (r'^load_more_new/$', 'server.views.load_more_new'),
    (r'^load_more_comments/$', 'server.views.load_more_comments'),
    (r'^load_more_stream/$', 'server.views.load_more_stream'),
    (r'^refresh_chatall/$', 'server.views.refresh_chatall'),
    (r'^refresh_inbox/$', 'server.views.refresh_inbox'),
    (r'^refresh_sent/$', 'server.views.refresh_sent'),
    (r'^set_theme/$', 'server.views.set_theme'),
    (r'^open_post/$', 'server.views.open_post'),
    (r'^post_comment/$', 'server.views.post_comment'),
    (r'^pin_post/$', 'server.views.pin_post'),
    (r'^get_pins/$', 'server.views.get_pins'),
    (r'^like_comment/$', 'server.views.like_comment'),
    (r'^get_notes/$', 'server.views.get_notes'),
    (r'^check_new_pms/$', 'server.views.check_new_pms'),
    (r'^show_last_comments/$', 'server.views.show_last_comments'),
    (r'^show_older_comments/$', 'server.views.show_older_comments'),
    (r'^load_more_pins/$', 'server.views.load_more_pins'),
    (r'^user_on_channel/$', 'server.views.user_on_channel'),
    (r'^(?P<uname>\w+)/on/(?P<cname>\w+)$', 'server.views.show_user_on_channel'),
    (r'^load_more_user_on_channel/$', 'server.views.load_more_user_on_channel'),
    (r'^view_alerts/$', 'server.views.view_alerts'),
    (r'^alerts/$', 'server.views.show_alerts'),
    (r'^check_new_alerts/$', 'server.views.check_new_alerts'),
    (r'^load_more_alerts/$', 'server.views.load_more_alerts'),
    (r'^reply_to_comment/$', 'server.views.reply_to_comment'),
    (r'^toggle_follow/$', 'server.views.toggle_follow'),
    (r'^toggle_subscribe/$', 'server.views.toggle_subscribe'),
    (r'^change_username/$', 'server.views.change_username'),
    (r'^change_password/$', 'server.views.change_password'),
    (r'^use_theme/$', 'server.views.use_theme'),
    (r'^ban_user/$', 'server.views.ban_user'),
    (r'^unban_user/$', 'server.views.unban_user'),
    (r'^edit_comment/$', 'server.views.edit_comment'),
    (r'^edit_post/$', 'server.views.edit_post'),
    (r'^get_post_content/$', 'server.views.get_post_content'),
    (r'^get_comment_content/$', 'server.views.get_comment_content'),
    (r'^get_post_likes/$', 'server.views.get_post_likes'),
    (r'^get_comment_likes/$', 'server.views.get_comment_likes'),
    (r'^get_quote/$', 'server.views.get_quote'),
    (r'^paste/$', 'server.views.paste_form'),
    (r'^paste/(?P<id>\w+)/$', 'server.views.show_paste'),
    (r'^(?P<channel>\w+)/$', 'server.views.show_channel'),
    (r'^$', 'server.views.main'),
)

