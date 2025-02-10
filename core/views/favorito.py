from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Favorito, Livro
from core.serializers.favorito import (
    FavoritoDetailSerializer,
    FavoritoSerializer,
)
from core.serializers.livro import LivroComFavoritosSerializer


class FavoritoViewSet(ModelViewSet):
    queryset = Favorito.objects.all()
    serializer_class = FavoritoSerializer

    def get_queryset(self):
        # Filtra favoritos apenas do usuário logado
        return self.queryset.filter(usuario=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return FavoritoDetailSerializer
        return FavoritoSerializer

    def perform_create(self, serializer):
        # Automaticamente define o usuário como o usuário logado
        serializer.save(usuario=self.request.user)

    @action(detail=False, methods=["get"])
    def livros_com_estatisticas(self, request):
        # Retorna apenas os livros que têm favoritos
        livros = Livro.objects.filter(favoritos__isnull=False).distinct()
        serializer = LivroComFavoritosSerializer(livros, many=True)
        return Response(serializer.data)
