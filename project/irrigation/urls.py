from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'irrigation'

urlpatterns = [
    # Login
    path("login/", views.login_view, name="login"),

    # Logout
    path("logout/", views.logout_view, name="logout"),

    # Dashboards
    path('farmer/<int:farmer_id>/', views.farmer_dashboard, name='farmer_dashboard'),
    path('gov/', views.gov_dashboard, name='gov_dashboard'),

    # ESP endpoint
    path('esp/<str:device_id>/<str:water_level>/<str:ph>/<str:ldr>/<str:humidity>/<str:temp>/',
         views.esp_endpoint, name='esp_endpoint'),

    # Chart endpoints
    path('chart/water/<int:farmer_id>/', views.chart_water, name='chart_water'),
    path('chart/ph/<int:farmer_id>/', views.chart_ph, name='chart_ph'),
    path('chart/temp_humi/<int:farmer_id>/', views.chart_temp_humi, name='chart_temp_humi'),

    # API
    path('api/latest/<int:farmer_id>/', views.api_latest_reading, name='api_latest_reading'),
    
    #chatbot
    path("chatbot/", views.chatbot_response, name="chatbot_api"),
    path("chatbot/ui/", views.chat_ui, name="chat_ui"),
]
