# Generated by Django 5.0.7 on 2024-08-28 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0014_remove_project_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='hod',
            name='profile_pic',
            field=models.FileField(default=1, upload_to=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='staff',
            name='profile_pic',
            field=models.FileField(default=1, upload_to=''),
            preserve_default=False,
        ),
    ]
