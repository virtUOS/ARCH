from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'arch_app'

urlpatterns = [
                  # landing page
                  path('', views.IndexView.as_view(), name='index'),
                  # activation link
                  path('activate/<str:uidb64>/<str:token>/', views.ActivateAccountView.as_view(), name='activate'),
                  path('change_password/', views.ChangePasswordView.as_view(), name='change_password'),
                  # archive homepage
                  path("<str:archive_name>/<int:pk>/home/", views.ArchiveDetailView.as_view(),
                       name="archive"),
                  # members page of an archive
                  path("<str:archive_name>/<int:pk>/members/", views.MembersViews.as_view(), name="members"),
                  # create or add member
                  path('add_member/', views.CreateAddMemberView.as_view(), name='add_member'),

                  # membership date
                  path('membership_date/<int:pk>/', views.MembershipDateFormView.as_view(), name='membership_date'),
                  # user profile
                  path("profile/", views.ProfileView.as_view(), name='profile'),

                  # search
                  path("search/", views.SearchView.as_view(), name="search"),

                  # record details
                  path('record/<pk>', views.RecordView.as_view(), name='record'),
                  # delete record
                  path('record/<pk>/delete', views.delete_record, name='delete_record'),
                  # upload record
                  path('<str:archive_name>/<int:archive_id>/upload_record/',
                       views.FileUploadView.as_view(), name='upload_record'),
                  # update record album (change album via drag and drop)
                  path('record_update/', views.RecordUpdateView.as_view(), name='update_record'),
                  # hide comment
                  path('comment/<pk>/hide', views.hide_comment, name='hide_comment'),
                  # create new tag
                  path('record/<pk>/create_tag', views.TagCreateView.as_view(), name='create_tag'),
                  # create new TagBox
                  path('record/<pk>/create_tag_box', views.create_tag_box, name='create_tag_box'),
                  # update tag user on an image
                  path('tag/<pk>', views.UpdateTagView.as_view(), name='tag_user'),
                  # delete tag
                  path('tag/<pk>/delete', views.delete_tag, name='delete_tag'),
                  # pixelate TagBox
                  path('pixelate/<pk>', views.pixelate_image, name='pixelate_image'),
                  # unblur tagbox
                  path('show_tag/<pk>', views.show_tag, name='show_tag'),
                  # create new album
                  path('<str:archive_name>/<int:archive_id>/new_album/', views.AlbumCreateView.as_view(),
                       name='create_album'),
                  # album list
                  path('album_list/<int:archive_pk>', views.AlbumListView.as_view(), name='album_list'),
                  # album
                  path('album/<pk>', views.AlbumView.as_view(), name='album'),
                  # delete album
                  path('album/<pk>/delete', views.delete_album, name='delete_album'),
                  # update album
                  path('album/<pk>/update', views.AlbumUpdateView.as_view(), name='update_album'),

                  # get autocomplete suggestions from database
                  path('autocomplete/', views.autocomplete, name='autocomplete'),
                  # sets the language of the app
                  path('set_language', views.set_language, name='set_language'),
                  # feedback form
                  path('feedback/', views.feedback_view, name='feedback'),
                  # privacy settings
                  path('privacy_settings/', views.PrivacySettingsView.as_view(), name='privacy_settings'),
                  # hide personal data
                  path('hide_personal_data/', views.hide_personal_data, name='hide_personal_data'),
                  # delete account and all data
                  path('delete_account/<str:uidb64>/<str:token>', views.DeleteAccountView.as_view(),
                       name='delete_account'),

                  # dashboard for usage statistics
                  path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
