from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    # owner is set automatically from request.user — never writable from client
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Project
        fields = (
            "id",
            "owner",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        return value.strip()

    def validate(self, attrs):
        owner = attrs.get("owner") or (self.instance.owner if self.instance else None)
        name = attrs.get("name", self.instance.name if self.instance else None)

        qs = Project.objects.filter(owner=owner, name__iexact=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                {"name": "You already have a project with this name."}
            )
        return attrs


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list responses (omits heavy fields)."""

    class Meta:
        model = Project
        fields = ("id", "name", "description", "is_active", "created_at", "updated_at")
        read_only_fields = fields
