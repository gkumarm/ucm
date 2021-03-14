from django import template

register = template.Library()

@register.filter(name='progress_get_class_name')
def progress_get_class_name(idx):
	switcher = {
		1:'bg-danger',
		2:'bg-warning',
		3:'bg-info',
		4:' ',	# Blue
		5:'bg-success',
	}
	return switcher.get(idx,' ')

@register.filter(name='expluralize')
def expluralize(nCount,sText):
	if nCount > 1:
		return str(nCount) + ' ' + sText + 's'
	else:
		return str(nCount) + ' ' + sText