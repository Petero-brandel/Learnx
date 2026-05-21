from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, ModuleViewSet, LessonViewSet, QuizViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'quizzes', QuizViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
