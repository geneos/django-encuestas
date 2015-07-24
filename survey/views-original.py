# -*- encoding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core import urlresolvers
from django.contrib import messages
import datetime
import settings
from django.contrib.auth import authenticate, login, logout

from models import Question, Survey, Category, Response#, AnswerBase
from forms import ResponseForm, LoginForm
import pdb

def Index(request):
	surveys_list = Survey.objects.order_by('name')		
	response_list = Response.objects.filter(interviewee=request.user.id).order_by('-category')[:1]		
	return render(request, 'index.html', {'surveys_list': surveys_list, 'response_list': response_list})


def error404(request):
	return render_to_response('404.html')

def SurveyDetail(request, response_id, id, p):
		
	survey = Survey.objects.get(id=id)	         	
	pagina_original = p
	
	#Lleno preguntas de la pagina de esa encuesta	
	category_items = Category.objects.filter(survey=survey, name=str(p))
	#Seteo booleans para workflow
	formnuevo = False
	formcorrecto = True

	if '_siguiente' in request.POST:	
		#Chequeo si la respuesta seleccionada implica un salto en los formularios (solo si es siguiente)
		salta_a_otra = False
		for key in request.POST:
			if key.startswith('question'):
				value = request.POST[key]
				if value != '':
					question_id = key[9:]
					questions = Question.objects.filter(survey=survey, id=int(question_id))
					if questions:						
						for question in questions:											
							if question.choices_salta_a_opcion == value:
								#esa respuesta tiene un "salta a"
								salta_a_otra = True
								pagina_nueva = question.choices_salta_a_numero
							else:
								if not salta_a_otra:
									pagina_nueva = question.choice_salta_por_default		


		#Si se presiono siguiente - me muevo a la pagina correspondiente
		form_sin_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=request.user, survey=survey)		
		form_sin_grabar.survey = survey
		form_sin_grabar.interviewee = request.user
		for categoria in category_items:
			form_sin_grabar.category = categoria							
		if form_sin_grabar.is_valid():						
			for field_name, field_value in form_sin_grabar.cleaned_data.iteritems():
				if field_name.startswith("question_"):
					#Creo un form nuevo y lo grabo por cada campo
					form_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=request.user, survey=survey)									
					form_grabar.survey = form_sin_grabar.survey
					form_grabar.interviewee = form_sin_grabar.interviewee
					form_grabar.category = form_sin_grabar.category
					#Grabo nuevo o update

					if response_id == '0': 					
						form_grabar.save(request.user, field_name, field_value, response_id)
					else:
						#Tengo que ver si ya existe o no						
						questions_actual = Question.objects.filter(id=field_name[9:])
						for question_actual in questions_actual:
							responses_actual = Response.objects.filter(survey=form_sin_grabar.survey, interviewee=form_sin_grabar.interviewee, category=form_sin_grabar.category, question=question_actual)
						
						if responses_actual:
							response_to_save = 0
							for response_actual in responses_actual:
								response_to_save = response_actual.id
							form_grabar.save(request.user, field_name, field_value, response_to_save)
						else:
							form_grabar.save(request.user, field_name, field_value, '0')						

		else:
			formcorrecto = False

		if formcorrecto:							
			p = pagina_nueva				
			category_items = Category.objects.filter(survey=survey, name=str(p))

			#Chequear response_id, para ver si ya esta llena la pagina siguiente o no
			if response_id == '0':
				form_nuevo = ResponseForm(category=p, id=response_id, interviewee=request.user, survey=survey)
			else:				
				responses_siguiente = Response.objects.filter(interviewee=request.user,survey=survey,category=p).order_by('id')[:1]
				if responses_siguiente:
					for response_siguiente in responses_siguiente:
						form_nuevo = ResponseForm(category=p, id=response_siguiente.id, interviewee=request.user, survey=survey)		
				else:					
					form_nuevo = ResponseForm(category=p, id=response_id, interviewee=request.user, survey=survey)		
			
			formnuevo = True

	elif '_anterior' in request.POST:
		#Si se presiono anterior - me muevo a la pagina correspondiente
		form_sin_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=request.user, survey=survey)			
		form_sin_grabar.survey = survey
		form_sin_grabar.interviewee = request.user
		for categoria in category_items:
			form_sin_grabar.category = categoria			
		if form_sin_grabar.is_valid():							
			for field_name, field_value in form_sin_grabar.cleaned_data.iteritems():
				if field_name.startswith("question_"):
					#Creo un form nuevo y lo grabo por cada campo
					form_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=request.user, survey=survey)					
					form_grabar.survey = form_sin_grabar.survey
					form_grabar.interviewee = form_sin_grabar.interviewee
					form_grabar.category = form_sin_grabar.category 					
					if response_id == '0': 					
						form_grabar.save(request.user, field_name, field_value, response_id)
					else:
						questions_actual = Question.objects.filter(id=field_name[9:])
						for question_actual in questions_actual:
							responses_actual = Response.objects.filter(survey=form_sin_grabar.survey, interviewee=form_sin_grabar.interviewee, category=form_sin_grabar.category, question=question_actual)
						if responses_actual:
							response_to_save = 0
							for response_actual in responses_actual:
								response_to_save = response_actual.id

							form_grabar.save(request.user, field_name, field_value, response_to_save)
		else:
			formcorrecto = False			
		
		form_nuevo = None
		if formcorrecto:						
			#Loop en responses, para encontrar el primer response de la pagina anterior						
		
			responses = Response.objects.filter(interviewee=request.user,survey=survey).order_by('-category')
			for response_anterior in responses: 
				if (response_anterior.category.name != str(p)) and (int(response_anterior.category.name) < int(p)):
					p_nuevo = response_anterior.category.name
					break

			p = int(p_nuevo)
			category_items = Category.objects.filter(survey=survey, name=str(p_nuevo))
			response_anterior = Response.objects.filter(interviewee=request.user,survey=survey,category=p_nuevo)[:1]
			if response_anterior:
				form_nuevo = ResponseForm(category=response_anterior[0].category, id=response_anterior[0].id, interviewee=request.user, survey=survey)

			formnuevo = True

	elif '_finalizar' in request.POST:
		#Si se presiono finalizar - redirecciono a la pagina de saludo
		form_sin_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=request.user, survey=survey)		
		form_sin_grabar.survey = survey
		form_sin_grabar.interviewee = request.user
		for categoria in category_items:
			form_sin_grabar.category = categoria			
		if form_sin_grabar.is_valid():							
			for field_name, field_value in form_sin_grabar.cleaned_data.iteritems():
				if field_name.startswith("question_"):					
					#Creo un form nuevo y lo grabo por cada campo
					form_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=request.user, survey=survey)	
					form_grabar.survey = form_sin_grabar.survey
					form_grabar.interviewee = form_sin_grabar.interviewee
					form_grabar.category = form_sin_grabar.category 					
					if response_id == '0': 					
						form_grabar.save(request.user, field_name, field_value, response_id)
					else:
						questions_actual = Question.objects.filter(id=field_name[9:])
						for question_actual in questions_actual:
							responses_actual = Response.objects.filter(survey=form_sin_grabar.survey, interviewee=form_sin_grabar.interviewee, category=form_sin_grabar.category, question=question_actual)
						if responses_actual:
							response_to_save = 0
							for response_actual in responses_actual:
								response_to_save = response_actual.id

							form_grabar.save(request.user, field_name, field_value, response_to_save)
						else:
							form_grabar.save(request.user, field_name, field_value, '0')	

			return HttpResponseRedirect("/confirm/%s" % request.user.username)
		else:
			formcorrecto = False			

	#Chequeo el form	
	if not request.method == 'POST':
		#Si es para edicion, tengo que pasarle un parametro de response
		form = ResponseForm(category=pagina_original, id=response_id, interviewee=request.user, survey=survey)

	#Reviso si es la ultima categoria para no mostrar Siguiente (mostrar "Finalizar")
	ultima = False
	ultimas_categorias = Category.objects.filter(survey=survey).order_by('-name')[:1]
	for ultima_categoria in ultimas_categorias:
		if int(ultima_categoria.name) == int(p):
			ultima = True
	
	#Calcular porcentaje de llenado
	surveys_paginas_totales = survey.categories().order_by('-name')[:1]
	for survey_paginas_totales in surveys_paginas_totales:
		porcentaje = (int(p)-1)*100/int(survey_paginas_totales.name)

	if formcorrecto:
		if formnuevo:
			return render(request, 'survey.html', {'response_form': form_nuevo, 'survey': survey, 'category_items': category_items, 'ultima': ultima, 'estudiante': request.user.id, 'response_id': response_id, 'porcentaje': porcentaje})
		else:
			return render(request, 'survey.html', {'response_form': form, 'survey': survey, 'category_items': category_items, 'ultima': ultima, 'estudiante': request.user.id, 'response_id': response_id,'porcentaje': porcentaje})	
	else:
		#form con errores
		return render(request, 'survey.html', {'response_form': form_sin_grabar, 'survey': survey, 'category_items': category_items, 'ultima': ultima, 'estudiante': request.user.id, 'form_errors': form_sin_grabar.errors, 'response_id': response_id, 'porcentaje': porcentaje})
		

