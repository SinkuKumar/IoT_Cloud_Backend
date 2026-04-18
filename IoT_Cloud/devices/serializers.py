from rest_framework import serializers

from projects.models import Project

from .models import Device


class DeviceSerializer(serializers.ModelSerializer):
    """
    Full serializer used for create / retrieve / update responses.

    Security:
    - `project` queryset is dynamically restricted to projects owned by the
      requesting user, so a client cannot assign a device to someone else's project.
    - `device_id` becomes read-only after creation (hardware ID must not change).
    """

    # Default to empty queryset; populated in __init__ from request context.
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.none())

    class Meta:
        model = Device
        fields = (
            "id",
            "project",
            "name",
            "device_id",
            "description",
            "status",
            "last_seen",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "last_seen", "created_at", "updated_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            # Scope the project field to only the requesting user's projects
            self.fields["project"].queryset = Project.objects.filter(
                owner=request.user
            )

        # Lock device_id after the device has been created
        if self.instance is not None:
            self.fields["device_id"].read_only = True

    def validate_name(self, value):
        return value.strip()

    def validate(self, attrs):
        # Resolve project: from attrs (create/update) or existing instance (partial update)
        project = attrs.get("project") or (self.instance.project if self.instance else None)
        name = attrs.get("name", self.instance.name if self.instance else None)

        if project and name:
            qs = Device.objects.filter(project=project, name__iexact=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"name": "A device with this name already exists in this project."}
                )

        return attrs


class DeviceListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list responses.
    Includes project_id for easy client-side grouping without a join.
    """

    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Device
        fields = (
            "id",
            "project",
            "project_name",
            "name",
            "device_id",
            "status",
            "last_seen",
            "created_at",
        )
        read_only_fields = fields


class DevicePingSerializer(serializers.Serializer):
    """Input for the ping action (no body fields required; all state is server-side)."""
    pass
