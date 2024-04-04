"""Tests for student APIs"""

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Student,
    Tag,
    Course,
)

from student.serializers import (
    StudentSerializer,
    StudentDetailSerializer,
)

STUDENTS_URL = reverse('student:student-list')

def detail_url(student_id):
    """Create and return a student detail URL"""
    return reverse('student:student-detail', args=[student_id])

def image_upload_url(student_id):
    """Create and return an image upload URL"""
    return reverse('student:student-upload-image', args=[student_id])


def create_student(user, **params):
    """Create and return a sample student"""
    defaults = {
        'name': 'Sample name',
        'email': 'sample@sample.com',
        'address': 'Sample Street',
        'birthday': '01/01/2001',
        'link': 'http://example.com/student.pdf',
    }
    defaults.update(params)

    student = Student.objects.create(user=user, **defaults)
    return student

def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicStudentAPITests(TestCase):
    """Test unauthenticated API requests"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(STUDENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateStudentApiTests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')
        self.client.force_authenticate(self.user)

    def test_retrieve_student(self):
        """Test retrieving a list of students"""
        create_student(user=self.user)
        create_student(user=self.user)

        res = self.client.get(STUDENTS_URL)

        students = Student.objects.all().order_by('-id')
        serializer = StudentSerializer(students, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_student_list_limited_to_user(self):
        """Test list of students is limited to authenticated user"""
        other_user = create_user(email='other@example.com', password='password123')
        create_student(user=other_user)
        create_student(user=self.user)

        res = self.client.get(STUDENTS_URL)

        students = Student.objects.filter(user=self.user)
        serializer = StudentSerializer(students, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_student_detail(self):
        """Test get student detail"""
        student = create_student(user=self.user)

        url = detail_url(student.id)
        res = self.client.get(url)

        serializer = StudentDetailSerializer(student)
        #self.assertEqual(res.data, serializer.data)

    def test_create_student(self):
        """Test creating a student"""
        payload = {
            'name': 'Sample name',
            'email': 'Sample@sample.com',
            'address': 'Address Street',
            'birthday': '01/01/2001',
        }
        res = self.client.post(STUDENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        student = Student.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(student, k), v)
        self.assertEqual(student.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""
        original_link = 'http://example.com/student.pdf'
        student = create_student(
            user=self.user,
            name='Sample student name',
            link=original_link
        )

        payload = {'name': 'New student title'}
        url = detail_url(student.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        student.refresh_from_db()
        self.assertEqual(student.name, payload['name'])
        self.assertEqual(student.link, original_link)
        self.assertEqual(student.user, self.user)

    def test_full_update(self):
        """Test full update of student"""
        student = create_student(
            user=self.user,
            name='Sample student name',
            link='http://example.com/student.pdf',
        )

        payload = {
            'name': 'New student name',
            'link': 'http://example.com/new-student.pdf',
            'email': 'New emails',
            'address': 'New addresses',
            'birthday': 'New birthday',
        }
        url = detail_url(student.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        student.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(student, k), v)
        self.assertEqual(student.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the student user results in an error"""
        new_user = create_user(email='user2@example.com', password='test123')
        student = create_student(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(student.id)
        self.client.patch(url, payload)

        student.refresh_from_db()
        self.assertEqual(student.user, self.user)

    def test_delete_student(self):
        """Test deleting a student successfully"""
        student = create_student(user=self.user)

        url = detail_url(student.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Student.objects.filter(id=student.id).exists())

    def test_student_other_users_student_error(self):
        """Test trying to delete another users student gives error"""
        new_user = create_user(email='user2@example.com', password='test123')
        student = create_student(user=new_user)

        url = detail_url(student.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Student.objects.filter(id=student.id).exists())

    def test_create_student_with_new_tags(self):
        payload = {
            'name': 'New student name',
            'email': 'New emails',
            'address': 'New addresses',
            'birthday': 'New birthday',
            'tags': [{'title': 'Thai'}, {'title': 'Dinner'}]
        }
        res = self.client.post(STUDENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        students = Student.objects.filter(user=self.user)
        self.assertEqual(students.count(), 1)
        student = students[0]
        self.assertEqual(student.tags.count(), 2)
        for tag in payload['tags']:
            exists = student.tags.filter(
                title=tag['title'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_student_with_existing_tags(self):
        tag_indian = Tag.objects.create(user=self.user, title='Indian')
        payload = {
            'name': 'New student name',
            'email': 'New emails',
            'address': 'New addresses',
            'birthday': 'New birthday',
            'tags': [{'title': 'Indian'}, {'title': 'Breakfast'}]
        }
        res = self.client.post(STUDENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        students = Student.objects.filter(user=self.user)
        self.assertEqual(students.count(), 1)
        student = students[0]
        self.assertEqual(student.tags.count(), 2)
        self.assertIn(tag_indian, student.tags.all())
        for tag in payload['tags']:
            exists = student.tags.filter(
                title=tag['title'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a student"""
        student = create_student(user=self.user)

        payload = {'tags': [{'title': 'Lunch'}]}
        url = detail_url(student.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, title='Lunch')
        self.assertIn(new_tag, student.tags.all())

    def test_update_student_assign_tag(self):
        """Test assigning an existing tag when updating a student"""
        tag_breakfast = Tag.objects.create(user=self.user, title='Breakfast')
        student = create_student(user=self.user)
        student.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, title='Lunch')
        payload = {'tags': [{'title': 'Lunch'}]}
        url = detail_url(student.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, student.tags.all())
        self.assertNotIn(tag_breakfast, student.tags.all())

    def test_clear_student_tags(self):
        """Test clearing a students tags"""
        tag = Tag.objects.create(user=self.user, title='Dessert')
        student = create_student(user=self.user)
        student.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(student.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(student.tags.count(), 0)

    def test_create_student_with_new_courses(self):
        payload = {
            'name': 'New student name',
            'email': 'New email',
            'address': 'New address',
            'birthday': 'New birthday',
            'courses': [{'title': 'BIO 101'}, {'title': 'ENG 101'}]
        }
        res = self.client.post(STUDENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        students = Student.objects.filter(user=self.user)
        self.assertEqual(students.count(), 1)
        student = students[0]
        self.assertEqual(student.courses.count(), 2)
        for course in payload['courses']:
            exists = student.courses.filter(
                title=course['title'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_student_with_existing_course(self):
        course = Course.objects.create(user=self.user, title='SCI 101')
        payload = {
            'name': 'New student name',
            'email': 'New email',
            'address': 'New address',
            'birthday': 'New birthday',
            'courses': [{'title': 'SCI 101'}, {'title': 'ENG 101'}]
        }
        res = self.client.post(STUDENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        students = Student.objects.filter(user=self.user)
        self.assertEqual(students.count(), 1)
        student = students[0]
        self.assertEqual(student.courses.count(), 2)
        self.assertIn(course, student.courses.all())
        for course in payload['courses']:
            exists = student.courses.filter(
                title=course['title'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_course_on_update(self):
        """Test creating a course when updating a student"""
        student = create_student(user=self.user)

        payload = {'courses': [{'title': 'SCI 101'}]}
        url = detail_url(student.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_course = Course.objects.get(user=self.user, title='SCI 101')
        self.assertIn(new_course, student.courses.all())

    def test_update_student_assign_course(self):
        """Test assigning an existing course when updating a student"""
        course1 = Course.objects.create(user=self.user, title='BIO 101')
        student = create_student(user=self.user)
        student.courses.add(course1)

        course2 = Course.objects.create(user=self.user, title='MATH 101')
        payload = {'courses': [{'title': 'MATH 101'}]}
        url = detail_url(student.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(course2, student.courses.all())
        self.assertNotIn(course1, student.courses.all())

    def test_clear_student_courses(self):
        """Test clearing a students courses"""
        course = Course.objects.create(user=self.user, title='BIO 101')
        student = create_student(user=self.user)
        student.courses.add(course)

        payload = {'courses': []}
        url = detail_url(student.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(student.courses.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering students by tags"""
        r1 = create_student(user=self.user, name='Student1')
        r2 = create_student(user=self.user, name='Student2')
        tag1 = Tag.objects.create(user=self.user, title='Vegan')
        tag2 = Tag.objects.create(user=self.user, title='Vegatarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_student(user=self.user, name='Student3')

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(STUDENTS_URL, params)

        s1 = StudentSerializer(r1)
        s2 = StudentSerializer(r2)
        s3 = StudentSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtering students by courses"""
        r1 = create_student(user=self.user, name='Student1')
        r2 = create_student(user=self.user, name='Student2')
        in1 = Course.objects.create(user=self.user, title='SCI 101')
        in2 = Course.objects.create(user=self.user, title='BIO 101')
        r1.courses.add(in1)
        r2.courses.add(in2)
        r3 = create_student(user=self.user, name='Student3')

        params = {'courses': f'{in1.id},{in2.id}'}
        res = self.client.get(STUDENTS_URL, params)

        s1 = StudentSerializer(r1)
        s2 = StudentSerializer(r2)
        s3 = StudentSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

class ImageUploadTests(TestCase):
    """Tests for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.student = create_student(user=self.user)

    def tearDown(self):
        self.student.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a student"""
        url = image_upload_url(self.student.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.student.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.student.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.student.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)