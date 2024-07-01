import base64
import os

from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django_q.conf import Conf

from ..forms import SearchForm
from ..views import AlbumView, AlbumCreateView, FileUploadView, delete_record
from ..models import User, Archive, Album, Membership, Record
import datetime


class BaseSetup:
    """ Base class for setting up test data """

    def setUpDB(self):
        """ setup """
        # set global setting to synchronous task execution
        Conf.SYNC = True
        # create 2 archive groups
        self.sample_files_dir = os.path.join(settings.BASE_DIR, 'arch_app/tests/sample_files')
        self.archive1 = Archive.objects.create(name='archive 1')
        self.archive2 = Archive.objects.create(name='archive 2')
        # create 4 users
        self.user1 = User.objects.create_user(username='member1', password='123')
        self.user2 = User.objects.create_user(username='member2', password='123')
        self.user3 = User.objects.create_user(username='mod1', password='123')
        self.user4 = User.objects.create_user(username='mod2', password='123')
        self.user5 = User.objects.create_user(username='member5', password='123')
        self.user6 = User.objects.create_user(username='member6', password='123')

        # create Membership objects
        Membership.objects.create(user=self.user1, archive=self.archive1, role='member')
        Membership.objects.create(user=self.user2, archive=self.archive2, role='member')
        Membership.objects.create(user=self.user5, archive=self.archive2, role='member')
        Membership.objects.create(user=self.user6, archive=self.archive2, role='member')
        Membership.objects.create(user=self.user3, archive=self.archive1, role='moderator')
        Membership.objects.create(user=self.user4, archive=self.archive2, role='moderator')


class TemplateTests(TestCase, BaseSetup):
    """ Template test """
    def setUp(self):
        """ setup """
        self.setUpDB()

    def test_base_template(self):
        """ test """
        self.assertIs(True, True)


