from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, Ambucycle, FireIncident, IncidentMedia, IncidentResponse

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'confirm_password', 'first_name', 'last_name', 
                  'phone_number', 'address', 'role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class AmbucycleSerializer(serializers.ModelSerializer):
    operator_details = UserSerializer(source='operator', read_only=True)

    class Meta:
        model = Ambucycle
        fields = ['id', 'vehicle_id', 'operator', 'operator_details', 'current_latitude', 
                  'current_longitude', 'is_available', 'last_location_update']
        read_only_fields = ['id', 'last_location_update']

class IncidentMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentMedia
        fields = ['id', 'incident', 'file_url', 'media_type', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

class FireIncidentSerializer(serializers.ModelSerializer):
    reporter_details = UserSerializer(source='reporter', read_only=True)
    assigned_ambucycle_details = AmbucycleSerializer(source='assigned_ambucycle', read_only=True)
    media = IncidentMediaSerializer(many=True, read_only=True)

    class Meta:
        model = FireIncident
        fields = ['id', 'reporter', 'reporter_details', 'title', 'description', 'latitude', 'longitude', 
                  'status', 'ai_confidence_score', 'voice_stress_score', 'voice_analysis_details',
                  'assigned_ambucycle', 'assigned_ambucycle_details', 'media', 'created_at', 
                  'updated_at', 'verified_at', 'resolved_at']
        read_only_fields = ['id', 'reporter', 'status', 'ai_confidence_score', 'voice_stress_score', 
                           'voice_analysis_details', 'created_at', 'updated_at', 'verified_at', 
                           'resolved_at']

class IncidentResponseSerializer(serializers.ModelSerializer):
    incident_details = FireIncidentSerializer(source='incident', read_only=True)
    ambucycle_details = AmbucycleSerializer(source='ambucycle', read_only=True)

    class Meta:
        model = IncidentResponse
        fields = ['id', 'incident', 'incident_details', 'ambucycle', 'ambucycle_details', 
                  'estimated_arrival_time', 'route_data', 'arrived_at', 'created_at']
        read_only_fields = ['id', 'created_at', 'arrived_at'] 