# Generated by Django 5.1.3 on 2024-11-21 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0026_alter_compra_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="compra",
            name="status",
            field=models.IntegerField(
                choices=[(1, "Carrinho"), (2, "FInalizado"), (3, "Pago"), (4, "Entregue")], default=1
            ),
        ),
    ]
