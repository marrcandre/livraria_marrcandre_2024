# Generated by Django 5.1.3 on 2024-11-21 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_alter_compra_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="compra",
            name="total",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
