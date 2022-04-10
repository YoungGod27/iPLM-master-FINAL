from django.forms import ModelForm
from django import forms
from .models import *

class InputGrades(ModelForm):
	class Meta:
		model = currchecklist
		fields = ('curriculumCode', 'subjectGrades')

class StudentsForm(forms.ModelForm):
	class Meta:
		model = StudentInfo
		fields = 'studentUser','studentSection',
		widgets = {
			'studentUser': forms.Select(
				attrs={"class": "form-control"}),

			'studentSection': forms.Select(
				attrs={
					"class": "form-control",
					"type": "text",
					"placeholder": "1",
					"id": "editprofile"
				}
			)
		}

class studyPlanForm(forms.ModelForm):
	class Meta: 
		model = studyPlan
		fields = 'curricula',
		widgets = {
			'curricula': forms.Select(
				attrs={"class": "form-control","required":True}),
				}
