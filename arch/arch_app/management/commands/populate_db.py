from django.core.management.base import BaseCommand
from arch_app.models import *
import datetime


class Command(BaseCommand):
    help = 'populates the database with two archives and four sample users'

    def handle(self, *args, **options):
        print("start populating DB ...")

        # create superuser
        superusers = User.objects.filter(is_superuser=True)
        if not superusers:
            from django.contrib.auth import get_user_model
            superuser = get_user_model().objects.create_superuser(
                'admin',
                'admin@test.com',
                'admin'
            )
        else:
            superuser = superusers[0]

        # create 2 archives

        address1, created = Location.objects.get_or_create(
            state="Aberdeenshire",
            country="UK",
            name="Address1"
        )
        address2, created = Location.objects.get_or_create(
            name="Address2",
            state="Bremen",
            country="Germany"
        )
        archive1, created = Archive.objects.get_or_create(
            name="GroupA",
            institution_name="organisationA",
            location=address1
        )
        archive2, created = Archive.objects.get_or_create(
            name="GroupB",
            institution_name="organisationB",
            location=address2
        )

        # create users #

        user1, created = User.objects.get_or_create(
            username="UserA",
            first_name="A",
            last_name="User",
            email="test_a@test.de",
        )
        if created:
            user1.set_password("123")
            # user1.is_staff = True
            user1.save()

        user2, created = User.objects.get_or_create(
            username="UserB",
            first_name="B",
            last_name="User",
            email="test_b@test.de"
        )
        if created:
            user2.set_password("123")
            # user2.is_staff = True
            user2.save()

        # create 2 members
        user3, created = User.objects.get_or_create(
            username="UserC",
            first_name="C",
            last_name="User",
            email="test_c@test.de",
        )
        if created:
            user3.set_password("123")
            user3.save()

        user4, created = User.objects.get_or_create(
            username="UserD",
            first_name="D",
            last_name="User",
            email="test_d@test.de",
        )
        if created:
            user4.set_password("123")
            user4.save()

        # add users to archives

        # to archive 1
        m1, created = Membership.objects.get_or_create(user=user1, archive=archive1, role='moderator')
        m2, created = Membership.objects.get_or_create(user=user2, archive=archive1, start_date=datetime.date(2018, 12, 24))
        m3, created = Membership.objects.get_or_create(user=user3, archive=archive1,
                                       start_date=datetime.date(2018, 1, 1),
                                       end_date=datetime.date(2020, 12, 24))
        m4, created = Membership.objects.get_or_create(user=user3, archive=archive1, start_date=datetime.date(2021, 1, 1))

        # to archive 2
        d = datetime.date(2018, 12, 24)
        m5, created = Membership.objects.get_or_create(user=user1, archive=archive2)
        m6, created = Membership.objects.get_or_create(user=user4, archive=archive2, start_date=datetime.date(2018, 12, 24),
                                       end_date=datetime.date(2024, 12, 24))
        m7, created = Membership.objects.get_or_create(user=user3, archive=archive2, start_date=datetime.date(2020, 1, 1),
                                       end_date=datetime.date(2021, 1, 1))

        # add superuser to all archives
        m8, created = Membership.objects.get_or_create(user=superuser, archive=archive1)
        m9, created = Membership.objects.get_or_create(user=superuser, archive=archive2)

        # done
        self.stdout.write(self.style.SUCCESS('Successfully populated DB.'))
