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
from django.contrib.auth.models import User

from models import Pregunta, Encuesta, Pagina, Response

from forms import ResponseForm, LoginForm

def Index(request):

	if '_encuesta' in request.POST:	
		#Redirecciono a Survey con el egresado elegido
		
		egresado_id = None
		survey_id = None
		for key in request.POST:
			if key.startswith('egresado_id'):
				egresado_id = request.POST[key]
			elif key.startswith('survey_id'):
				survey_id = request.POST[key]
		
		egresado = User.objects.filter(id=egresado_id)		
		survey = Encuesta.objects.get(id=survey_id)	         	

		#Chequeo si ya respondieron encuesta para ese egresado
		response = Response.objects.filter(survey=survey, interviewee=egresado)
		if response:
			mensaje = "Ya se cargó esa encuesta para ese egresado."
			#Operador
			#Cargo un combo de egresados, lo elige y ahi puede cargar formulario nuevo.			
			surveys_list = Encuesta.objects.order_by('name')	
			egresados_list = User.objects.filter(groups__name__in=['egresados'], is_active=True).order_by('last_name')
			return render(request, 'index.html', {'surveys_list': surveys_list, 'response_list': None, 'egresados_list': egresados_list,'mensaje':mensaje})
			

		#pagina
		p = 1
		#Lleno preguntas de la pagina de esa encuesta	
		category_items = Pagina.objects.filter(survey=survey, name=str(p))		
		form = ResponseForm(category=p, id=None, interviewee=egresado_id, survey=survey)
		
		return render(request, 'survey.html', {'response_form': form, 'survey': survey, 'category_items': category_items, 'ultima': False, 'egresado_id': egresado_id, 'response_id': 0,'porcentaje': 0, 'operador': 1})	

	else:
		if not is_member(request.user):
			#Egresado
			surveys_list = Encuesta.objects.order_by('name')		
			response_list = Response.objects.filter(interviewee=request.user.id).order_by('-category')[:1]		
			return render(request, 'index.html', {'surveys_list': surveys_list, 'response_list': response_list, 'egresados_list': None})
		else:
			#Operador
			#Cargo un combo de egresados, lo elige y ahi puede cargar formulario nuevo.
			surveys_list = Encuesta.objects.order_by('name')	
			egresados_list = User.objects.filter(groups__name__in=['egresados'], is_active=True).order_by('last_name')
			return render(request, 'index.html', {'surveys_list': surveys_list, 'response_list': None, 'egresados_list': egresados_list})
			
		

def is_member(user):
    return user.groups.filter(name='operadores').exists()

def error404(request):
	return render_to_response('404.html')

