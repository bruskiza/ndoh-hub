# Generated by Django 2.2.4 on 2019-10-31 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("eventstore", "0008_add_chw_registration")]

    operations = [
        migrations.AlterField(
            model_name="chwregistration",
            name="passport_country",
            field=models.CharField(
                blank=True,
                choices=[
                    ("zw", "Zimbabwe"),
                    ("mz", "Mozambique"),
                    ("mw", "Malawi"),
                    ("ng", "Nigeria"),
                    ("cd", "DRC"),
                    ("so", "Somalia"),
                    ("other", "Other"),
                ],
                max_length=5,
            ),
        ),
        migrations.AlterField(
            model_name="postbirthregistration",
            name="passport_country",
            field=models.CharField(
                blank=True,
                choices=[
                    ("zw", "Zimbabwe"),
                    ("mz", "Mozambique"),
                    ("mw", "Malawi"),
                    ("ng", "Nigeria"),
                    ("cd", "DRC"),
                    ("so", "Somalia"),
                    ("other", "Other"),
                ],
                max_length=5,
            ),
        ),
        migrations.AlterField(
            model_name="prebirthregistration",
            name="passport_country",
            field=models.CharField(
                blank=True,
                choices=[
                    ("zw", "Zimbabwe"),
                    ("mz", "Mozambique"),
                    ("mw", "Malawi"),
                    ("ng", "Nigeria"),
                    ("cd", "DRC"),
                    ("so", "Somalia"),
                    ("other", "Other"),
                ],
                max_length=5,
            ),
        ),
    ]