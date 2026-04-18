from django.utils import timezone
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Device
from .permissions import IsProjectOwner
from .serializers import DeviceListSerializer, DevicePingSerializer, DeviceSerializer


class DeviceViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """
    CRUD endpoints for devices scoped to projects owned by the authenticated user.

    list:           GET    /api/devices/              → all own devices; ?project_id= filter
    create:         POST   /api/devices/              → project must be owned by user
    retrieve:       GET    /api/devices/{id}/         → 404 if not reachable
    update:         PUT    /api/devices/{id}/         → ownership enforced
    partial_update: PATCH  /api/devices/{id}/         → ownership enforced
    destroy:        DELETE /api/devices/{id}/         → ownership enforced
    ping:           POST   /api/devices/{id}/ping/    → mark online + update last_seen
    """

    permission_classes = [IsProjectOwner]

    # ------------------------------------------------------------------
    # Queryset – always scoped to the requesting user's projects
    # Uses select_related to avoid N+1 when checking project.owner
    # ------------------------------------------------------------------
    def get_queryset(self):
        qs = (
            Device.objects
            .select_related("project", "project__owner")
            .filter(project__owner=self.request.user)
            .order_by("-created_at")
        )

        # Optional ?project_id= filter
        project_id = self.request.query_params.get("project_id")
        if project_id is not None:
            qs = qs.filter(project_id=project_id)

        return qs

    # ------------------------------------------------------------------
    # Serializer selection
    # ------------------------------------------------------------------
    def get_serializer_class(self):
        if self.action == "list":
            return DeviceListSerializer
        if self.action == "ping":
            return DevicePingSerializer
        return DeviceSerializer

    # ------------------------------------------------------------------
    # create – 201 with full representation
    # ------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        out = DeviceSerializer(device, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # destroy – 200 with confirmation message
    # ------------------------------------------------------------------
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        instance.delete()
        return Response(
            {"detail": f'Device "{name}" deleted successfully.'},
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # ping – POST /api/devices/{id}/ping/
    # Sets status=online and updates last_seen to now.
    # Intended to be called by the device itself or a gateway on its behalf.
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="ping")
    def ping(self, request, pk=None):
        device = self.get_object()
        device.status = Device.Status.ONLINE
        device.last_seen = timezone.now()
        device.save(update_fields=["status", "last_seen", "updated_at"])
        out = DeviceSerializer(device, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_200_OK)