def SurveyDetail(request, response_id, id, p, operador, egresado_id):
		
	survey = Encuesta.objects.get(id=id)	         	
	pagina_original = p
	
	#Lleno preguntas de la pagina de esa encuesta	
	category_items = Pagina.objects.filter(survey=survey, name=str(p))
	#Seteo booleans para workflow
	formnuevo = False
	formcorrecto = True

	if operador == '1':
		usuario = User.objects.get(id=egresado_id)		
	else:
		usuario = request.user

	if '_siguiente' in request.POST:	
		#Chequeo si la respuesta seleccionada implica un salto en los formularios (solo si es siguiente)
		salta_a_otra = False
		for key in request.POST:
			if key.startswith('question'):
				value = request.POST[key]
				if value != '':
					question_id = key[9:]
					questions = Pregunta.objects.filter(survey=survey, id=int(question_id))
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
		form_sin_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=egresado_id, survey=survey)							
		form_sin_grabar.interviewee = usuario
		form_sin_grabar.survey = survey
		
		for categoria in category_items:
			form_sin_grabar.category = categoria							
		if form_sin_grabar.is_valid():						
			for field_name, field_value in form_sin_grabar.cleaned_data.iteritems():
				if field_name.startswith("question_"):
					#Creo un form nuevo y lo grabo por cada campo
					form_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=usuario, survey=survey)									
					form_grabar.survey = form_sin_grabar.survey
					form_grabar.interviewee = form_sin_grabar.interviewee
					form_grabar.category = form_sin_grabar.category
					#Grabo nuevo o update

					if response_id == '0': 											
						form_grabar.save(usuario, field_name, field_value, response_id)											
					else:
						#Tengo que ver si ya existe o no						
						questions_actual = Pregunta.objects.filter(id=field_name[9:])
						for question_actual in questions_actual:
							responses_actual = Response.objects.filter(survey=form_sin_grabar.survey, interviewee=form_sin_grabar.interviewee, category=form_sin_grabar.category, question=question_actual)
						
						if responses_actual:
							response_to_save = 0
							for response_actual in responses_actual:
								response_to_save = response_actual.id							
							form_grabar.save(usuario, field_name, field_value, response_to_save)														
						else:
							form_grabar.save(usuario, field_name, field_value, '0')													
		else:
			formcorrecto = False

		if formcorrecto:							
			p = pagina_nueva				
			category_items = Pagina.objects.filter(survey=survey, name=str(p))

			#Chequear response_id, para ver si ya esta llena la pagina siguiente o no
			if response_id == '0':				
				form_nuevo = ResponseForm(category=p, id=response_id, interviewee=usuario, survey=survey)								
			else:				
				responses_siguiente = Response.objects.filter(interviewee=usuario,survey=survey,category=p).order_by('id')[:1]								
				if responses_siguiente:
					for response_siguiente in responses_siguiente:						
						form_nuevo = ResponseForm(category=p, id=response_siguiente.id, interviewee=usuario, survey=survey)								
				else:							
					form_nuevo = ResponseForm(category=p, id=response_id, interviewee=usuario, survey=survey)							
			formnuevo = True

	elif '_anterior' in request.POST:
		#Si se presiono anterior - me muevo a la pagina correspondiente
		form_sin_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=usuario, survey=survey)			
		form_sin_grabar.survey = survey
		form_sin_grabar.interviewee = usuario
		for categoria in category_items:
			form_sin_grabar.category = categoria			
		if form_sin_grabar.is_valid():							
			for field_name, field_value in form_sin_grabar.cleaned_data.iteritems():
				if field_name.startswith("question_"):
					#Creo un form nuevo y lo grabo por cada campo
					form_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=usuario, survey=survey)					
					form_grabar.survey = form_sin_grabar.survey
					form_grabar.interviewee = form_sin_grabar.interviewee
					form_grabar.category = form_sin_grabar.category 					
					if response_id == '0': 					
						form_grabar.save(usuario, field_name, field_value, response_id)
					else:
						questions_actual = Pregunta.objects.filter(id=field_name[9:])
						for question_actual in questions_actual:
							responses_actual = Response.objects.filter(survey=form_sin_grabar.survey, interviewee=form_sin_grabar.interviewee, category=form_sin_grabar.category, question=question_actual)
						if responses_actual:
							response_to_save = 0
							for response_actual in responses_actual:
								response_to_save = response_actual.id

							form_grabar.save(usuario, field_name, field_value, response_to_save)
		else:
			formcorrecto = False			
		
		form_nuevo = None
		if formcorrecto:						
			#Loop en responses, para encontrar el primer response de la pagina anterior						
		
			responses = Response.objects.filter(interviewee=usuario,survey=survey).order_by('-category')
			for response_anterior in responses: 
				if (response_anterior.category.name != str(p)) and (int(response_anterior.category.name) < int(p)):
					p_nuevo = response_anterior.category.name
					break

			p = int(p_nuevo)
			category_items = Pagina.objects.filter(survey=survey, name=str(p_nuevo))
			response_anterior = Response.objects.filter(interviewee=usuario,survey=survey,category=p_nuevo)[:1]
			if response_anterior:
				form_nuevo = ResponseForm(category=response_anterior[0].category, id=response_anterior[0].id, interviewee=usuario, survey=survey)

			formnuevo = True

	elif '_finalizar' in request.POST:
		#Si se presiono finalizar - redirecciono a la pagina de saludo
		form_sin_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=usuario, survey=survey)		
		form_sin_grabar.survey = survey
		form_sin_grabar.interviewee = usuario
		for categoria in category_items:
			form_sin_grabar.category = categoria			
		if form_sin_grabar.is_valid():							
			for field_name, field_value in form_sin_grabar.cleaned_data.iteritems():
				if field_name.startswith("question_"):					
					#Creo un form nuevo y lo grabo por cada campo
					form_grabar = ResponseForm(request.POST, category=pagina_original, id=response_id, interviewee=usuario, survey=survey)	
					form_grabar.survey = form_sin_grabar.survey
					form_grabar.interviewee = form_sin_grabar.interviewee
					form_grabar.category = form_sin_grabar.category 					
					if response_id == '0': 					
						form_grabar.save(usuario, field_name, field_value, response_id)
					else:
						questions_actual = Pagina.objects.filter(id=field_name[9:])
						responses_actual = None
						for question_actual in questions_actual:
							responses_actual = Response.objects.filter(survey=form_sin_grabar.survey, interviewee=form_sin_grabar.interviewee, category=form_sin_grabar.category, question=question_actual)
						if responses_actual:
							response_to_save = 0
							for response_actual in responses_actual:
								response_to_save = response_actual.id

							form_grabar.save(usuario, field_name, field_value, response_to_save)
						else:
							form_grabar.save(usuario, field_name, field_value, '0')	

			return HttpResponseRedirect("/confirm/%s" % usuario.username)
		else:
			formcorrecto = False			

	#Chequeo el form	
	if not request.method == 'POST':
		#Si es para edicion, tengo que pasarle un parametro de response
		form = ResponseForm(category=pagina_original, id=response_id, interviewee=usuario, survey=survey)

	#Reviso si es la ultima categoria para no mostrar Siguiente (mostrar "Finalizar")
	ultima = False
	ultimas_categorias = Pagina.objects.filter(survey=survey).order_by('-name')[:1]
	for ultima_categoria in ultimas_categorias:
		if int(ultima_categoria.name) == int(p):
			ultima = True
	
	
	#Calcular porcentaje de llenado
	#surveys_paginas_totales = survey.categories().order_by('-name')[:1]
	import pdb
	pdb.set_trace()
	surveys_paginas_totales = survey.categories()[:1]
	for survey_paginas_totales in surveys_paginas_totales:		
		porcentaje = (int(p)-1)*100/int(survey_paginas_totales.name)

	if formcorrecto:
		if formnuevo:
			if operador == '1':
				return render(request, 'survey.html', {'response_form': form_nuevo, 'survey': survey, 'category_items': category_items, 'ultima': ultima, 'estudiante': usuario.id, 'response_id': response_id, 'porcentaje': porcentaje, 'operador': 1, 'egresado_id': egresado_id})
			else:
				return render(request, 'survey.html', {'response_form': form_nuevo, 'survey': survey, 'category_items': category_items, 'ultima': ultima, 'estudiante': usuario.id, 'response_id': response_id, 'porcentaje': porcentaje, 'operador': 0, 'egresado_id': 0})			
		else:
			if operador == '1':				
				return render(request, 'survey.html', {'response_form': form, 'survey': survey, 'category_items': category_items, 'ultima': ultima, 'estudiante': usuario.id, 'response_id': response_id,'porcentaje': porcentaje, 'operador': 1, 'egresado_id': egresado_id})	
			else:
				return render(request, 'survey.html', {'response_form': form, 'survey': survey, 'category_items': category_items, 'ultima': ultima, 'estudiante': usuario.id, 'response_id': response_id,'porcentaje': porcentaje, 'operador': 0, 'egresado_id': 0})	
	else:
		#form con errores
		if operador == '1':
			return render(request, 'survey.html', {'response_form': form_sin_grabar, 'survey': survey, 'category_items': category_items, 'ultima': ultima, 'estudiante': usuario.id, 'form_errors': form_sin_grabar.errors, 'response_id': response_id, 'porcentaje': porcentaje, 'operador': 1, 'egresado_id': egresado_id})
		else:
			return render(request, 'survey.html', {'response_form': form_sin_grabar, 'survey': survey, 'category_items': category_items, 'ultima': ultima, 'estudiante': usuario.id, 'form_errors': form_sin_grabar.errors, 'response_id': response_id, 'porcentaje': porcentaje, 'operador': 0, 'egresado_id': 0})

