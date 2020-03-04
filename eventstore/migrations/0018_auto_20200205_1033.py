# Generated by Django 2.2.8 on 2020-02-05 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("eventstore", "0017_pmtctregistration")]

    operations = [
        migrations.AddField(
            model_name="chwregistration",
            name="channel",
            field=models.CharField(
                choices=[("SMS", "SMS"), ("WhatsApp", "WhatsApp")],
                default="",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="postbirthregistration",
            name="channel",
            field=models.CharField(
                choices=[("SMS", "SMS"), ("WhatsApp", "WhatsApp")],
                default="",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="prebirthregistration",
            name="channel",
            field=models.CharField(
                choices=[("SMS", "SMS"), ("WhatsApp", "WhatsApp")],
                default="",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="publicregistration",
            name="channel",
            field=models.CharField(
                choices=[("SMS", "SMS"), ("WhatsApp", "WhatsApp")],
                default="",
                max_length=8,
            ),
        ),
    ]