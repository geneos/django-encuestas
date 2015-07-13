from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class Survey(models.Model):
	name = models.CharField(max_length=400)
	description = models.TextField()

	def __unicode__(self):
		return (self.name)

	def questions(self):
		if self.pk:
			return Question.objects.filter(survey=self.pk)
		else:
			return None

	def categories(self):
		if self.pk:
			return Category.objects.filter(survey=self.pk)
		else:
			return None

class Category(models.Model):
	#funcionan como paginas
	name = models.CharField(max_length=40)
	titulo = models.CharField(max_length=400)	
	survey = models.ForeignKey(Survey)

	def __unicode__(self):
		return (self.name)

def validate_list(value):
	'''takes a text value and verifies that there is at least one comma '''
	values = value.split(',')
	if len(values) < 2:
		raise ValidationError("The selected field requires an associated list of choices. Choices must contain more than one item.")

class Question(models.Model):
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

	text = models.TextField()
	required = models.BooleanField()
	category = models.ForeignKey(Category, blank=True, null=True,) 
	survey = models.ForeignKey(Survey)
	question_type = models.CharField(max_length=200, choices=QUESTION_TYPES, default=TEXT)
	# the choices field is only used if the question type 
	choices = models.TextField(blank=True, null=True,
		help_text='if the question type is "radio," "select," or "select multiple" provide a comma-separated list of options for this question .')
	choices_salta_a_opcion = models.CharField(max_length=100, null=True, blank=True)
	choices_salta_a_numero = models.IntegerField(null=True, blank=True)
	choice_salta_por_default = models.IntegerField()

	def save(self, *args, **kwargs):
		if (self.question_type == Question.RADIO or self.question_type == Question.SELECT 
			or self.question_type == Question.SELECT_MULTIPLE):
			validate_list(self.choices)
		super(Question, self).save(*args, **kwargs)

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
	survey = models.ForeignKey(Survey)
	interviewee = models.ForeignKey(User,related_name='user_estudiante', null=False)		#Este usuario solo puede acceder + GESTORES (VER UNIQUE=TRUE)	
	category = models.ForeignKey(Category)
	#Agrego
	question = models.ForeignKey(Question)
	answertype = models.CharField(max_length=12)
	answervalue = models.CharField(max_length=400)
	
	def __unicode__(self):
		return ("%s - %s -  %s" % (self.survey.name, self.interviewee, 'Pagina ' + self.category.name))
		#return str(self.survey.name + ' - ' + self.interviewee + ' - Pagina ' + self.category.name)

