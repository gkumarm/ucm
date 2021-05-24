from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Button, HTML
from crispy_forms.bootstrap import FormActions
from django.contrib.auth.models import Group, User

from .models import Topic, Notem, Noted, Template, ReviewLog, NOTE_TYPES

class TopicForm (forms.ModelForm):
	# title = forms.CharField (widget = forms.TextInput (attrs={
	# 		'autocomplete': 'off',
	# 		'placeholder' : 'Topic Title',
	# 	}))

	class Meta:
		model = Topic
		fields = ['title', 'description','imagefile', ]
		labels = {
			'title': '',
			'description': ''
		}

		widgets = {
			"title": forms.TextInput(
				attrs={
					"required": True,
					'autocomplete': 'off',
					"placeholder": "Enter a topic title here",
					"label": "xx",
				}
			),
			"description": forms.Textarea(
				attrs={
					'required': True,
					'rows':'4',
					'autocomplete': 'off',
					"placeholder": 'Enter meaningful description here',
					'maxlength' : "300",
					"label": "xx",
				}
			),		
		}	
	# short_desc    = forms.CharField (widget = forms.TextInput (attrs={'autocomplete': 'off'}))
	# group         = forms.ModelChoiceField(queryset=Group.objects.none(), required=False)
	# assigned_to   = forms.ModelChoiceField(queryset=Resource.objects.none(), required=False)
	# created_by    = forms.CharField (disabled=True, required=False)
	# context_id    = forms.ModelChoiceField(queryset=Context.objects.all(), to_field_name='context_id',
	# 				required=False, widget=autocomplete.ModelSelect2(url='context-autocomplete'))
	# todo_type     = forms.ModelChoiceField(queryset=TodoType.objects.all().order_by('name'), to_field_name='code', required=False)
	# status        = forms.ModelChoiceField(queryset=TodoStatus.objects.all().order_by('name'), to_field_name='code', required=False)
	# start_date    = forms.DateTimeField (input_formats=['%d-%b-%Y'],
    #                        label='Start Date',
    #                        required=False,
    #                        widget=forms.DateInput(
    #                                format='%d-%b-%Y',
    #                                attrs={'autocomplete': 'off', 'placeholder': 'Select a date', 'class': 'datepicker'})
    #                        )
	# end_date   = forms.DateTimeField (input_formats=['%d-%b-%Y'],
    #                        label='End Date',
    #                        required=False,
    #                        widget=forms.DateInput(
    #                                format='%d-%b-%Y',
    #                                attrs={'autocomplete': 'off', 'placeholder': 'Select a date', 'class': 'datepicker'})
    #                        )

class NotemForm (forms.ModelForm):
	class Meta:
		model = Notem
		fields = ['name']

class NotedForm (forms.ModelForm):
	ndata = forms.CharField(widget=forms.Textarea (attrs={'rows':'2'}), label='Content:')

	class Meta:
		model = Noted
		fields = ['ntype', 'ndata', 'norder']
		labels = {
			'ntype': 'Type:',
			'norder': 'Display Order:',			
		}		
		widgets = {
			'norder': forms.NumberInput(attrs={'min': '1'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.helper = FormHelper()

class TemplateForm (forms.ModelForm):
	class Meta:
		model = Template
		fields = "__all__"

class ReviewLogForm (forms.ModelForm):
	class Meta():
		model = ReviewLog
		fields = ('usernotem', 'cuser', 'notes')
		widgets = {
			'usernotem': forms.HiddenInput(),
			'cuser': forms.HiddenInput(),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'POST'
		self.helper.layout = Layout (
		Row (
			Column(HTML('<textarea class="form-control" placeholder="Add a note here..." name="notes" id="notes" maxlength="300"></textarea>'),
				css_class='form-group col-10 col-lg-10 col-md-8 mb-2'),
			Column(HTML('<button class="form-control btn btn-success" type="submit" name="post" id="post" value="Post">Post</button>'),
				css_class='form-group col-auto mb-2'),
				css_class='row'
		),
		Row (  
				Column('usernotem'),
				Column('cuser'),
			)
		)

NotemFormSet = forms.modelformset_factory(
		Notem,
		form=NotemForm, 
		extra=1,
        can_delete=True,		
	)

NotedFormSet = inlineformset_factory (
        Notem,
        Noted,
        form = NotedForm,
        extra=1,
        can_delete=True,
    )
