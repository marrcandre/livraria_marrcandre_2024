# Generated by Django 5.1.3 on 2025-02-10 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0031_favorito"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="favorito",
            options={"ordering": ["-data_atualizacao"]},
        ),
        migrations.RemoveField(
            model_name="favorito",
            name="data_cadastro",
        ),
        migrations.AddField(
            model_name="favorito",
            name="data_atualizacao",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
