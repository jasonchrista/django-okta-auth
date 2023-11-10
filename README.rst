Django Okta Auth
=================

*Django Okta Auth* allows you to authenticate through Okta.

Installation
------------

Run ``pip install django-okta-authentication``

Add the ``OktaBackend`` to your ``AUTHENTICATION_BACKENDS`` setting:

.. code:: python

   AUTHENTICATION_BACKENDS = (
       ...
       'okta_auth.backends.OktaBackend',
   )

Edit your ``urls.py`` to include:

.. code:: python

   urlpatterns = [
       url(r'^okta/', include('okta_auth.urls')),
       ...
   ]

Settings
--------

###OKTA_DOMAIN

Okta domain.

###OKTA_CLIENT_ID

Okta client id.

###OKTA_CLIENT_SECRET

Okta client secret.

###OKTA_SCOPE

**default:** ``'openid email'`` OAuth scope parameter.

###OKTA_RESPONSE_TYPE

**default:** ``'id_token'`` OAuth response type parameter.

###OKTA_USER_CREATION

**default:** ``True`` Allow creation of new users after successful
authentication.

Logging
-------

To enable logging add ``okta_auth`` to ``LOGGING['loggers']`` options.

.. code:: python

   LOGGING = {
       ...,
       'loggers': {
           ...,
           'okta_auth': {
               'handlers': ['console'],
               'level': 'DEBUG',
           }
       }
   }