class SearchTest(TestCase, BaseSetup):
    """ Test for the search view """
    def setUp(self):
        self.setUpDB()
        # create sample files
        with open(os.path.join(self.sample_files_dir, 'Free_Test_Data_1MB_MP4.mp4'), 'rb') as file:
            video = file.read()
        self.sample_video = SimpleUploadedFile("video.mp4", video)
        with open(os.path.join(self.sample_files_dir, '500kb.png'), 'rb') as file:
            self.sample_image = SimpleUploadedFile("image.png", file.read())
        self.sample_text = SimpleUploadedFile("text.txt", b"file_content", content_type="text/plain")
        files = [self.sample_video, self.sample_image, self.sample_text]
        # login with user1
        self.client.login(username='member1', password='123')
        # send post request to upload_record view
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': files})

        self.client.logout()
        # upload media with a different user
        self.client.login(username='member2', password='123')
        # create sample file

        self.sample_video_2 = SimpleUploadedFile("video2.mp4", video)

        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_video_2]})

        # Archive2 users
        self.client.logout()
        self.client.login(username='member5', password='123')

        # upload a record
        self.sample_video_3_arch_2 = SimpleUploadedFile("video_3_arch_2.mp4", video)
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive2.name,
                                         'archive_id': self.archive2.id}),
                         data={'files': [self.sample_video_3_arch_2]})


        self.client.logout()
        # log in with different username
        self.client.login(username='member6', password='123')

        # upload a record
        self.sample_video_4_arch_2 = SimpleUploadedFile("video_4_arch_2.mp4", video)
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive2.name,
                                         'archive_id': self.archive2.id}),
                         data={'files': [self.sample_video_4_arch_2]})

    def test_search_records(self):

        form_data = {
            'search_query': 'free test data',
            'depicted_users': 'member1',
            'start_date': '2009-12-12',
            'end_date': '2023-11-11',
            'location': 'Osnabrueck',
            'media_type': 'Image'
        }
        search_form = SearchForm(data=form_data)
        self.assertTrue(search_form.is_valid())

        response = self.client.post(reverse('arch_app:search'), data=form_data)
        # check if the view redirects correctly. 302 is redirect
        self.assertEqual(response.status_code, 302)

    def test_search_permissions_member(self):
        # Only show media uploaded by the user.
        form_data = {

            'media_type': 'Video'

        }

        # log in as member2 from archive1
        self.client.logout()
        # log in with different username
        self.client.login(username='member2', password='123')

        response = self.client.post(reverse('arch_app:search'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        # the db contains 4 videos, only 'video2' should be shown, as this one was the only one
        # uploaded by current logged-in user: member2
        self.assertEqual(response.context_data['record_list'][0].title, 'video2')



        # log in as member6 from archive2
        self.client.logout()
        # log in with different username
        self.client.login(username='member6', password='123')

        response = self.client.post(reverse('arch_app:search'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['record_list'][0].title, 'video_4_arch_2')

    def test_search_permissions_album_member(self):
        form_data = {

            'media_type': 'Image'

        }

        # user2 should not have access to the image as this was uploaded by user1
        self.client.logout()
        # log in with different username
        self.client.login(username='member2', password='123')
        response = self.client.post(reverse('arch_app:search'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['record_list']), 0)

        # create album
        self.album_test = Album.objects.create(title='test album',
                                                  description='test description',
                                                  creator=self.user3,
                                                  archive=self.archive1
                                                  )

        # move record to album using the view.
        record = Record.objects.get(title='image')
        self.client.logout()
        self.client.login(username='mod1', password='123')

        response = self.client.post(reverse('arch_app:update_record'), data={
            'album':self.album_test.id,
            'record_id': record.id
        })

        self.assertEqual(response.status_code, 302)

        # Add user2 to the album
        self.album_test.group.user_set.add(self.user2)

        self.client.logout()
        # log in with different username
        self.client.login(username='member2', password='123')

        # even though user2 did not upload the image, they now have access to it. Since user2
        # was added to an album where the image has been moved.
        response = self.client.post(reverse('arch_app:search'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['record_list']), 1)

    def test_search_permissions_moderator(self):


        form_data = {

            'media_type': 'Video'

        }

        # moderator user3 should be able to see all content in archive 1 even if they did not upload it
        self.client.logout()
        # log in as a moderator
        self.client.login(username='mod1', password='123')

        response = self.client.post(reverse('arch_app:search'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['record_list']), 2)

        self.assertIn("video",[i.title for i in response.context_data['record_list']])
        self.assertIn("video2",[i.title for i in response.context_data['record_list']],)

        # log in as moderator user4: Moderator of archive2
        self.client.logout()
        self.client.login(username='mod2', password='123')

        response = self.client.post(reverse('arch_app:search'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context_data['record_list']), 2)
        self.assertIn('video_3_arch_2',[i.title for i in response.context_data['record_list']])
        self.assertIn('video_4_arch_2',[i.title for i in response.context_data['record_list']])


class RecordTests(TestCase, BaseSetup):
    """ Test for creating and deleting Record objects """

    def setUp(self):
        """ setup """
        self.setUpDB()
        # create sample files
        with open(os.path.join(self.sample_files_dir, 'Free_Test_Data_1MB_MP4.mp4'), 'rb') as file:
            self.sample_video = SimpleUploadedFile("video.mp4", file.read())
        with open(os.path.join(self.sample_files_dir, '500kb.png'), 'rb') as file:
            self.sample_image = SimpleUploadedFile("image.png", file.read())
        self.sample_text = SimpleUploadedFile("text.txt", b"file_content", content_type="text/plain")

    def test_create_record(self):
        """ test to create a record """
        files = [self.sample_video, self.sample_image, self.sample_text]
        # login with user1
        self.client.login(username='member1', password='123')
        # send post request to upload_record view
        response = self.client.post(reverse('arch_app:upload_record',
                                            kwargs={'archive_name': self.archive1.name, 'archive_id': self.archive1.id}),
                                    data={'files': files})

        # check if the view redirects correctly. 302 is redirect (to the inbox)
        self.assertEqual(response.status_code, 302)
        # check if the record was created
        records = Record.objects.all()
        self.assertEqual(records.count(), 3)
        # check if the record has the right type and title
        r = Record.objects.get(title='image')
        self.assertEqual(r.type, "Image")
        r = Record.objects.get(title='text')
        self.assertEqual(r.type, "Text")
        r = Record.objects.get(title='video')
        self.assertEqual(r.type, "Video")

    def test_get_record(self):
        """ test to get a record """
        # login with user1
        self.client.login(username='member1', password='123')
        # create one record
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_image]})
        # check if the record was created
        self.assertEqual(Record.objects.count(), 1)
        record = Record.objects.first()
        # send get request to record view
        response = self.client.get(reverse('arch_app:record', kwargs={'pk': record.id}))

        # check if the view returns the correct status code
        self.assertEqual(response.status_code, 200)
        # check if the view returns the correct template
        self.assertEqual(response.context_data['record'].title, 'image')
        # check if the record has the correct creator
        self.assertEqual(response.context_data['record'].creator, self.user1)

    def test_get_record_not_logged_in(self):
        """ test that only logged-in users can access a record """
        # create one record
        self.client.login(username='member1', password='123')
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_image]})
        # check if the record was created
        self.assertEqual(Record.objects.count(), 1)
        logout = self.client.logout()
        record = Record.objects.first()
        # send get request to record view
        response = self.client.get(reverse('arch_app:record', kwargs={'pk': record.id}))

        # check if the view redirects correctly. 302 means redirect
        self.assertEqual(response.status_code, 302)
        # check if the redirect url is correct
        self.assertEqual(response.url, '/accounts/login/?next=/record/' + str(record.id))

    def test_get_record_not_member(self):
        """ test that only members of the archive can access a record """
        # create one record
        self.client.login(username='member1', password='123')
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_image]})
        self.client.logout()
        # check if the record was created
        self.assertEqual(Record.objects.count(), 1)
        self.client.login(username='member2', password='123')
        record = Record.objects.first()
        # send get request to record view
        response = self.client.get(reverse('arch_app:record', kwargs={'pk': record.id}))

        # check if the view redirects correctly. 302 means redirect
        self.assertEqual(response.status_code, 302)
        # check if the redirect url is correct
        self.assertEqual(response.url, '/search/')

    def test_get_record_moderator(self):
        """ test that a moderator can access a record """
        # create one record
        self.client.login(username='member1', password='123')
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_image]})
        self.client.logout()
        # check if the record was created
        self.assertEqual(Record.objects.count(), 1)
        self.client.login(username='mod1', password='123')
        record = Record.objects.first()
        # send get request to record view
        response = self.client.get(reverse('arch_app:record', kwargs={'pk': record.id}))

        # check if the view returns the correct status code
        self.assertEqual(response.status_code, 200)
        # check if the view returns the correct template
        self.assertEqual(response.context_data['record'].title, 'image')
        # check if the record has the correct creator
        self.assertEqual(response.context_data['record'].creator, self.user1)

    def test_get_record_not_moderator(self):
        """ test that a member cannot access a record in the Inbox """
        # create one record
        self.client.login(username='mod1', password='123')
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_image]})
        self.client.logout()
        # check if the record was created
        self.assertEqual(Record.objects.count(), 1)
        self.client.login(username='member1', password='123')
        record = Record.objects.first()
        # send get request to record view
        response = self.client.get(reverse('arch_app:record', kwargs={'pk': record.id}))

        # check if the view redirects correctly. 302 means redirect
        self.assertEqual(response.status_code, 302)
        # check if the redirect url is correct
        self.assertEqual(response.url, '/search/')

        self.client.logout()
        self.client.login(username='mod1', password='123')
        response = self.client.get(reverse('arch_app:record', kwargs={'pk': record.id}))
        self.assertEqual(response.status_code, 200)
        # check if the view returns the correct template
        self.assertEqual(response.context_data['record'].title, 'image')
        # check if the record has the correct creator
        self.assertEqual(response.context_data['record'].creator, self.user3)

    def test_delete_record(self):
        """ test to delete a record """
        # login with user1
        self.client.login(username='member1', password='123')
        # create one record
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_image]})
        # check if the record was created
        self.assertEqual(Record.objects.count(), 1)
        record = Record.objects.first()
        # send post request to delete_record view
        response = self.client.post(reverse('arch_app:delete_record', kwargs={'pk': record.id}))

        # check if the view redirects correctly. 302 means redirect
        self.assertEqual(response.status_code, 302)
        # check if the record was deleted
        self.assertEqual(Record.objects.count(), 0)
        # check if the redirect url is correct
        self.assertEqual(response.url, reverse('arch_app:search'))

    def test_delete_record_not_logged_in(self):
        """ test that only logged-in users can delete a record"""
        # create one record
        login = self.client.login(username='member1', password='123')
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_image]})
        # check if the record was created
        self.assertEqual(Record.objects.count(), 1)
        logout = self.client.logout()
        record = Record.objects.first()
        # send post request to delete_record view
        response = self.client.post(reverse('arch_app:delete_record', kwargs={'pk': record.id}))

        # check if the view redirects correctly. 302 means redirect
        self.assertEqual(response.status_code, 302)
        # check that the record was not deleted
        self.assertEqual(Record.objects.count(), 1)
        # check if the redirect url is correct
        redirect_url = response.url.split('?')[0]
        self.assertEqual(redirect_url, "/accounts/login/")

    def test_delete_record_not_creator(self):
        """ test that a user who is not the creator can not delete a record """
        # create one record
        login = self.client.login(username='mod1', password='123')
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_image]})
        # check if the record was created
        self.assertEqual(Record.objects.count(), 1)
        logout = self.client.logout()
        login = self.client.login(username='member1', password='123')
        record = Record.objects.first()
        # send post request to delete_record view
        response = self.client.post(reverse('arch_app:delete_record', kwargs={'pk': record.id}))

        # check if the view redirects correctly. 302 means redirect
        self.assertEqual(response.status_code, 302)
        # check that the record was not deleted
        self.assertEqual(Record.objects.count(), 1)
        # # check if the redirect url is correct
        # redirect_url = response.url.split('?')[0]
        # target = ""
        # self.assertEqual(redirect_url, target)

    def test_delete_record_moderator(self):
        """ test that a moderator can delete a record """
        # create one record
        login = self.client.login(username='member1', password='123')
        self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': [self.sample_image]})
        # check if the record was created
        self.assertEqual(Record.objects.count(), 1)
        logout = self.client.logout()
        login = self.client.login(username='mod1', password='123')
        record = Record.objects.first()
        # send post request to delete_record view
        response = self.client.post(reverse('arch_app:delete_record', kwargs={'pk': record.id}))

        # check if the view redirects correctly. 302 means redirect
        self.assertEqual(response.status_code, 302)
        # check that the record was deleted
        self.assertEqual(Record.objects.count(), 0)
        # check if the redirect url is correct
        self.assertEqual(response.url, reverse('arch_app:search'))


