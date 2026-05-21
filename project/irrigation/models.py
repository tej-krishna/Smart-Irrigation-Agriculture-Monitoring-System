from django.db import models

class Farmer(models.Model):
    FARMING_CHOICES = (
        ('traditional', 'Traditional'),
        ('hydroponics', 'Hydroponics'),
    )
    name = models.CharField(max_length=200)
    device_id = models.CharField(max_length=50, unique=True)  # maps to the ESP id
    crop = models.CharField(max_length=200, blank=True)
    farming_type = models.CharField(max_length=50, choices=FARMING_CHOICES, default='traditional')
    tank_capacity = models.FloatField(default=1000.0, help_text='Tank capacity in liters (used to compute water usage)')

    def __str__(self):
        return f"{self.name} ({self.device_id})"

class SensorReading(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField(auto_now_add=True)
    water_level = models.FloatField()
    ph = models.FloatField()
    light_intensity = models.FloatField()
    humidity = models.FloatField()
    temperature = models.FloatField()

    # derived
    fan_speed = models.FloatField(null=True, blank=True)
    light_control = models.FloatField(null=True, blank=True)
    water_usage = models.FloatField(null=True, blank=True)

    raw_payload = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Reading {self.id} for {self.farmer} @ {self.timestamp.isoformat()}"
