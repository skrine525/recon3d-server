# Generated by Django 5.2.1 on 2025-07-01 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reconstruction', '0007_reconstruction_plan_signs'),
    ]

    operations = [
        migrations.AddField(
            model_name='reconstruction',
            name='rooms',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