class AlbumTest(TestCase, BaseSetup):
    def setUp(self):
        # Every test needs access to the request factory.
        self.setUpDB()
        self.album = Album.objects.create(title='test album',
                                          description='test description',
                                          creator=self.user1,
                                          archive=self.archive1
                                          )

    def test_get_album(self):
        """ test if a user that is logged in can access an album """
        self.client.login(username='member1', password='123')
        response = self.client.get(reverse('arch_app:album', kwargs={'pk': str(self.album.id)}))
        # check if the view returns the correct status code
        self.assertEqual(response.status_code, 200)
        # check if the view returns the correct template
        self.assertEqual(response.context_data['album'].title, 'test album')

    def test_get_album_not_logged_in(self):
        """ test if a user that is not logged in is redirected to the login page """
        response = self.client.get(reverse('arch_app:album', kwargs={'pk': str(self.album.id)}))
        # check if the view redirects correctly. 302 means redirect
        self.assertEqual(response.status_code, 302)
        # check if the redirect url is correct
        self.assertEqual(response.url, '/accounts/login/?next=/album/' + str(self.album.id))
    def test_album_create_delete_permissions(self):
        # log in as a moderator and create an album
        self.client.login(username='mod2', password='123')

        # form data
        form_data = {
            'title': 'testAlbumPermissions',
            'description': 'this is a test album',
            'action': 'create',
            'archive': self.archive1.id,

        }
        # create album
        response = self.client.post(reverse('arch_app:create_album', kwargs={
            'archive_name':   self.archive1.name,
            'archive_id': self.archive1.id
        }), data=form_data, follow=True)

        # mod2 does not have the permissions to create an album in archive1
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['messages'])[0].tags, 'error')
        self.assertEqual(Album.objects.filter(title='testAlbumPermissions').count(), 0)

        # log in as mod1, who has the permissions to create albums in archive1
        self.client.logout()
        self.client.login(username='mod1', password='123')

        # create album
        response = self.client.post(reverse('arch_app:create_album', kwargs={
            'archive_name': self.archive1.name,
            'archive_id': self.archive1.id
        }), data=form_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Album.objects.filter(title='testAlbumPermissions').count(), 1)

        # get album created previously
        album_delete = self.archive1.albums.filter(title='testAlbumPermissions')[0]

        self.client.logout()
        self.client.login(username='mod2', password='123')

        # try to delete the album

        response = self.client.post(reverse('arch_app:delete_album', kwargs={
            'pk': album_delete.id}), follow=True)
        self.assertEqual(list(response.context['messages'])[0].tags, 'error')
        # log in as mod1, who has the permissions to delete album
        self.client.logout()
        self.client.login(username='mod1', password='123')

        response = self.client.post(reverse('arch_app:delete_album', kwargs={
            'pk': album_delete.id}), follow=True)

        self.assertEqual(list(response.context['messages'])[0].tags, 'success')

