from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Course, Module, Lesson

def clear_course_cache():
    """
    Clears the entire cache.
    cache invalidation on save or delete
    """
    cache.clear()

@receiver(post_save, sender=Course)
@receiver(post_delete, sender=Course)
@receiver(post_save, sender=Module)
@receiver(post_delete, sender=Module)
@receiver(post_save, sender=Lesson)
@receiver(post_delete, sender=Lesson)
def invalidate_course_cache(sender, instance, **kwargs):
    clear_course_cache()
