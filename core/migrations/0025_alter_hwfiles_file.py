# Generated by Django 5.1.1 on 2024-10-11 18:46

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_alter_hwfiles_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hwfiles',
            name='file',
            field=cloudinary.models.CloudinaryField(max_length=255, verbose_name='hw'),
        ),
    ]
