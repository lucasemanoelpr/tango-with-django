from django.contrib import admin
from rango.models import Category, Page
from rango.models import UserProfile

class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'views')
    ordering = ('-views',)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'likes')
    ordering = ('-likes',)


admin.site.register(Category)
admin.site.register(Page)
admin.site.register(UserProfile)