def Confirm(request, uuid):
	email = settings.support_email
	return render(request, 'confirm.html', {'uuid':uuid, "email": email})

def login_page(request):
	
	response_list = None
	surveys_list = None
	message = None
	if request.method == 'POST':		
		form = LoginForm(request.POST)
		if form.is_valid():
			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(username=username,password=password)
			if user is not None:
				if user.is_active:
					login(request, user)
					surveys_list = Survey.objects.order_by('name')	
					response_list = Response.objects.filter(interviewee=request.user.id).order_by('-category')[:1]	
					return render_to_response('index.html', {'surveys_list': surveys_list, 'response_list': response_list}, context_instance=RequestContext(request))
				else:
					message = "Tu usuario está inactivo"
					return render_to_response('login.html', {'message': message, 'form':form, 'surveys_list': surveys_list, 'response_list': response_list}, 
								context_instance=RequestContext(request))
			else:
				message = "Nombre de usuario y/o password incorrecto"			
				return render_to_response('login.html', {'message': message, 'form':form, 'surveys_list': surveys_list, 'response_list': response_list}, 
								context_instance=RequestContext(request))
		else: 
			return render_to_response('login.html', {'message': message, 'form':form, 'surveys_list': surveys_list, 'response_list': response_list}, 
								context_instance=RequestContext(request))
		
	else:
		form = LoginForm()
		surveys_list = Survey.objects.order_by('name')	
		response_list = Response.objects.filter(interviewee=request.user.id).order_by('-category')[:1]	
		
		return render_to_response('login.html', {'message': message, 'form':form, 'surveys_list': surveys_list, 'response_list': response_list}, 
								context_instance=RequestContext(request))
	
	
def logout_view(request):
	logout(request)


