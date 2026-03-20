from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from core.models import Autor
from core.serializers import AutorSerializer


class AutorViewSet(ModelViewSet):
    queryset = Autor.objects.order_by('-id')
    serializer_class = AutorSerializer
    search_fields = ['nome']
    filter_backends = (SearchFilter, OrderingFilter)
