from rest_framework import serializers

from .models import CarBrand


class CarBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarBrand
        fields = [
            "brand_id",
            "brand_name",
            "brand_photo",
        ]


