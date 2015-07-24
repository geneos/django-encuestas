from survey.models import Pregunta, Pagina, Encuesta, Response, Contacto#, AnswerText, AnswerRadio, AnswerSelect, AnswerInteger, AnswerSelectMultiple
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

class PreguntaInline(admin.TabularInline):
	model = Pregunta
	ordering = ('category',)
	extra = 0

class PaginaInline(admin.TabularInline):
	model = Pagina
	extra = 0

class EncuestaAdmin(admin.ModelAdmin):
	inlines = [PaginaInline, PreguntaInline]

class ResponseAdmin(admin.ModelAdmin):
	#list_display = ('interview_uuid', 'interviewer', 'created') 
	#inlines = [AnswerTextInline, AnswerRadioInline, AnswerSelectInline, AnswerSelectMultipleInline, AnswerIntegerInline]
	# specifies the order as well as which fields to act on 
	readonly_fields = ('survey', 'created', 'updated')

admin.site.register(Pregunta)
admin.site.register(Encuesta, EncuestaAdmin)
admin.site.register(Response, ResponseAdmin)

admin.site.register(Contacto)

#class ContactoInline(admin.TabularInline):
#	model = Contacto
#	extra = 0

