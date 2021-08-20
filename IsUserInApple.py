# Tested on Python 3.9.2, python-3.9.2-amd64.exe
# pip install requests authlib
#
# Reads in settings from IsUserInApple.config
# [settings]
# private_key = path-to-your-p8-file
# KEY_ID = your-key-id
# ISSUER_ID = your-issuer-id
#
import requests, time, json, sys, tempfile, os, configparser, datetime
from authlib.jose import jwt

def getToken(KEY_ID, ISSUER_ID, PATH_TO_KEY):
    EXPIRATION_TIME = int(round(time.time() + (10.0 * 60.0))) # 10 minutes timestamp

    with open(PATH_TO_KEY, 'rb') as f:
        PRIVATE_KEY = f.read()

    header = {
        "alg": "ES256",
        "kid": KEY_ID
    }


    payload = {
        "iss": ISSUER_ID,
        "exp": EXPIRATION_TIME,
        "aud": "appstoreconnect-v1"
    }

    # Create and return the JWT
    return jwt.encode(header, payload, PRIVATE_KEY)

def getAllUsers(token):
    JWT = 'Bearer ' + token.decode()
    URL = 'https://api.appstoreconnect.apple.com/v1/users?limit=100'
    HEAD = {'Authorization': JWT}

    teamMembers = []

    nextURL = URL
    keepGoing = True

    while keepGoing:
        r = requests.get(nextURL, params={}, headers=HEAD)

        y = r.json()

        if 'errors' in y:
            errorCode = y['errors'][0]
            print('Apple returned an HTTP ' + errorCode['status'] + ' code')
            print(errorCode['detail'])
            sys.exit('whoops')

        for i in y['data']:
            teamMembers.append({'username':i['attributes']['username'].lower(), 'roles': ','.join(i['attributes']['roles'])})

        if 'next' in y['links']:
            nextURL = y['links']['next']
        else:
             keepGoing = False

    return teamMembers


if len(sys.argv) > 1:
    config = configparser.ConfigParser()
    try:
        configPath = os.path.dirname(os.path.abspath(__file__)) + "/IsUserInApple.config"
        config.read(configPath)
    except Exception as e :
        print(str(e))

    try:
        private_key = config['settings']['private_key']    
        KEY_ID = config['settings']['KEY_ID']    
        ISSUER_ID = config['settings']['ISSUER_ID']    
    except Exception as e :
        print(str(e))
        
    if not os.path.isfile(private_key):
        sys.exit("Error missing private key file for JWT")

    UserEmail = sys.argv[1].lower()

    print('Looking for a match on ' + UserEmail)

    token = getToken(KEY_ID, ISSUER_ID, private_key)

    members = getAllUsers(token)

    HasMatch = False

    for i in members:
        if i['username'] == UserEmail:
            HasMatch = True
            print('Match on ' + i['username'] + ', Roles: ' + i['roles'])

    if HasMatch == False:
        print('No match')

else:
    sys.exit("Error: Please specify an email address")