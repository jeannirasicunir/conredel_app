from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        choices=Task.STATUS_CHOICES,
        allow_blank=True,
        required=False,
        initial=Task.STATUS_TODO
    )
    priority = serializers.IntegerField(
        min_value=1,
        max_value=5,
        required=False,
        initial=1
    )

    class Meta:
        model = Task
        fields = ["id", "title", "description", "status", "priority", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_initial(self):
        initial = super().get_initial()
        initial['status'] = Task.STATUS_TODO
        initial['priority'] = 1
        return initial

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Handle the case when showing the form template
        if data.get('status') is None:
            data['status'] = Task.STATUS_TODO
        if data.get('priority') is None:
            data['priority'] = 1
        return data