# def test_create_album(self):
    #     # # Create an instance of a POST request.
    #     # login = self.client.login(username='u', password='123')
    #     response = self.client.post(reverse('arch_app:create_album',
    #                                         data={
    #                                             'action': 'create',
    #                                             'title': 'new album',
    #                                             'description': 'new album test description',
    #                                             'creator': self.user,
    #                                             'archive': self.archive.id
    #                                         },
    #                                         kwargs={
    #                                             'archive': str(self.archive.id),
    #                                         }
    #                                         )
    #                                 )
    #
    #     #
    #     # # request = self.factory.post(f'{self.archive.name}/{self.archive.id}/new_album',
    #     # #                             {'action': 'create',
    #     # #                              'title': 'new album',
    #     # #                              'description': 'new album test description',
    #     # #                              'creator': self.user,
    #     # #                              'archive': self.archive.id
    #     # #                              })
    #     #
    #     # # middleware are not supported. Simulate a logged-in user by setting request.user manually.
    #     # # request.user = self.user
    #     # #
    #     # # view = AlbumCreateView.as_view()
    #     # # response = view(request)
    #     #
    #     # # check if album was created and has the right title
    #     self.assertEqual(Album.objects.count(), 2)
    #     self.assertEqual(Album.objects.last().title, 'new album')
    #     # check if album was created in the database
    #     new_album = Album.objects.get(title='new album', creator=self.user, archive=self.archive)
    #     self.assertEqual(new_album, self.album)
    #     # self.assertIs(True, True)

