from django.contrib import admin

# Register your models here.
# Register your models here.
from .models import Topic, Notem, Noted, Template, UserTopic, UserNotem, UserNotemLog, UserLearningDeck

admin.site.register (Topic)
#admin.site.register (Notem)
#admin.site.register (Noted)
admin.site.register (Template)
admin.site.register (UserTopic)
#admin.site.register (UserNotem)
#admin.site.register (UserNotemLog)
#admin.site.register (UserLearningDeck)

class NotedTabularInline (admin.TabularInline):
	model = Noted

class NotemAdmin (admin.ModelAdmin):
	inlines = [NotedTabularInline]
	class Meta:
		model = Notem

#    list_display = ('title', 'author', 'display_genre')

admin.site.register (Notem, NotemAdmin)    