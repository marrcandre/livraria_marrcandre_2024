from django.db import transaction
from django.utils import timezone

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Compra, User
from core.models.compra import ItensCompra
from core.serializers import (
    CompraAdicionarLivroAoCarrinhoSerializer,
    CompraCreateUpdateSerializer,
    CompraListSerializer,
    CompraSerializer,
)


class CompraViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["usuario__email", "status", "data"]
    search_fields = ["usuario__email"]
    ordering_fields = ["usuario__email", "status", "data"]
    ordering = ["-data"]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        if usuario.is_superuser:
            return Compra.objects.order_by("-id")
        if usuario.groups.filter(name="administradores"):
            return Compra.objects.order_by("-id")
        if usuario.tipo_usuario == User.TipoUsuario.GERENTE:
            return Compra.objects.order_by("-id")
        return Compra.objects.filter(usuario=usuario)

    def get_serializer_class(self):
        if self.action == "list":
            return CompraListSerializer
        if self.action in ("create", "update"):
            return CompraCreateUpdateSerializer
        return CompraSerializer

    @action(detail=True, methods=["post"])
    def finalizar(self, request, pk=None):
        compra = self.get_object()

        if compra.status != Compra.StatusCompra.CARRINHO:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"status": "Compra já finalizada"},
            )

        with transaction.atomic():
            for item in compra.itens.all():
                if item.quantidade > item.livro.quantidade:
                    return Response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data={
                            "status": "Quantidade insuficiente",
                            "livro": item.livro.titulo,
                            "quantidade_disponivel": item.livro.quantidade,
                        },
                    )

                item.livro.quantidade -= item.quantidade
                item.livro.save()

            compra.status = Compra.StatusCompra.FINALIZADO
            compra.save()

        return Response(status=status.HTTP_200_OK, data={"status": "Compra finalizada"})

    @action(detail=False, methods=["get"])
    def relatorio_vendas_mes(self, request):
        agora = timezone.now()
        inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        compras = Compra.objects.filter(status=Compra.StatusCompra.FINALIZADO, data__gte=inicio_mes)

        total_vendas = sum(compra.total for compra in compras)
        quantidade_vendas = compras.count()

        return Response(
            {
                "status": "Relatório de vendas deste mês",
                "total_vendas": total_vendas,
                "quantidade_vendas": quantidade_vendas,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def adicionar_ao_carrinho(self, request):
        serializer = CompraAdicionarLivroAoCarrinhoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        livro = serializer.validated_data["livro_id"]
        quantidade = serializer.validated_data["quantidade"]
        usuario = request.user

        if not usuario.is_authenticated:
            return Response(
                {"detail": "Autenticação necessária."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        compra, criada = Compra.objects.get_or_create(
            usuario=usuario,
            status=Compra.StatusCompra.CARRINHO,
            defaults={"tipo_pagamento": Compra.TipoPagamento.CARTAO_CREDITO},
        )

        item_existente = compra.itens.filter(livro=livro).first()
        if item_existente:
            item_existente.quantidade += quantidade
            item_existente.save()
        else:
            ItensCompra.objects.create(
                compra=compra,
                livro=livro,
                quantidade=quantidade,
                preco=livro.preco,
            )

        compra_serializada = CompraSerializer(compra)

        return Response(
            compra_serializada.data,
            status=status.HTTP_200_OK if not criada else status.HTTP_201_CREATED,
        )
