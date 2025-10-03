from django.db.models.aggregates import Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Compra, Favorito, ItensCompra, Livro
from core.serializers import (
    CompraSerializer,
    FavoritoSerializer,
    LivroAdicionarAoCarrinhoSerializer,
    LivroAjustarEstoqueSerializer,
    LivroAlterarPrecoSerializer,
    LivroListSerializer,
    LivroRetrieveSerializer,
    LivroSerializer,
)


class LivroViewSet(ModelViewSet):
    queryset = Livro.objects.order_by('-id')
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['categoria__descricao', 'editora__nome']
    search_fields = ['titulo']
    ordering_fields = ['titulo', 'preco']
    ordering = ['titulo']

    def get_serializer_class(self):
        if self.action == 'list':
            return LivroListSerializer
        elif self.action == 'retrieve':
            return LivroRetrieveSerializer

        return LivroSerializer

    @extend_schema(
        summary="Alterar preço do livro",
        description="Permite alterar o preço de um livro específico.",
        request=LivroAlterarPrecoSerializer,
        responses={200: None, 400: None, 404: None},
    )
    @action(detail=True, methods=['patch'])
    def alterar_preco(self, request, pk=None):
        livro = self.get_object()

        serializer = LivroAlterarPrecoSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        livro.preco = serializer.validated_data['preco']
        livro.save()

        return Response(
            {'detail': f"Preço do livro '{livro.titulo}' atualizado para {livro.preco}."}, status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Ajustar estoque do livro",
        description="Permite ajustar a quantidade em estoque de um livro específico.",
        request=LivroAjustarEstoqueSerializer,
        responses={200: None, 400: None, 404: None},
    )
    @action(detail=True, methods=['post'])
    def ajustar_estoque(self, request, pk=None):
        livro = self.get_object()

        serializer = LivroAjustarEstoqueSerializer(data=request.data, context={'livro': livro})
        serializer.is_valid(raise_exception=True)

        quantidade_ajuste = serializer.validated_data['quantidade']

        livro.quantidade += quantidade_ajuste
        livro.save()

        return Response(
            {'status': 'Quantidade ajustada com sucesso', 'novo_estoque': livro.quantidade}, status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Livros mais vendidos",
        description="Retorna os livros com mais de 10 unidades vendidas.",
        responses={200: None},
    )
    @action(detail=False, methods=['get'])
    def mais_vendidos(self, request):
        """
        Retorna os livros com mais de 10 unidades vendidas.
        """
        livros = Livro.objects.annotate(total_vendidos=Sum('itenscompra__quantidade')).filter(total_vendidos__gt=10)

        data = [
            {
                'id': livro.id,
                'titulo': livro.titulo,
                'total_vendidos': livro.total_vendidos,
            }
            for livro in livros
        ]

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Adicionar livro ao carrinho",
        description="Adiciona um livro ao carrinho de compras do usuário autenticado.",
        request=LivroAdicionarAoCarrinhoSerializer,
        responses={200: CompraSerializer, 400: None, 404: None},
    )
    @action(detail=True, methods=['post'])
    def adicionar_ao_carrinho(self, request, pk=None):
        livro = self.get_object()

        serializer = LivroAdicionarAoCarrinhoSerializer(data=request.data, context={'livro': livro})
        serializer.is_valid(raise_exception=True)
        quantidade = serializer.validated_data['quantidade']

        compra, created = Compra.objects.get_or_create(usuario=request.user, status=Compra.StatusCompra.CARRINHO)

        item_existente = compra.itens.filter(livro=livro).first()

        if item_existente:
            item_existente.quantidade += quantidade
            item_existente.preco = livro.preco
            item_existente.save()
        else:
            ItensCompra.objects.create(compra=compra, livro=livro, quantidade=quantidade, preco=livro.preco)

        compra_serializada = CompraSerializer(compra)
        return Response(compra_serializada.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Favoritar livro",
        description="Favorita um livro ou atualiza os dados (nota e/ou comentário) de um favorito existente.",
        request=FavoritoSerializer,
        responses={200: FavoritoSerializer, 201: FavoritoSerializer, 400: None, 404: None},
    )
    @action(detail=True, methods=['post', 'put', 'patch'])
    def favoritar(self, request, pk=None):
        """
        Favorita um livro ou atualiza os dados (nota e/ou comentário) de um favorito existente.
        """
        livro = self.get_object()
        favorito = Favorito.objects.filter(usuario=request.user, livro=livro).first()

        if not favorito and request.method in {'PUT', 'PATCH'}:
            return Response({'error': 'Livro não está na sua lista de favoritos'}, status=status.HTTP_404_NOT_FOUND)

        if favorito:
            # Atualiza favorito existente
            serializer = FavoritoSerializer(
                favorito, data=request.data, partial=True, context={'livro': livro, 'usuario': request.user}
            )
        else:
            # Cria novo favorito
            serializer = FavoritoSerializer(data=request.data, context={'livro': livro, 'usuario': request.user})

        serializer.is_valid(raise_exception=True)
        serializer.save()

        status_code = status.HTTP_200_OK if favorito else status.HTTP_201_CREATED
        return Response(serializer.data, status=status_code)
