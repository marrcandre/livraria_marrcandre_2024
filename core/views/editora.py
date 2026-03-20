from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from core.models import Editora
from core.serializers import EditoraSerializer


class EditoraViewSet(ModelViewSet):
    queryset = Editora.objects.order_by('-id')
    serializer_class = EditoraSerializer
    search_fields = ['nome', 'cidade']
    filter_backends = (SearchFilter, OrderingFilter)