class UploadFormatsTest(TestCase,BaseSetup):
    def setUp(self):
        # Every test needs access to the request factory.
        self.setUpDB()


    def upload_files(self, files_upload):
        # list of sample files
        files = []
        for item in files_upload:
            with open(os.path.join(self.sample_files_dir, item), 'rb') as file:
                f = file.read()
            sample_video = SimpleUploadedFile(item,f)
            files.append(sample_video)

        # send post request to upload_record view
        response = self.client.post(reverse('arch_app:upload_record',
                                 kwargs={'archive_name': self.archive1.name,
                                         'archive_id': self.archive1.id}),
                         data={'files': files})
        return response

    def test_upload_video_formats(self):
        '''
        Test if the upload of videos in different formats works correctly.
        '''
        # login with user1
        self.client.logout()
        self.client.login(username='member1', password='123')

        # list of sample files
        videos = ['test_video_4.ogg','test_video_3.mpg', 'test_video_2.MOV', 'test_video_1.webm',
                  'Free_Test_Data_881KB_AVI.avi', 'Free_Test_Data_1MB_MP4.mp4', 'Free_Test_Data_5MB_WMV.wmv']

        response = self.upload_files(videos)

        # check if the response is 200
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Record.objects.count(), 7)


    def test_upload_image_formats(self):
        '''
        Test if the upload of images works correctly and if the metadata is extracted correctly
        Currently the metadata is extracted only for jpg and png files
        '''
        images = ['test_img_1.JPG', 'test_img_2.png', 'test_img_3.gif', 'test_img_4.svg',
                  'test_img_5.HEIC']

        self.client.login(username='member1', password='123')
        response = self.upload_files(images)

        # check if the response is 302
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Record.objects.count(), 5)
        # check metadata was extracted correctly
        jpg_record = Record.objects.get(title='test_img_1')

        self.assertEqual(jpg_record.date_created,  datetime.date(2023, 11, 23))
        self.assertEqual(f'{jpg_record.location.name} ({ jpg_record.location.country_code})','Dusseldorf (DE)')

        pgn_record = Record.objects.get(title='test_img_2')
        self.assertEqual(pgn_record.date_created, datetime.date(2023, 11, 23))
        self.assertEqual(f'{pgn_record.location.name} ({pgn_record.location.country_code})', 'Dusseldorf (DE)')

    def test_upload_audio_formats(self):
        '''
        Test if the upload of audio files in different formats works correctly.
        '''
        audios = ['test_audio_1.m4a', 'test_audio_2.mp3', 'test_audio_3.aac', 'test_audio_4.mp4',
                  'test_audio_5.ogg','test_audio_6.wav']

        self.client.login(username='member1', password='123')
        response = self.upload_files(audios)

        # check if the response is 302
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Record.objects.count(), 6)




