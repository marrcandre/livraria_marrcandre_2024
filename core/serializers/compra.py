from rest_framework.serializers import (
    CharField,
    CurrentUserDefault,
    DateTimeField,
    HiddenField,
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField,
    ValidationError,
)

from core.models import Compra, ItensCompra, Livro
from core.serializers.livro import Serializer


class ItensCompraCreateUpdateSerializer(ModelSerializer):
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


class ItensCompraListSerializer(ModelSerializer):
    livro = CharField(source="livro.titulo", read_only=True)

    class Meta:
        model = ItensCompra
        fields = ("livro", "quantidade", "preco")
        depth = 1


class ItensCompraSerializer(ModelSerializer):
    total = SerializerMethodField()

    def get_total(self, item):
        return item.preco * item.quantidade

    class Meta:
        model = ItensCompra
        fields = ("livro", "quantidade", "preco", "total")
        depth = 1


class CompraCreateUpdateSerializer(ModelSerializer):
    usuario = HiddenField(default=CurrentUserDefault())
    itens = ItensCompraCreateUpdateSerializer(many=True)

    class Meta:
        model = Compra
        fields = ("usuario", "itens")

    def create(self, validated_data):
        itens = validated_data.pop("itens")
        usuario = validated_data["usuario"]

        compra, criada = Compra.objects.get_or_create(
            usuario=usuario, status=Compra.StatusCompra.CARRINHO, defaults=validated_data
        )

        for item in itens:
            item_existente = compra.itens.filter(livro=item["livro"]).first()

            if item_existente:
                item_existente.quantidade += item["quantidade"]
                item_existente.preco = item["livro"].preco
                item_existente.save()
            else:
                item["preco"] = item["livro"].preco
                ItensCompra.objects.create(compra=compra, **item)

        compra.save()
        return compra

    def update(self, compra, validated_data):
        itens = validated_data.pop("itens", [])
        if itens:
            compra.itens.all().delete()
            for item in itens:
                item["preco"] = item["livro"].preco
                ItensCompra.objects.create(compra=compra, **item)

        return super().update(compra, validated_data)


class CompraListSerializer(ModelSerializer):
    usuario = CharField(source="usuario.email", read_only=True)
    status = CharField(source="get_status_display", read_only=True)
    itens = ItensCompraListSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
        fields = ("id", "usuario", "status", "total", "itens")


class CompraSerializer(ModelSerializer):
    usuario = CharField(source="usuario.email", read_only=True)
    status = CharField(source="get_status_display", read_only=True)
    data = DateTimeField(read_only=True)
    tipo_pagamento = CharField(source="get_tipo_pagamento_display", read_only=True)  # novo campo
    itens = ItensCompraSerializer(many=True, read_only=True)

    class Meta:
        model = Compra
        fields = ("id", "usuario", "status", "total", "data", "tipo_pagamento", "itens")  # modificado


class CompraAdicionarLivroAoCarrinhoSerializer(Serializer):
    livro_id = PrimaryKeyRelatedField(queryset=Livro.objects.all())
    quantidade = IntegerField(min_value=1, default=1)

    def validate(self, data):
        if data["quantidade"] > data["livro_id"].quantidade:
            raise ValidationError({"quantidade": "Quantidade solicitada não disponível em estoque."})
        return data
