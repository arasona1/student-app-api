# Generated by Django 3.2.25 on 2024-04-01 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('courses', models.TextField(blank=True)),
                ('email', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
                ('birthday', models.CharField(max_length=255)),
            ],
        ),
    ]