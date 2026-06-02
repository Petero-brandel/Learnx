from django.contrib import admin
from .models import Payment, Enrollment, LessonProgress

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user', 'course', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('reference', 'user__email', 'paystack_id')
    readonly_fields = ('reference', 'paystack_id', 'created_at', 'updated_at')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress_percentage', 'enrolled_at')
    list_filter = ('enrolled_at',)
    search_fields = ('user__email', 'course__title')

admin.site.register(LessonProgress)
