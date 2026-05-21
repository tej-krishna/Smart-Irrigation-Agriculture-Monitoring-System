# irrigation/views.py
import io
import base64
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Farmer, SensorReading
from django.http import JsonResponse
from django.shortcuts import render
import requests

# Matplotlib setup
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

# ----- Utilities / computations -----

def compute_fan_speed(temperature, humidity):
    # simple proportional rule
    base = max(0.0, (temperature - 22.0) * 8.0)
    hum_adjust = max(0.0, (humidity - 50.0) * 0.2)
    speed = min(100.0, base + hum_adjust)
    return round(speed, 2)


def compute_light_control(ldr):
    # convert LDR reading (0..1023 maybe) to percent artificial light required
    try:
        val = float(ldr)
    except:
        val = 0.0
    # assume 0..1000 range
    pct = max(0.0, 100.0 - (val / 1000.0) * 100.0)
    return round(min(100.0, pct), 2)


def compute_water_usage(prev_level, current_level, tank_capacity):
    if prev_level is None:
        return None
    delta_pct = prev_level - current_level
    if delta_pct <= 0:
        return 0.0
    liters_used = (delta_pct / 100.0) * tank_capacity
    return round(liters_used, 2)


# ----- Login / Logout (custom) -----

def login_view(request):
    """
    Custom login view handling two modes:
     - farmer: submit device_id (no Django auth required)
     - gov: username/password via Django auth
    """
    if request.method == 'POST':
        mode = request.POST.get('mode', 'farmer')
        if mode == 'farmer':
            device_id = request.POST.get('device_id')
            if not device_id:
                return render(request, 'login.html', {'error': 'Enter device ID or farmer ID'})
            # try to find farmer
            farmer = Farmer.objects.filter(device_id=device_id).first()
            if not farmer:
                return render(request, 'login.html', {'error': 'No farmer with that device id. Create it from admin first.'})
            # redirect to farmer dashboard (global name used: 'farmer_dashboard')
            return redirect('irrigation:farmer_dashboard', farmer_id=farmer.id)
        else:
            # government login using Django auth
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('irrigation:gov_dashboard')
            return render(request, 'login.html', {'error': 'Invalid government credentials'})
    return render(request, 'login.html')


def logout_view(request):
    """
    Logout and redirect to the login page (global name: 'login').
    IMPORTANT: use the global name because the app is included without a namespace.
    """
    logout(request)
    return redirect('irrigation:login')


# ----- ESP endpoint -----

def esp_endpoint(request, device_id, water_level, ph, ldr, humidity, temp):
    # parse floats
    try:
        water_level_f = float(water_level)
        ph_f = float(ph)
        ldr_f = float(ldr)
        humidity_f = float(humidity)
        temp_f = float(temp)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'invalid numeric payload', 'error': str(e)}, status=400)

    farmer = Farmer.objects.filter(device_id=str(device_id)).first()
    if not farmer:
        return JsonResponse({'status': 'error', 'message': 'farmer not found for device_id {}'.format(device_id)}, status=404)

    prev = SensorReading.objects.filter(farmer=farmer).order_by('-timestamp').first()

    fan = compute_fan_speed(temp_f, humidity_f)
    light_ctrl = compute_light_control(ldr_f)
    prev_level = prev.water_level if prev else None
    water_usage = compute_water_usage(prev_level, water_level_f, farmer.tank_capacity)

    sr = SensorReading.objects.create(
        farmer=farmer,
        water_level=water_level_f,
        ph=ph_f,
        light_intensity=ldr_f,
        humidity=humidity_f,
        temperature=temp_f,
        fan_speed=fan,
        light_control=light_ctrl,
        water_usage=water_usage,
        raw_payload=f"{device_id}/{water_level}/{ph}/{ldr}/{humidity}/{temp}"
    )

    return JsonResponse({'status': 'ok', 'reading_id': sr.id})


# ----- APIs -----

def api_latest_reading(request, farmer_id):
    farmer = get_object_or_404(Farmer, pk=farmer_id)
    latest = farmer.readings.order_by('-timestamp').first()
    if not latest:
        return JsonResponse({'status': 'empty'})
    data = {
        'timestamp': latest.timestamp.isoformat(),
        'water_level': latest.water_level,
        'ph': latest.ph,
        'light_intensity': latest.light_intensity,
        'humidity': latest.humidity,
        'temperature': latest.temperature,
        'fan_speed': latest.fan_speed,
        'light_control': latest.light_control,
        'water_usage': latest.water_usage,
    }
    return JsonResponse({'status': 'ok', 'data': data})


# ----- Dashboards -----

def farmer_dashboard(request, farmer_id):
    farmer = get_object_or_404(Farmer, pk=farmer_id)
    latest = farmer.readings.order_by('-timestamp').first()
    context = {
        'farmer': farmer,
        'latest': latest,
    }
    return render(request, 'farmer_dashboard.html', context)


