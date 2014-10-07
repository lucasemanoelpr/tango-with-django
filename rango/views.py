
#coding: utf-8

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

def index(request):
    # Solicite o contexto da solicitação.
    # O contexto contém informações como detalhes da máquina do cliente, por exemplo.
    context = RequestContext(request)

    category_list = Category.objects.order_by('-likes')[:5]
    context_dict = {'categories': category_list}

    for category in category_list:
        category.url = category.name.replace(' ', '_')


    return render_to_response('rango/index.html', context_dict, context)

    # Construir um dicionário para passar para o modelo de motor como o seu contexto.
    # Observe a boldmessage chave é o mesmo que {{}} boldmessage no modelo!
    # Retorna uma resposta prestados para enviar para o cliente.
    # Nós fazemos uso da função de atalho para facilitar nossas vidas.
    # Note que o primeiro parâmetro é o modelo que deseja usar.



def about(request):
    return HttpResponse("Rango Says: Here is the about page.  <br> <a href='/rango/'>Index</a>")

#def static(request):

def category(request, category_name_url):

    # Solicite o contexto do pedido transmitido nos
    context = RequestContext(request)

    # Mudança destaca no nome da categoria para espaços.
    # URLs não lidar com espaços bem, então codificá-los como sublinhados.
    # Podemos, então, basta substituir os sublinhados com espaços novamente para obter o nome.
    category_name = category_name_url.replace('_', ' ')

    # Criar um dicionário de contexto que podemos passar para o motor de renderização do modelo.
    # Começamos contendo o nome da categoria passou pelo usuário.

    context_dict = {'category_name': category_name}
    try:
        # Podemos encontrar uma categoria com o nome dado
        # Se não podemos, o método .get () gera uma exceção DoesNotExist
        # Assim, o método .get () retorna uma instância do modelo ou levanta uma exceção
        category = Category.objects.get(name=category_name)

        # Recuperar todas as páginas associadas.
        # Note que instância de filtro returns> = 1 modelo.
        pages = Page.objects.filter(category=category)

        # Adiciona a nossa lista de resultados para o contexto do modelo sob páginas nome.
        context_dict['pages'] = pages

        # Nós também adicionar o objeto categoria do banco de dados para o dicionário de contexto.
        # Usaremos este no modelo para verificar que a categoria existe.
        context_dict['category'] = category

    except Category.DoesNotExist:
        # chegamos aqui se não encontrar a categoria especificada.
        # Não fazer nada - o modelo exibe a mensagem "nenhuma categoria" para nós.
        pass

    # Vai tornar a resposta e enviá-lo para o cliente.
    return render_to_response('rango/category.html', context_dict, context)




def add_category(request):
    # Get the context from the request.
    context = RequestContext(request)

    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', {'form': form}, context)


def register(request):
    # Like before, get the request's context.
    context = RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render_to_response(
            'rango/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
            context)


def user_login(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)

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
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('rango/login.html', {}, context)


def some_view(request):
    if not request.user.is_authenticated():
        return HttpResponse("You are logged in.")
    else:
        return HttpResponse("You are not logged in.")


@login_required

def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")

# Use the login_required() decorator to ensure only those logged in can access the view.

@login_required

def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')