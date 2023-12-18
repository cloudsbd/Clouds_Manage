# Import necessary modules from Django
from django.shortcuts import render, redirect
from django.http import HttpResponse
from linode_api4 import (LinodeClient, LinodeLoginClient, StackScript, Image, Region,
                         Type, OAuthScopes)

from . import config
# Define our Django app
def index(request):
    """
    This view renders the main page, where users land when visiting the example
    site normally. This will present a simple form to deploy a Linode and allow
    them to submit the form.
    """
    client = LinodeClient('no-token')
    types = client.linode.types(Type.label.contains("Linode"))
    regions = client.regions()
    stackscript = StackScript(client, config.stackscript_id)
    return render(request, 'configure.html',  
        {'types': types,
         'regions': regions,
         'application_name': config.application_name,
         'stackscript': stackscript}
    )

def start_auth(request):
    """
    This view is called when the form rendered by GET / is submitted. This
    will store the selections in the Django session before redirecting to
    login.linode.com to log into configured OAuth Client.
    """
    login_client = get_login_client()
    request.session['dc'] = request.POST['region']
    request.session['distro'] = request.POST['distribution']
    request.session['type'] = request.POST['type']
    return redirect(login_client.generate_login_url(scopes=OAuthScopes.Linodes.read_write))

def auth_callback(request):
    """
    This view is where users who log in to our OAuth Client will be redirected
    from login.linode.com; it is responsible for completing the OAuth Workflow
    using the Exchange Code provided by the login server, and then proceeding with
    application logic.
    """
    # complete the OAuth flow by exchanging the Exchange Code we were given
    # with login.linode.com to get a working OAuth Token that we can use to
    # make requests on the user's behalf.
    code = request.GET.get('code')
    login_client = get_login_client()
    token, scopes, _, _ = login_client.finish_oauth(code)

    # ensure we were granted sufficient scopes - this is a best practice, but
    # at present users cannot elect to give us lower scopes than what we requested.
    # In the future they may be allowed to grant partial access.
    if not OAuthScopes.Linodes.read_write in scopes:
        return render(request, 'error.html', {'error': 'Insufficient scopes granted to deploy {}'.format(config.application_name)})

    # application logic - create the linode
    (linode, password) = make_instance(token, request.session['type'], request.session['dc'], request.session['distro'])

    # expire the OAuth Token we were given, effectively logging the user out of
    # of our application. While this isn't strictly required, it's a good
    # practice when the user is done (normally when clicking "log out")
    get_login_client().expire_token(token)
    return render(request, 'success.html',
        {'password': password,
         'linode': linode,
         'application_name': config.application_name}
    )

def make_instance(token, type_id, region_id, distribution_id):
    """
    A helper function to create a Linode with the selected fields.
    """
    client = LinodeClient('{}'.format(token))
    stackscript = StackScript(client, config.stackscript_id)
    (linode, password) = client.linode.instance_create(type_id, region_id,
            group=config.application_name,
            image=distribution_id, stackscript=stackscript.id)
    
    if not linode:
        raise RuntimeError("it didn't work")
    return linode, password


def create_stackscript(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        client = LinodeClient(token)
        public_images = client.images(Image.is_public == True)
        s = client.linode.stackscript_create('Demonstration_Public', '#!/bin/bash', public_images, is_public=True)
        return render(request, 'stackscript_created.html', {'stackscript_id': s.id})
    else:
        return render(request, 'token_input.html')
