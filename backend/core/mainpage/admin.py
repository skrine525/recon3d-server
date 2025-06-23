from django.contrib import admin
from .models import ApplicationFile

@admin.register(ApplicationFile)
class ApplicationFileAdmin(admin.ModelAdmin):
    list_display = ('os', 'version', 'uploaded_at', 'hidden')
    list_filter = ('os', 'hidden')
    search_fields = ('version',)
    ordering = ('-uploaded_at',)
    fieldsets = (
        (None, {
            'fields': ('os', 'version', 'file', 'hidden')
        }),
        ('Служебная информация', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('uploaded_at',)
