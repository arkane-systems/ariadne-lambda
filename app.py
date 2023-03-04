# -*- coding: utf-8 -*-

"""
AWS Lambda function for handling Alexa skill requests.

Copyright (c) 2022 AListair J. R. Young
"""

import json
import logging
import os
import sys
import urllib3

debug = bool(os.environ.get('DEBUG'))
base_url = os.environ.get('BASE_URL')
verify_ssl = not bool(os.environ.get('DO_NOT_VERIFY_SSL'))

logger = logging.getLogger('Ariadne-Lambda')
logger.setLevel (logging.DEBUG if debug else logging.INFO)

def smart_home_handler (event, context):
  """Handle requests intended for the Smart Home skill."""

  directive = event.get ('directive')
  assert directive is not None, 'Malformed request (missing directive).'
  assert directive.get('header', {}).get('payloadVersion') == '3', 'Unsupported request (only support payloadVersion == 3).'

  scope = directive.get('endpoint', {}).get('scope')
  if scope is None:
    # token is in grantee for Linking directive
    scope = directive.get('payload', {}).get('grantee')
  if scope is None:
    # token is in payload for Discovery directive
    scope = directive.get('payload', {}).get('scope')
  assert scope is not None, 'Malformed request (missing endpoint.scope).'
  assert scope.get('type') == 'BearerToken', 'Unsupported request (only support BearerToken).'

  token = scope.get('token')
  if token is None and debug:
    token = os.environ.get('LONG_LIVED_ACCESS_TOKEN')  # only for debug purposes

  assert token, 'Configuration error (could not get access token.)'

  http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED' if verify_ssl else 'CERT_NONE',
    timeout=urllib3.Timeout(connect=2.0, read=10.0)
  )

  response = http.request(
    'POST',
    '{}/api/alexa/smart_home'.format(base_url),
    headers={
      'Authorization': 'Bearer {}'.format(token),
      'Content-Type': 'application/json',
    },
    body=json.dumps(event).encode('utf-8'),
  )

  if response.status >= 400:
    return {
      'event': {
        'payload': {
          'type': 'INVALID_AUTHORIZATION_CREDENTIAL'
                  if response.status in (401, 403) else 'INTERNAL_ERROR',
          'message': response.data.decode("utf-8"),
        }
      }
    }

  return json.loads(response.data.decode("utf-8"))


def custom_handler (event, context):
  """Handle requests intended for the Custom skill."""

  try:
    token = event.get('session', {}).get('user', {}).get('accessToken')
  except AttributeError:
    token = None

  if token is None and _debug:
    token = os.environ.get('LONG_LIVED_ACCESS_TOKEN')

  assert token, 'Configuration error (could not get access token.)'

  if token is None and debug:
    token = os.environ.get('LONG_LIVED_ACCESS_TOKEN')  # only for debug purposes

  assert token, 'Configuration error (could not get access token.)'

  http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED' if verify_ssl else 'CERT_NONE',
    timeout=urllib3.Timeout(connect=2.0, read=10.0)
  )

  response = http.request(
    'POST',
    '{}/api/alexa'.format(base_url),
    headers={
      'Authorization': 'Bearer {}'.format(token),
      'Content-Type': 'application/json',
    },
    body=json.dumps(event).encode('utf-8'),
  )

  if response.status >= 400:
    return {
      'event': {
        'payload': {
          'type': 'INVALID_AUTHORIZATION_CREDENTIAL'
                  if response.status in (401, 403) else 'INTERNAL_ERROR',
          'message': response.data.decode("utf-8"),
        }
      }
    }

  return json.loads(response.data.decode("utf-8"))


def test_handler (event, context):
  """Handle requests intended for the test function."""
  return "Hello from Ariadne Lambda function, using Python " + sys.version + "!"


def handler (event, context):
  """Handle incoming requests."""

  # Assert that we have the necessary information.
  assert base_url is not None, 'Please set BASE_URL environment variable.'

  logger.debug ('Context: %s', context)
  logger.debug ('Event: %s', event)

  if context.function_name == 'ariadneSmartHome':
    # Execute Smart Home Skill function.
    return smart_home_handler(event, context)

  elif context.function_name == 'ariadneCustom':
    # Execute Custom Skill function.
    return custom_handler(event, context)

  elif context.function_name == 'ariadneTest':
    # Execute test function.
    return test_handler(event, context)

  else:
    # Bugger.
    return {
      'statusCode': 418,
      'body': "Sorry, Dave, I'm afraid I can't do that."
    }
