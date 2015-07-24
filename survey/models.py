from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from django.db.models.signals import post_save


class Encuesta(models.Model):
	name = models.CharField('Nombre', max_length=400)
	description = models.TextField('Descripcion')

	def __unicode__(self):
		return (self.name)

	def questions(self):
		if self.pk:
			return Pregunta.objects.filter(survey=self.pk)
		else:
			return None

	def categories(self):
		if self.pk:
			return Pagina.objects.extra(select={'intname': 'CAST(name AS INTEGER)'}).filter(survey=self.pk).order_by('-intname')
			#return Pagina.objects.filter(survey=self.pk)
		else:
			return None

class Pagina(models.Model):
	#Funcionan como paginas
	name = models.CharField('Numero', max_length=40)
	titulo = models.CharField('Titulo', max_length=400)	
	survey = models.ForeignKey(Encuesta)

	def __unicode__(self):
		return (self.name)

def validate_list(value):
	'''takes a text value and verifies that there is at least one comma '''
	values = value.split(',')
	if len(values) < 2:
		raise ValidationError("The selected field requires an associated list of choices. Choices must contain more than one item.")

class Pregunta(models.Model):
	TEXT = 'text'
	RADIO = 'radio'
	SELECT = 'select'
	SELECT_MULTIPLE = 'select-multiple'
	INTEGER = 'integer'

	QUESTION_TYPES = (
		(TEXT, 'text'),
		(RADIO, 'radio'),
		(SELECT, 'select'),
		(SELECT_MULTIPLE, 'Select Multiple'),
		(INTEGER, 'integer'),
	)

	text = models.TextField('Pregunta')
	required = models.BooleanField('Requerido')
	category = models.ForeignKey(Pagina, blank=True, null=True,) 
	survey = models.ForeignKey(Encuesta)
	question_type = models.CharField('Tipo de Pregunta', max_length=200, choices=QUESTION_TYPES, default=TEXT)
	# the choices field is only used if the question type 
	choices = models.TextField('Opciones', blank=True, null=True,
		help_text='Si es "radio," "select," or "select multiple" ingrese una lista de elementos separados por comas.')
	choices_salta_a_opcion = models.CharField('Opcion que salta a',max_length=100, null=True, blank=True)
	choices_salta_a_numero = models.IntegerField('Opcion salta a pagina', null=True, blank=True)
	choice_salta_por_default = models.IntegerField('Por default salta a')

	def save(self, *args, **kwargs):
		if (self.question_type == Pregunta.RADIO or self.question_type == Pregunta.SELECT 
			or self.question_type == Pregunta.SELECT_MULTIPLE):
			validate_list(self.choices)
		super(Pregunta, self).save(*args, **kwargs)

	def get_choices(self):
		''' parse the choices field and return a tuple formatted appropriately
		for the 'choices' argument of a form widget.'''
		choices = self.choices.split(',')
		choices_list = []
		for c in choices:
			c = c.strip()
			choices_list.append((c,c))
		choices_tuple = tuple(choices_list)
		return choices_tuple

	def __unicode__(self):
		return (self.text)

class Response(models.Model):	
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	survey = models.ForeignKey(Encuesta)
	interviewee = models.ForeignKey(User,related_name='user_estudiante', null=False)		#Este usuario solo puede acceder + GESTORES (VER UNIQUE=TRUE)	
	category = models.ForeignKey(Pagina)
	#Agrego
	question = models.ForeignKey(Pregunta)
	answertype = models.CharField(max_length=12)
	answervalue = models.CharField(max_length=400)
	
	def __unicode__(self):
		return ("%s - %s -  %s" % (self.survey.name, self.interviewee, 'Pagina ' + self.category.name))
		
class Contacto(models.Model):
	
	CONTACT_TYPES = (
		('', ''),
		('mail', 'Mail'),
		('telefono', 'Telefono'),
		('personal', 'Personal'),
		('chat', 'Chat'),		
	)

	user = models.ForeignKey(User)
	fecha = models.DateTimeField('Fecha de Contacto', blank=False, null=False)	
	tipocontacto = models.CharField('Tipo de Contacto', max_length=100, choices=CONTACT_TYPES, default='', blank=False, null=False)
	observaciones = models.TextField(blank=True, null=True)
	

    