# Generated by Django 3.2.3 on 2021-05-31 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_alter_chat_messages'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='group',
            field=models.BooleanField(default=False),
        ),
    ]