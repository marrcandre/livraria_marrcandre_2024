# TODO: Modificar nomes dos serializers para padrão EntidadeMetodosSerializer

from rest_framework.serializers import (
    CharField,
    CurrentUserDefault,
    DateTimeField,
    HiddenField,
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
)

from core.models import Compra, ItensCompra


class ItensCompraSerializer(ModelSerializer):
    total = SerializerMethodField()

    def get_total(self, item):
        return item.preco * item.quantidade

    class Meta:
        model = ItensCompra
        fields = ("livro", "quantidade", "preco", "total")
        depth = 1


class CriarEditarItensCompraSerializer(ModelSerializer):
    class Meta:
        model = ItensCompra
        fields = ("livro", "quantidade")

    def validate(self, item):
        if item["quantidade"] > item["livro"].quantidade:
            raise ValidationError({"quantidade": "Quantidade solicitada não disponível em estoque."})
        return item

    def validate_quantidade(self, value):
        if value <= 0:
            raise ValidationError("A quantidade deve ser maior que zero.")
        return value


class CompraSerializer(ModelSerializer):
    usuario = CharField(source="usuario.email", read_only=True)
    status = CharField(source="get_status_display", read_only=True)
    data = DateTimeField(read_only=True)
    tipo_pagamento = CharField(source="get_tipo_pagamento_display", read_only=True) # novo campo
    itens = ItensCompraSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
        fields = ("id", "usuario", "status", "total", "data", "tipo_pagamento", "itens") # modificado


class CriarEditarCompraSerializer(ModelSerializer):
    usuario = HiddenField(default=CurrentUserDefault())
    itens = CriarEditarItensCompraSerializer(many=True)

    class Meta:
        model = Compra
        fields = ("usuario", "itens")

    def create(self, validated_data):
        itens = validated_data.pop("itens")
        compra = Compra.objects.create(**validated_data)
        for item in itens:
            item["preco"] = item["livro"].preco  # nova linha
            ItensCompra.objects.create(compra=compra, **item)
        return compra

    def update(self, compra, validated_data):
        itens = validated_data.pop("itens")
        if itens:
            compra.itens.all().delete()
            for item in itens:
                item["preco"] = item["livro"].preco  # nova linha
                ItensCompra.objects.create(compra=compra, **item)
        compra.save()
        return super().update(compra, validated_data)
