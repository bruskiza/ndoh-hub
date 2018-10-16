# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2018-02-12 08:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("registrations", "0009_auto_20171027_0928")]

    operations = [
        migrations.AlterField(
            model_name="registration",
            name="reg_type",
            field=models.CharField(
                choices=[
                    ("momconnect_prebirth", "MomConnect pregnancy registration"),
                    ("momconnect_postbirth", "MomConnect baby registration"),
                    ("whatsapp_prebirth", "WhatsApp MomConnect pregnancy registration"),
                    ("nurseconnect", "Nurseconnect registration"),
                    ("whatsapp_nurseconnect", "WhatsApp Nurseconnect registration"),
                    ("pmtct_prebirth", "PMTCT pregnancy registration"),
                    (
                        "whatsapp_pmtct_prebirth",
                        "WhatsApp PMTCT pregnancy registration",
                    ),
                    ("pmtct_postbirth", "PMTCT baby registration"),
                    ("whatsapp_pmtct_postbirth", "WhatsApp PMTCT baby registration"),
                    ("loss_general", "Loss general registration"),
                ],
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="source",
            name="authority",
            field=models.CharField(
                choices=[
                    ("patient", "Patient"),
                    ("advisor", "Trusted Advisor"),
                    ("hw_partial", "Health Worker Partial"),
                    ("hw_full", "Health Worker Full"),
                ],
                max_length=30,
            ),
        ),
    ]
