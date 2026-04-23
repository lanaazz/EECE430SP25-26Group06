from django.urls import path
from . import views

urlpatterns = [
    path('messages/',                        views.inbox,                  name='messages'),
    path('messages/<int:conv_id>/',          views.conversation_detail,    name='conversation_detail'),
    path('messages/dm/<int:user_id>/',       views.start_direct_message,   name='start_dm'),
    path('messages/group/new/',              views.create_group_chat,      name='create_group_chat'),
    path('notifications/',                   views.notifications_view,     name='notifications'),
    path('api/unread-counts/',               views.unread_counts_api,      name='unread_counts_api'),
    path('api/notifications/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]
