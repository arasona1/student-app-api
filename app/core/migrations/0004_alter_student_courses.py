# Generated by Django 3.2.25 on 2024-04-01 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20240401_0929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='courses',
            field=models.CharField(max_length=255),
        ),
    ]