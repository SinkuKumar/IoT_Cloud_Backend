from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Project
from .permissions import IsOwner
from .serializers import ProjectListSerializer, ProjectSerializer


class ProjectViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """
    CRUD endpoints for projects scoped to the authenticated user.

    list:   GET  /api/projects/          → own projects only
    create: POST /api/projects/          → owner auto-set from request.user
    retrieve: GET /api/projects/{id}/   → 404 if not owned
    update: PUT  /api/projects/{id}/    → owner-only
    partial_update: PATCH               → owner-only
    destroy: DELETE /api/projects/{id}/ → owner-only
    """

    permission_classes = [IsOwner]

    def get_queryset(self):
        return (
            Project.objects.select_related("owner")
            .filter(owner=self.request.user)
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ProjectListSerializer
        return ProjectSerializer

    # ------------------------------------------------------------------
    # create – 201 with full representation
    # ------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        # Return with ProjectSerializer (includes all fields)
        out = ProjectSerializer(project, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # destroy – 204 with confirmation message
    # ------------------------------------------------------------------
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        instance.delete()
        return Response(
            {"detail": f'Project "{name}" deleted successfully.'},
            status=status.HTTP_200_OK,
        )
