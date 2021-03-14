from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Button, HTML
from crispy_forms.bootstrap import FormActions
from django.contrib.auth.models import Group, User

from .models import Topic, Noted, Template, ReviewLog

# class TopicForm (forms.ModelForm):
# 	class Meta:
# 		model = Topic
# 		fields = [
# 			'name',		
# 		]
# #		fields = "__all__"

# 	def clean(self):
# 		cleaned_data = super().clean()
# 		short_desc  = cleaned_data.get("short_desc")
# 		assigned_to = cleaned_data.get("assigned_to")
# 		if not (short_desc):
# 			self.add_error('short_desc', "Short Description is empty")
# 		if not (assigned_to):
# 			self.add_error('assigned_to', "Assigned To is empty")

# 		return cleaned_data

class NoteForm (forms.ModelForm):
	class Meta:
		model = Noted
		fields = [
			'name',		
		]
		fields = "__all__"		

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

#	def clean(self):
#		print ("Calling Clean Start date --> (1)")
#		self.cleaned_data['id_todo'] = 95
#		return super(TodoNotesForm, self).clean()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'POST'
		self.helper.layout = Layout (
			Row(
				Column(HTML('<textarea class="form-control" placeholder="Add a note here..." name="notes" id="notes" maxlength="300"></textarea>'),
					css_class='form-group col-md-11 mb-0'),
				Column(
				FormActions(
        			Submit( 'post', 'Post', css_class = 'btn btn-success')),
					css_class='form-group col-md-1 mb-0'),
				css_class='form-row'
			),
			Row (
				Column('usernotem'),
				Column('cuser'),
			)
		)
