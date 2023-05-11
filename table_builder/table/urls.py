from django.urls import path

from .views import TableCreateView, TableRowCreateView, TableRowListView, TableUpdateView

urlpatterns = [
    path("", TableCreateView.as_view()),
    path("<str:table_name>", TableUpdateView.as_view()),
    path("<str:table_name>/row", TableRowCreateView.as_view()),
    path("<str:table_name>/rows", TableRowListView.as_view()),
]
