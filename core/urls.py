from django.urls import path
from . import views
from django.conf import settings
from core.views import chat_query, chat_with_pdf, chat_with_pdf_ask

urlpatterns = [
    path('', views.home, name='home'),
    path('mcq-generator/', views.mcq_generator, name='mcq-generator'),
    path('chat-with-pdf/', views.chat_with_pdf, name='chat-with-pdf'),
    path('chat-query/', chat_query, name='chat_query'),
    path('chat-with-pdf/ask/', chat_with_pdf_ask, name='chat_with_pdf_ask'),
    path('all-in-one-ai/', views.all_in_one_ai, name='all-in-one-ai'),
    path('get-ai-responses/', views.get_ai_responses, name='get_ai_responses'),
    path('notes/', views.notes, name='notes'),
    path('notes/save/', views.save_note, name='save_note'),
    path('notes/edit/<int:note_id>/', views.edit_note, name='edit_note'),
    path('notes/delete/<int:note_id>/', views.delete_note, name='delete_note'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
]
