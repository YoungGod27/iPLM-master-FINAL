import django_filters
from django_filters import *
from django.forms.widgets import TextInput


class Search(django_filters.FilterSet):
    studentID = CharFilter(lookup_expr='icontains', label='',
                             widget=TextInput(attrs={
                                 "type": "text",
                                 "name": "search",
                                 "id": "search",
                                 "placeholder": "Student Number"}))

class Faculty(django_filters.FilterSet):
    facultyID = CharFilter(lookup_expr='icontains', label='',
                             widget=TextInput(attrs={                             
                                "type": "text",
                                 "name": "search",
                                 "id": "search",
                                 "placeholder": "Faculty Number"}))


class ClassCode(django_filters.FilterSet):
    subjectCode = CharFilter(lookup_expr='icontains', label='',
                             widget=TextInput(attrs={'placeholder': 'Subject Code'}))
