from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, permissions
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import User, Ambucycle, FireIncident, IncidentMedia, IncidentResponse
from .serializers import (
    UserSerializer, AmbucycleSerializer, FireIncidentSerializer,
    IncidentMediaSerializer, IncidentResponseSerializer
)
from .ai_analysis import analyze_image
from .audio_analysis import VoiceStressAnalyzer
import logging
import mimetypes

logger = logging.getLogger(__name__)

# Initialize voice stress analyzer
voice_analyzer = VoiceStressAnalyzer()

# User API Endpoints
@api_view(['POST'])
@permission_classes([])  # Open for registration
 def user_register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def user_update(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_list(request):
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_detail(request, pk):
    if request.user.role != 'ADMIN' and request.user.id != pk:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    user = get_object_or_404(User, pk=pk)
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def user_update_role(request, pk):
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    user = get_object_or_404(User, pk=pk)
    role = request.data.get('role')
    if role not in dict(User.ROLES):
        return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
    user.role = role
    user.save()
    serializer = UserSerializer(user)
    return Response(serializer.data)

# Ambucycle API Endpoints
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ambucycle_list(request):
    user = request.user
    if user.role == 'ADMIN':
        ambucycles = Ambucycle.objects.all()
    elif user.role == 'AMBUCYCLE_OPERATOR':
        ambucycles = Ambucycle.objects.filter(operator=user)
    else:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = AmbucycleSerializer(ambucycles, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ambucycle_detail(request, pk):
    ambucycle = get_object_or_404(Ambucycle, pk=pk)
    if request.user.role != 'ADMIN' and request.user != ambucycle.operator:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = AmbucycleSerializer(ambucycle)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ambucycle_create(request):
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    serializer = AmbucycleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def ambucycle_update(request, pk):
    ambucycle = get_object_or_404(Ambucycle, pk=pk)
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    serializer = AmbucycleSerializer(ambucycle, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def ambucycle_delete(request, pk):
    ambucycle = get_object_or_404(Ambucycle, pk=pk)
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    ambucycle.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ambucycle_update_location(request, pk):
    ambucycle = get_object_or_404(Ambucycle, pk=pk)
    if request.user != ambucycle.operator and request.user.role != 'ADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    if latitude is not None and longitude is not None:
        ambucycle.current_latitude = latitude
        ambucycle.current_longitude = longitude
        ambucycle.last_location_update = timezone.now()
        ambucycle.save()
        serializer = AmbucycleSerializer(ambucycle)
        return Response(serializer.data)
    return Response({'error': 'Latitude and longitude are required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ambucycle_available(request):
    if request.user.role not in ['ADMIN', 'AMBUCYCLE_OPERATOR']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    available_ambucycles = Ambucycle.objects.filter(is_available=True)
    serializer = AmbucycleSerializer(available_ambucycles, many=True)
    return Response(serializer.data)

# FireIncident API Endpoints
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def incident_list(request):
    user = request.user
    if user.role == 'ADMIN':
        incidents = FireIncident.objects.all()
    elif user.role == 'AMBUCYCLE_OPERATOR':
        incidents = FireIncident.objects.filter(Q(status='VERIFIED') | Q(status='IN_PROGRESS'))
    else:  # REPORTER
        incidents = FireIncident.objects.filter(reporter=user)
    serializer = FireIncidentSerializer(incidents, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def incident_detail(request, pk):
    incident = get_object_or_404(FireIncident, pk=pk)
    if request.user.role != 'ADMIN' and request.user != incident.reporter and incident.status not in ['VERIFIED', 'IN_PROGRESS']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = FireIncidentSerializer(incident)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def incident_create(request):
    serializer = FireIncidentSerializer(data=request.data)
    if serializer.is_valid():
        incident = serializer.save(reporter=request.user)
        _analyze_incident(incident)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def incident_update(request, pk):
    incident = get_object_or_404(FireIncident, pk=pk)
    if request.user.role != 'ADMIN' and request.user != incident.reporter:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = FireIncidentSerializer(incident, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def incident_delete(request, pk):
    incident = get_object_or_404(FireIncident, pk=pk)
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    incident.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def incident_verify(request, pk):
    incident = get_object_or_404(FireIncident, pk=pk)
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    if incident.ai_confidence_score is None:
        _analyze_incident(incident)
    incident.status = 'VERIFIED'
    incident.verified_at = timezone.now()
    incident.save()
    serializer = FireIncidentSerializer(incident)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def incident_reject(request, pk):
    incident = get_object_or_404(FireIncident, pk=pk)
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    incident.status = 'REJECTED'
    incident.save()
    serializer = FireIncidentSerializer(incident)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def incident_assign_ambucycle(request, pk):
    incident = get_object_or_404(FireIncident, pk=pk)
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    ambucycle_id = request.data.get('ambucycle_id')
    try:
        ambucycle = Ambucycle.objects.get(id=ambucycle_id, is_available=True)
        incident.assigned_ambucycle = ambucycle
        incident.status = 'IN_PROGRESS'
        incident.save()
        IncidentResponse.objects.create(incident=incident, ambucycle=ambucycle)
        ambucycle.is_available = False
        ambucycle.save()
        serializer = FireIncidentSerializer(incident)
        return Response(serializer.data)
    except Ambucycle.DoesNotExist:
        return Response({'error': 'Ambucycle not found or not available'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def incident_pending(request):
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    pending_incidents = FireIncident.objects.filter(status='PENDING')
    serializer = FireIncidentSerializer(pending_incidents, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def incident_active(request):
    if request.user.role not in ['ADMIN', 'AMBUCYCLE_OPERATOR']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    active_incidents = FireIncident.objects.filter(Q(status='VERIFIED') | Q(status='IN_PROGRESS'))
    serializer = FireIncidentSerializer(active_incidents, many=True)
    return Response(serializer.data)

# IncidentMedia API Endpoints
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def media_list(request):
    user = request.user
    if user.role == 'ADMIN':
        media = IncidentMedia.objects.all()
    elif user.role == 'AMBUCYCLE_OPERATOR':
        media = IncidentMedia.objects.filter(incident__status__in=['VERIFIED', 'IN_PROGRESS'])
    else:  # REPORTER
        media = IncidentMedia.objects.filter(incident__reporter=user)
    serializer = IncidentMediaSerializer(media, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def media_detail(request, pk):
    media = get_object_or_404(IncidentMedia, pk=pk)
    if request.user.role != 'ADMIN' and request.user != media.incident.reporter and media.incident.status not in ['VERIFIED', 'IN_PROGRESS']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = IncidentMediaSerializer(media)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def media_create(request):
    incident_id = request.data.get('incident')
    try:
        incident = FireIncident.objects.get(id=incident_id)
        if incident.reporter != request.user and request.user.role != 'ADMIN':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        serializer = IncidentMediaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            if incident.media.count() <= 1:
                _analyze_incident(incident)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except FireIncident.DoesNotExist:
        return Response({'error': 'Incident not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def media_delete(request, pk):
    media = get_object_or_404(IncidentMedia, pk=pk)
    if request.user.role != 'ADMIN' and request.user != media.incident.reporter:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    media.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# IncidentResponse API Endpoints
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def response_list(request):
    user = request.user
    if user.role == 'ADMIN':
        responses = IncidentResponse.objects.all()
    elif user.role == 'AMBUCYCLE_OPERATOR':
        responses = IncidentResponse.objects.filter(ambucycle__operator=user)
    else:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = IncidentResponseSerializer(responses, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def response_detail(request, pk):
    response = get_object_or_404(IncidentResponse, pk=pk)
    if request.user.role != 'ADMIN' and request.user != response.ambucycle.operator:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = IncidentResponseSerializer(response)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def response_create(request):
    if request.user.role != 'ADMIN':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    serializer = IncidentResponseSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def response_update(request, pk):
    response = get_object_or_404(IncidentResponse, pk=pk)
    if request.user.role != 'ADMIN' and request.user != response.ambucycle.operator:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = IncidentResponseSerializer(response, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def response_update_eta(request, pk):
    response = get_object_or_404(IncidentResponse, pk=pk)
    if request.user != response.ambucycle.operator and request.user.role != 'ADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    eta = request.data.get('estimated_arrival_time')
    route_data = request.data.get('route_data')
    if eta:
        response.estimated_arrival_time = eta
        if route_data:
            response.route_data = route_data
        response.save()
        serializer = IncidentResponseSerializer(response)
        return Response(serializer.data)
    return Response({'error': 'Estimated arrival time is required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def response_mark_arrived(request, pk):
    response = get_object_or_404(IncidentResponse, pk=pk)
    if request.user != response.ambucycle.operator and request.user.role != 'ADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    response.arrived_at = timezone.now()
    response.save()
    incident = response.incident
    incident.status = 'RESOLVED'
    incident.resolved_at = timezone.now()
    incident.save()
    ambucycle = response.ambucycle
    ambucycle.is_available = True
    ambucycle.save()
    serializer = IncidentResponseSerializer(response)
    return Response(serializer.data)

# Helper function for incident analysis
def _analyze_incident(incident):
    try:
        image_score = 0.0
        voice_stress_score = 0.0
        voice_analysis_details = None
        image_media = incident.media.filter(media_type='IMAGE').first()
        voice_media = incident.media.filter(media_type='AUDIO').first()
        if image_media:
            image_score, image_status = analyze_image(image_media.file_url)
            if 'Error' in image_status:
                logger.error(f"Image analysis error for incident {incident.id}: {image_status}")
        if voice_media:
            file_ext = voice_media.file_url.name.split('.')[-1].lower()
            voice_stress_score, analysis_details, voice_status = voice_analyzer.analyze_voice_stress(
                voice_media.file_url.read(),
                source_format=file_ext
            )
            if 'Error' in voice_status:
                logger.error(f"Voice analysis error for incident {incident.id}: {voice_status}")
            else:
                voice_analysis_details = analysis_details
        confidence_score = (voice_stress_score * 0.7) + (image_score * 0.3)
        incident.voice_stress_score = voice_stress_score
        incident.voice_analysis_details = voice_analysis_details
        incident.ai_confidence_score = confidence_score
        if confidence_score >= 80:
            incident.status = 'VERIFIED'
            incident.verified_at = timezone.now()
        elif confidence_score < 20:
            incident.status = 'REJECTED'
        incident.save()
    except Exception as e:
        logger.error(f"Error analyzing incident {incident.id}: {str(e)}")