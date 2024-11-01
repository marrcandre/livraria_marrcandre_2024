from rest_framework.serializers import (
    DecimalField,
    ModelSerializer,
    Serializer,
    SlugRelatedField,
    ValidationError,
)

from core.models import Livro
from uploader.models import Image
from uploader.serializers import ImageSerializer


class LivroRetrieveSerializer(ModelSerializer):
    capa = ImageSerializer(required=False)

    class Meta:
        model = Livro
        fields = "__all__"
        depth = 1


class LivroListSerializer(ModelSerializer):
    class Meta:
        model = Livro
        fields = ["id", "titulo", "preco"]


class LivroSerializer(ModelSerializer):
    capa_attachment_key = SlugRelatedField(
        source="capa",
        queryset=Image.objects.all(),
        slug_field="attachment_key",
        required=False,
        write_only=True,  # Não será exibido na resposta
    )
    capa = ImageSerializer(required=False, read_only=True)  # Não será usado para criar ou atualizar

    class Meta:
        model = Livro
        fields = "__all__"


class LivroAlterarPrecoSerializer(Serializer):
    preco = DecimalField(max_digits=10, decimal_places=2)

    def validate_preco(self, value):
        """Valida se o preço é um valor positivo."""
        if value <= 0:
            raise ValidationError("O preço deve ser um valor positivo.")
        return value
