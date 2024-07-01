from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
from .models import *
from guardian.admin import GuardedModelAdmin


class RecordInline(admin.TabularInline):
    model = Record
    extra = 0


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


class ReactionInline(admin.TabularInline):
    model = Reaction
    extra = 0


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


class UserAdmin(admin.ModelAdmin):
    inlines = (MembershipInline, )


class ArchiveAdmin(GuardedModelAdmin):
    inlines = (MembershipInline, )


class AlbumAdmin(GuardedModelAdmin):
    # fieldsets = [
    #     (None,               {'fields': ['title']}),
    #     ('Date Information', {'fields': ['created'], 'classes': ['collapse']}),
    # ]
    inlines = [RecordInline]
    # list_display = ('title', 'created')
    # list_filter = ['created']
    # search_fields = ['title']


class RecordAdmin(GuardedModelAdmin):
    inlines = [CommentInline, ReactionInline]


admin.site.register(User, UserAdmin)
admin.site.register(Archive, ArchiveAdmin)
admin.site.register(Record, RecordAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Tag)
admin.site.register(Location)
admin.site.register(Membership)
admin.site.register(TagBox)
admin.site.register(Comment)
admin.site.register(Tracker)
