"""
Serializers for student APIs
"""

from rest_framework import serializers

from core.models import (
    Student,
    Tag,
    Course,
)

class CourseSerializer(serializers.ModelSerializer):
    """Serializer for courses"""

    class Meta:
        model = Course
        fields = ['id', 'title']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags"""

    class Meta:
        model = Tag
        fields = ['id', 'title']
        read_only_fields = ['id']

class StudentSerializer(serializers.ModelSerializer):
    """Serializer for students"""
    tags = TagSerializer(many=True, required=False)
    courses = CourseSerializer(many=True, required=False)

    class Meta:
        model = Student
        fields = [
            'id', 'name', 'email', 'address', 'birthday', 'link', 'tags',
            'courses',
        ]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, student):
        """Handle getting or creating tags as needed"""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            student.tags.add(tag_obj)

    def _get_or_create_courses(self, courses, student):
        """Handle getting or creating courses as needed"""
        auth_user = self.context['request'].user
        for course in courses:
            course_obj, create = Course.objects.get_or_create(
                user=auth_user,
                **course,
            )
            student.courses.add(course_obj)


    def create(self, validated_data):
        """Create a student"""
        tags = validated_data.pop('tags', [])
        courses = validated_data.pop('courses', [])
        student = Student.objects.create(**validated_data)
        self._get_or_create_tags(tags, student)
        self._get_or_create_courses(courses, student)

        return student

    def update(self, instance, validated_data):
        """Updated student"""
        tags = validated_data.pop('tags', None)
        courses = validated_data.pop('courses', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if courses is not None:
            instance.courses.clear()
            self._get_or_create_courses(courses, instance)

        for attr, value, in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class StudentDetailSerializer(StudentSerializer):
    """Serializer for student detail view"""

    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields + ['courses', 'image']

class StudentImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to students"""

    class Meta:
        model = Student
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}