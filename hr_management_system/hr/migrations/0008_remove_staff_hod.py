# Generated by Django 5.0.6 on 2024-07-03 09:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0007_staff_hod'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='staff',
            name='hod',
        ),
    ]
