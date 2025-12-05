from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Category, Application


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Основное', {
            'fields': ('user', 'title', 'description', 'category', 'image')
        }),
        ('Статус и метаданные', {
            'fields': ('status', 'created_at')
        }),
        ('Для статуса "Принято в работу"', {
            'fields': ('admin_comment',),
            'classes': ('collapse',)
        }),
        ('Для статуса "Выполнено"', {
            'fields': ('design_image',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            original = Application.objects.get(pk=obj.pk)
            if original.status != 'new' and obj.status != original.status:
                raise ValidationError("Нельз: изменить статус, если он уже не «Новая».")

        if obj.status == 'in_progress' and not obj.admin_comment:
            raise ValidationError("При смене статуса на «Принято в работу» обязателен комментарий.")
        if obj.status == 'completed' and not obj.design_image:
            raise ValidationError("При смене статуса на «Выполнено» обязателен файл дизайна.")

        super().save_model(request, obj, form, change)