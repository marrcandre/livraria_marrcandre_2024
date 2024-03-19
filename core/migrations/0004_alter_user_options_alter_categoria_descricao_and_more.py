# Generated by Django 5.0.2 on 2024-03-19 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_editora"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={"verbose_name": "Usuário", "verbose_name_plural": "Usuários"},
        ),
        migrations.AlterField(
            model_name="categoria",
            name="descricao",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="editora",
            name="nome",
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
