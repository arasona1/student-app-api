"""
Tests for the courses API
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Course,
    Student,
)

from student.serializers import CourseSerializer

COURSES_URL = reverse('student:course-list')

def detail_url(course_id):
    """Create and return a course detail URL"""
    return reverse('student:course-detail', args=[course_id])


def create_user(email='user@example.com', password='testpass123'):
    return get_user_model().objects.create_user(email=email, password=password)

class PublicCoursesApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving courses"""
        res = self.client.get(COURSES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateCoursesApiTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_courses(self):
        """Test retrieving a list of courses"""
        Course.objects.create(user=self.user, title='SCI 101')
        Course.objects.create(user=self.user, title='MATH 102')

        res = self.client.get(COURSES_URL)

        courses = Course.objects.all().order_by('-title')
        serializer = CourseSerializer(courses, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_courses_limited_to_user(self):
        """Test list of courses is limited to authenticated user"""
        user2 = create_user(email='user2@example.com')
        Course.objects.create(user=user2, title='ENG 101')
        course = Course.objects.create(user=self.user, title='CS 101')

        res = self.client.get(COURSES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], course.title)
        self.assertEqual(res.data[0]['id'], course.id)

    def test_update_course(self):
        course = Course.objects.create(user=self.user, title='SCI 101')

        payload = {'title': 'BIO 101'}
        url = detail_url(course.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.title, payload['title'])

    def test_delete_course(self):
        course = Course.objects.create(user=self.user, title='CHEM 101')

        url = detail_url(course.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        courses = Course.objects.filter(user=self.user)
        self.assertFalse(courses.exists())

    def test_filter_courses_assigned_to_students(self):
        """Test listing courses by those assigned to students"""
        in1 = Course.objects.create(user=self.user, title='Apples')
        in2 = Course.objects.create(user=self.user, title='Turkey')
        student = Student.objects.create(
            name='Sample name',
            email='Sample4@sample.com',
            address='Address Street',
            birthday='01/01/2001',
            user=self.user,
        )
        student.courses.add(in1)

        res = self.client.get(COURSES_URL, {'assigned_only': 1})

        s1 = CourseSerializer(in1)
        s2 = CourseSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered courses returns a unique list"""
        ing = Course.objects.create(user=self.user, title='Eggs')
        Course.objects.create(user=self.user, title='Lentils')
        student1 = Student.objects.create(
            name='Student11',
            email='Sample1@sample.com',
            address='Student1 Street',
            birthday='01/01/2001',
            user=self.user,
        )
        student2 = Student.objects.create(
            name='Student22',
            email='Sample2@sample.com',
            address='Student2 Street',
            birthday='01/01/2001',
            user=self.user,
        )
        student1.courses.add(ing)
        student2.courses.add(ing)

        res = self.client.get(COURSES_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)