from django.db import models


class Device(models.Model):

    class Status(models.TextChoices):
        ONLINE   = "online",   "Online"
        OFFLINE  = "offline",  "Offline"
        INACTIVE = "inactive", "Inactive"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="devices",
    )
    name = models.CharField(max_length=255)
    # Hardware/firmware identifier — globally unique, set once at registration
    device_id = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.INACTIVE,
    )
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                name="unique_device_name_per_project",
            )
        ]
        indexes = [
            # Fast per-project device listing
            models.Index(fields=["project", "-created_at"]),
            # Fast status filtering
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.device_id} ({self.project_id})"
