
#coding: utf-8

from django.http import HttpResponse

from django.template import RequestContext
from django.shortcuts import render_to_response,redirect
from rango.models import Category
from rango.models import Page
from rango.models import UserProfile
from rango.forms import CategoryForm, PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User

from datetime import datetime

def decode_url(category_name_url):
    return category_name_url.replace('_', ' ')

def encode_url(category):
    return category.name.replace(' ', '_')

def get_category_list():
    cat_list = Category.objects.all()

    for cat in cat_list:
        cat.url = encode_url(cat)

    return cat_list


def index(request):
    #context = {}
    context = RequestContext(request)
    context_dict = {}

    cat_list = get_category_list()
    context['cat_list'] = cat_list

    category_list = Category.objects.order_by('-likes')[:5]
    context['categories'] = category_list
    for category in category_list:
        category.url = encode_url(category)

    page_list = Page.objects.order_by('-views')[:5]
    context['pages'] = page_list

    if request.session.get('last_visit'):
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).seconds > 5:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1

    #print(request.session['visits'], request.session['last_visit'])
    return render_to_response('rango/index.html', context_dict, context)
    #return render(request, 'rango/index.html', context)



def about(request):
    #context = {}
    context = RequestContext(request)
    context_dict = {}

    cat_list = get_category_list()
    context['cat_list'] = cat_list

    context['mensagem_negrito'] = "Está página explica quem é o Rango."

    if request.session.get('visits'):
        visits = request.session.get('visits')
        last_visit = request.session.get('last_visit')
    else:
        visits = 0

    context['visits'] = visits
    context['last_visit'] = last_visit

    return render_to_response('rango/about.html', context_dict, context)
    #return render(request, 'rango/about.html', context)



#def static(request):

def category(request, category_name_url):

    # Solicite o contexto do pedido transmitido nos
    #context ={}
    context = RequestContext(request)
    context_dict = {}

    cat_list = get_category_list()
    context['cat_list'] = cat_list
    # Mudança destaca no nome da categoria para espaços.
    # URLs não lidar com espaços bem, então codificá-los como sublinhados.
    # Podemos, então, basta substituir os sublinhados com espaços novamente para obter o nome.
    category_name = decode_url(category_name_url)

    # Criar um dicionário de contexto que podemos passar para o motor de renderização do modelo.
    # Começamos contendo o nome da categoria passou pelo usuário.

    context['category_name'] = category_name
    context['category_name_url'] = category_name_url

    try:
        category = Category.objects.get(name=category_name)
        context['category'] = category
        page_list = Page.objects.filter(category=category)
        context['pages'] = page_list

    except Category.DoesNotExist:
        pass

    return render_to_response('rango/category.html', context_dict, context)
    #return render(request, 'rango/category.html', context)


@login_required

def add_category(request):
    # Get the context from the request.
    #context = {}
    context = RequestContext(request)
    context_dict = {}

    cat_list = get_category_list()
    context['cat_list'] = cat_list

    # A HTTP POST?
    if request.method != 'POST':
        form = CategoryForm()
    else:
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors

    context['form'] = form
    return render_to_response('rango/add_category.html', context_dict, context)

    #return render(request, 'rango/add_category.html', context)

@login_required

def add_page(request, category_name_url):
    #context = {}
    context = RequestContext(request)
    context_dict = {}

    cat_list = get_category_list()
    context['cat_list'] = cat_list

    context['category_name_url'] = category_name_url

    category_name = decode_url(category_name_url)
    context['category_name'] = category_name

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render(request, 'rango/add_page.html', context)
            page.views = 0
            page.save()
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()

    context['form'] = form

    return render_to_response('rango/add_page.html', context_dict, context)
    #return render(request, 'rango/add_page.html', context)



def register(request):
    # Like before, get the request's context.
    #context = {}
    context = RequestContext(request)
    context_dict = {}

    cat_list = get_category_list()
    context['cat_list'] = cat_list

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            # print('Senha antes: %s' %user.password)
            user.set_password(user.password)
            user.save()
            # print('Senha depois: %s' %user.password)

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()

            registered = True
        else:
            print user_form.errors, profile_form.errors
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    context['user_form'] = user_form
    context['profile_form'] = profile_form
    context['registered'] = registered

    return render_to_response('rango/register.html', context_dict, context)

    #return render(request,'rango/register.html', context)



def user_login(request):
    # Like before, obtain the context for the user's request.
    #context = {}
    context = RequestContext(request)
    context_dict = {}


    cat_list = get_category_list()
    context['cat_list'] = cat_list

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse(" Sua conta no rango está desabilitada.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print " Detalhes de login inválidos: {0}, {1}".format(username, password)
            return HttpResponse("Detalhes Inválidos de login.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        #return render(request, 'rango/login.html',context)
        return render_to_response('rango/login.html', context_dict, context)

@login_required

def restricted(request):
    #context = {}
    context = RequestContext(request)
    context_dict = {}

    cat_list = get_category_list()
    context['cat_list'] = cat_list
    context['texto'] = "Você pode ler esse texto, pois está logado!"

    return render_to_response('rango/restricted.html', context_dict, context)

    #return render(request, 'rango/restricted.html', context)


# Use the login_required() decorator to ensure only those logged in can access the view.

@login_required

def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')


def profile(request):

    context = RequestContext(request)
    context_dict = {}
    cat_list = get_category_list()
    context_dict['cat_list']= cat_list

    u = User.objects.get(username=request.user)

    try:
        up = UserProfile.objects.get(user=u)
    except:
        up = None

    context['user'] = u
    context['userprofile'] = up
    #return render(request, 'rango/profile.html', context)
    return render_to_response('rango/profile.html', context_dict, context)


def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)