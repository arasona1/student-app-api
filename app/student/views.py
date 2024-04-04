"""
Views for the student APIs
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import (
    viewsets,
    mixins,
    status,
)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Student,
    Tag,
    Course,
)
from student import serializers

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of IDs to filter',
            ),
            OpenApiParameter(
                'courses',
                OpenApiTypes.STR,
                description='Comma separated list of course IDs to filter',
            )
        ]
    )
)

class StudentViewSet(viewsets.ModelViewSet):
    """View for manage student APIs"""
    serializer_class = serializers.StudentSerializer
    queryset = Student.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers"""
        return [int(str_id) for str_id in qs.split(',')]


    def get_queryset(self):
        """Retrieve students for authenticated user"""
        tags = self.request.query_params.get('tags')
        courses = self.request.query_params.get('courses')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if courses:
            course_ids = self._params_to_ints(courses)
            queryset = queryset.filter(courses__id__in=course_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == 'list':
            return serializers.StudentSerializer
        elif self.action == 'upload_image':
            return serializers.StudentImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a student"""
        student = self.get_object()
        serializer = self.get_serializer(student, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to students',
            )
        ]
    )
)
class BaseStudentAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset for student attributes"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(student__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-title').distinct()

class TagViewSet(BaseStudentAttrViewSet):
    """Manage tags in the database"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()

class CourseViewSet(BaseStudentAttrViewSet):
    """Manage courses in the database"""
    serializer_class = serializers.CourseSerializer
    queryset = Course.objects.all()