from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'ambucycles', views.AmbucycleViewSet)
router.register(r'incidents', views.FireIncidentViewSet)
router.register(r'incident-media', views.IncidentMediaViewSet)
router.register(r'incident-responses', views.IncidentResponseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.UserViewSet.as_view({'post': 'create'}), name='register'),
]