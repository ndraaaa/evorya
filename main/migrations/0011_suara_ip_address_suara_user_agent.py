# Generated by Django 4.2 on 2025-07-12 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_logvotingactivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='suara',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='suara',
            name='user_agent',
            field=models.TextField(blank=True, null=True),
        ),
    ]
