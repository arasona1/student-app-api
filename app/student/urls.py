"""URL mappings for the student app"""

from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from student import views

router = DefaultRouter()
router.register('students', views.StudentViewSet)
router.register('tags', views.TagViewSet)
router.register('courses', views.CourseViewSet)

app_name = 'student'

urlpatterns = [
    path('', include(router.urls)),
]