def Confirm(request, uuid):
	email = settings.support_email
	return render(request, 'confirm.html', {'uuid':uuid, "email": email})

def login_page(request):
	

	if '_encuesta' in request.POST:	
		#Redirecciono a Survey con el egresado elegido
		
		egresado_id = None
		survey_id = None
		for key in request.POST:
			if key.startswith('egresado_id'):
				egresado_id = request.POST[key]
			elif key.startswith('survey_id'):
				survey_id = request.POST[key]
		
		egresado = User.objects.filter(id=egresado_id)		
		survey = Encuesta.objects.get(id=survey_id)	         	

		#Chequeo si ya respondieron encuesta para ese egresado
		response = Response.objects.filter(survey=survey, interviewee=egresado)
		if response:
			mensaje = "Ya se cargó esa encuesta para ese egresado."
			#Operador
			#Cargo un combo de egresados, lo elige y ahi puede cargar formulario nuevo.			
			surveys_list = Encuesta.objects.order_by('name')	
			egresados_list = User.objects.filter(groups__name__in=['egresados'], is_active=True).order_by('last_name')
			return render(request, 'index.html', {'surveys_list': surveys_list, 'response_list': None, 'egresados_list': egresados_list,'mensaje':mensaje})
			

		#pagina
		p = 1
		#Lleno preguntas de la pagina de esa encuesta	
		category_items = Pagina.objects.filter(survey=survey, name=str(p))		
		form = ResponseForm(category=p, id=None, interviewee=egresado_id, survey=survey)

		return render(request, 'survey.html', {'response_form': form, 'survey': survey, 'category_items': category_items, 'ultima': False, 'egresado_id': egresado_id, 'response_id': 0,'porcentaje': 0, 'operador': 1})	
	else:		
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
						
						if not is_member(request.user):
							#Egresado
							surveys_list = Encuesta.objects.order_by('name')		
							response_list = Response.objects.filter(interviewee=request.user.id).order_by('-category')[:1]		
							return render(request, 'index.html', {'surveys_list': surveys_list, 'response_list': response_list, 'egresados_list': None})
						else:
							#Operador
							#Cargo un combo de egresados, lo elige y ahi puede cargar formulario nuevo.
							surveys_list = Encuesta.objects.order_by('name')	
							egresados_list = User.objects.filter(groups__name__in=['egresados'], is_active=True).order_by('last_name')
							return render(request, 'index.html', {'surveys_list': surveys_list, 'response_list': None, 'egresados_list': egresados_list})
																													
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
			surveys_list = Encuesta.objects.order_by('name')	
			response_list = Response.objects.filter(interviewee=request.user.id).order_by('-category')[:1]	
			
			return render_to_response('login.html', {'message': message, 'form':form, 'surveys_list': surveys_list, 'response_list': response_list}, 
									context_instance=RequestContext(request))
		
	
def logout_view(request):
	logout(request)