@login_required
def gov_dashboard(request):
    farmers = Farmer.objects.all().order_by('name')
    selected_id = request.GET.get('farmer')
    selected = None
    if selected_id:
        selected = Farmer.objects.filter(pk=selected_id).first()
    context = {
        'farmers': farmers,
        'selected': selected,
    }
    return render(request, 'gov_dashboard.html', context)


# ----- Chart generation helpers -----

def render_chart_to_response(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    buf.seek(0)
    plt.close(fig)
    return HttpResponse(buf.getvalue(), content_type='image/png')


def chart_water(request, farmer_id):
    farmer = get_object_or_404(Farmer, pk=farmer_id)
    readings = list(farmer.readings.order_by('-timestamp')[:100])[::-1]
    if not readings:
        fig = plt.figure(figsize=(6, 3), facecolor='white')
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, 'No data', ha='center', va='center')
        return render_chart_to_response(fig)

    times = [r.timestamp for r in readings]
    vals = [r.water_level for r in readings]

    fig, ax = plt.subplots(figsize=(8, 3), facecolor='white')
    ax.plot(times, vals, marker='o', linewidth=2, color='blue', label='Water Level')
    ax.fill_between(times, vals, alpha=0.2, color='blue')
    ax.set_title('Water Level')
    ax.set_ylabel('Percent (%)')
    ax.set_ylim(0, 110)
    ax.legend()
    ax.xaxis.set_major_formatter(DateFormatter('%m-%d %H:%M'))
    fig.autofmt_xdate()
    return render_chart_to_response(fig)


def chart_ph(request, farmer_id):
    farmer = get_object_or_404(Farmer, pk=farmer_id)
    readings = list(farmer.readings.order_by('-timestamp')[:100])[::-1]
    if not readings:
        fig = plt.figure(figsize=(6, 3), facecolor='white')
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, 'No data', ha='center', va='center')
        return render_chart_to_response(fig)

    times = [r.timestamp for r in readings]
    vals = [r.ph for r in readings]

    colors = ['violet' if v >= 7 else 'red' for v in vals]

    fig, ax = plt.subplots(figsize=(8, 3), facecolor='white')
    ax.bar(times, vals, color=colors, width=0.02)
    ax.axhline(7.0, linestyle='--', color='black', alpha=0.6, label='Neutral pH 7')
    ax.set_title('pH Level')
    ax.set_ylabel('pH')
    ax.legend()
    ax.xaxis.set_major_formatter(DateFormatter('%m-%d %H:%M'))
    fig.autofmt_xdate()
    return render_chart_to_response(fig)


def chart_temp_humi(request, farmer_id):
    farmer = get_object_or_404(Farmer, pk=farmer_id)
    readings = list(farmer.readings.order_by('-timestamp')[:100])[::-1]
    if not readings:
        fig = plt.figure(figsize=(6, 3), facecolor='white')
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, 'No data', ha='center', va='center')
        return render_chart_to_response(fig)

    times = [r.timestamp for r in readings]
    temps = [r.temperature for r in readings]
    hums = [r.humidity for r in readings]

    x = range(len(times))  # use index for grouped bars
    width = 0.4

    fig, ax = plt.subplots(figsize=(8, 3), facecolor='white')
    ax.bar([i - width/2 for i in x], temps, width=width, color='orange', label='Temp (°C)')
    ax.bar([i + width/2 for i in x], hums, width=width, color='deeppink', label='Humidity (%)')

    ax.set_title('Temperature & Humidity')
    ax.set_ylabel('Values')
    ax.legend()
    ax.set_xticks(x)
    ax.set_xticklabels([t.strftime('%m-%d %H:%M') for t in times], rotation=45, ha='right')

    return render_chart_to_response(fig)

# ----- Chatbot (LLM) -----

import os
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = "mistralai/mistral-small-3.2-24b-instruct-2506"

def call_llm_openrouter(user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a farming assistant. "
                    "Reply in **1-2 short sentences only**. "
                    "Be direct, clear, and accurate about crops, fertilizers, pesticides, or climate. "
                    "Do not give long paragraphs."
                )
            },
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 80,
        "temperature": 0.5,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 429:
            return "Error: Rate limit exceeded (429). You are sending messages too quickly, or the free model limit has been reached. Please wait a moment."
        elif resp.status_code != 200:
            return f"Error: got status {resp.status_code} from LLM. Details: {resp.text}"
        data = resp.json()
        reply = data.get("choices", [])[0].get("message", {}).get("content", "")
        return reply.strip()
    except Exception:
        return "Sorry, I cannot connect to the LLM server right now."


def chatbot_response(request):
    user_message = request.GET.get("message", "").strip()
    if not user_message:
        return JsonResponse({"reply": "Please enter a question."})
    reply = call_llm_openrouter(user_message)
    return JsonResponse({"reply": reply})


def chat_ui(request):
    return render(request, "chatbot/chat.html")
