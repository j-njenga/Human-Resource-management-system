# Generated by Django 5.0.7 on 2024-08-22 10:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0013_alter_project_members_remove_task_assigned_to_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='department',
        ),
    ]
