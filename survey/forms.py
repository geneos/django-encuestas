from django import forms
from django.forms import models
from survey.models import Question, Category, Survey, Response#, AnswerText, AnswerRadio, AnswerSelect, AnswerInteger, AnswerSelectMultiple
from django.utils.safestring import mark_safe
import uuid

class HorizontalRadioRenderer(forms.RadioSelect.renderer):
  def render(self):
    return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))


class ResponseForm(models.ModelForm):
	class Meta:
		model = Response	
		exclude = ('survey', 'interviewee', 'category', 'question', 'answertype', 'answervalue')

	def __init__(self, *args, **kwargs):
		# expects a survey object to be passed in initially
		
		
		#Capturo Parametros	
		p = kwargs.pop('category')
		user = kwargs.pop('interviewee')
		response_id = kwargs.pop('id')
		survey = kwargs.pop('survey')
		data = kwargs.get('data')

		answer_for_questions = None
		#Si es edicion, viene un response_id (ultima pagina cargada)
		if response_id != '0':
			#Traigo la respuesta completa 			
			response = Response.objects.filter(id=response_id)
			for r in response:
				#Traigo todas las respuestas de esa pagina			
				answer_for_questions = Response.objects.filter(interviewee=r.interviewee,survey=r.survey,category=r.category).order_by('question')
				#answer_for_questions = Response.objects.filter(interviewee=r.interviewee,survey=r.survey,category=p).order_by('question')

		#Inicializo el FORM
		super(ResponseForm, self).__init__(*args, **kwargs)				
		#Traigo las preguntas de esa pagina
		questions = survey.questions().filter(category=p)

		for q in questions.order_by('id'):
			if q.question_type == Question.TEXT:
				self.fields["question_%d" % q.pk] = forms.CharField(label=q.text, 
					widget=forms.Textarea)				
			elif q.question_type == Question.RADIO:
				question_choices = q.get_choices()
				self.fields["question_%d" % q.pk] = forms.ChoiceField(label=q.text, 
					widget=forms.RadioSelect(), 
					choices = question_choices)												
			elif q.question_type == Question.SELECT:
				question_choices = q.get_choices()
				# add an empty option at the top so that the user has to
				# explicitly select one of the options
				question_choices = tuple([('', '-------------')]) + question_choices
				self.fields["question_%d" % q.pk] = forms.ChoiceField(label=q.text, 
					widget=forms.Select, choices = question_choices)
			elif q.question_type == Question.SELECT_MULTIPLE:
				question_choices = q.get_choices()
				self.fields["question_%d" % q.pk] = forms.MultipleChoiceField(label=q.text, 
					widget=forms.CheckboxSelectMultiple, choices = question_choices)
			elif q.question_type == Question.INTEGER:
				self.fields["question_%d" % q.pk] = forms.IntegerField(label=q.text)				
			
			# if the field is required, give it a corresponding css class.
			if q.required:
				self.fields["question_%d" % q.pk].required = True
				self.fields["question_%d" % q.pk].widget.attrs["class"] = "required"
			else:
				self.fields["question_%d" % q.pk].required = False
			
			# add the category as a css class, and add it as a data attribute
			# as well (this is used in the template to allow sorting the
			# questions by category)
			if q.category:
				classes = self.fields["question_%d" % q.pk].widget.attrs.get("class")
				if classes:
					self.fields["question_%d" % q.pk].widget.attrs["class"] = classes + (" cat_%s" % q.category.name)
				else:
					self.fields["question_%d" % q.pk].widget.attrs["class"] = (" cat_%s" % q.category.name)
				self.fields["question_%d" % q.pk].widget.attrs["category"] = q.category.name


			# initialize the form field with values from a POST request, if any.
			if data:
				self.fields["question_%d" % q.pk].initial = data.get('question_%d' % q.pk)
	
			#Si es edicion de encuesta ya cargada, cargo el valor inicial de los campos			
			if response_id != '0' and answer_for_questions is not None:
				for answer in answer_for_questions:					
					if q.pk == answer.question.id:						
						self.fields["question_%d" % q.pk].initial = answer.answervalue


	def save(self, user, field_name, field_value, response_id, commit=True):

		
		#Response Nuevo
		if response_id == '0':
			#Creo el objeto response
			response = super(ResponseForm, self).save(commit=False)							
			response.survey = self.survey
			response.category = self.category
			response.interviewee = user

			q_id = int(field_name.split("_")[1])
			q = Question.objects.get(pk=q_id)
			#Guardo la question
			response.question = q
							
			if q.question_type == Question.TEXT:
				response.answertype = 'TEXT'
				response.answervalue = field_value
			elif q.question_type == Question.RADIO:
				response.answertype = 'RADIO'
				response.answervalue = field_value
			elif q.question_type == Question.SELECT:
				response.answertype = 'SELECT'
				response.answervalue = field_value				
			elif q.question_type == Question.SELECT_MULTIPLE:
				response.answertype = 'MULTIPLE'
				response.answervalue = field_value					
			elif q.question_type == Question.INTEGER:	
				response.answertype = 'INTEGER'
				response.answervalue = field_value
						
			response.save()
		else:
			#Response ya existe
			responses = Response.objects.filter(id=response_id)
			if responses:
				for response in responses:
					q_id = int(field_name.split("_")[1])
					q = Question.objects.get(pk=q_id)
					#Guardo la question
					response.question = q
								
					if q.question_type == Question.TEXT:
						response.answertype = 'TEXT'
						response.answervalue = field_value
					elif q.question_type == Question.RADIO:
						response.answertype = 'RADIO'
						response.answervalue = field_value
					elif q.question_type == Question.SELECT:
						response.answertype = 'SELECT'
						response.answervalue = field_value				
					elif q.question_type == Question.SELECT_MULTIPLE:
						response.answertype = 'MULTIPLE'
						response.answervalue = field_value					
					elif q.question_type == Question.INTEGER:	
						response.answertype = 'INTEGER'
						response.answervalue = field_value
								
					response.save()

		return response
		
class LoginForm(forms.Form):
	username = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput())