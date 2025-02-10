from rest_framework.serializers import ModelSerializer, SerializerMethodField

from core.models import Favorito


class FavoritoSerializer(ModelSerializer):
    class Meta:
        model = Favorito
        fields = ["nota", "comentario"]

    def create(self, validated_data):
        # Pega usuario e livro do contexto
        usuario = self.context["usuario"]
        livro = self.context["livro"]
        
        # Adiciona usuario e livro aos dados validados
        validated_data["usuario"] = usuario
        validated_data["livro"] = livro
        
        return super().create(validated_data)


class FavoritoDetailSerializer(ModelSerializer):
    livro_titulo = SerializerMethodField()
    
    class Meta:
        model = Favorito
        fields = "__all__"
    
    def get_livro_titulo(self, obj):
        return obj.livro.titulo
