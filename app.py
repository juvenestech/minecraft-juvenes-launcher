import eel, requests, json, uuid, minecraft_launcher_lib, subprocess, os

def setProgress(percentage, speed):
    eel.setProgressSpeed(speed)
    eel.setProgress(percentage)

maxProgress = 1
def setMaxProgress(mp):
    global maxProgress
    maxProgress = mp
currentProgress = 0
def setCurrentProgress(cp):
    global currentProgress
    currentProgress = cp
    setProgress(currentProgress/maxProgress*100, 200)

def encode(text: str)-> str:
    text = text[::-1]
    output = ""
    for c in text:
        output += chr(ord(c) + 5)
    return output

def decode(text: str) -> str:
    text = text[::-1]
    output = ""
    for c in text:
        output += chr(ord(c) - 5)
    return output

options = None
minecraft_version = None
minecraft_director = None

@eel.expose
def auth():
    try:
        eel.setCode('CARICAMENTO...')
        eel.setMessage('Attendi il caricamento del codice e comunicalo all\'animatore.')
        setProgress(0, 0)

        # 0 CONFIG:
        def config():
            url = 'https://raw.githubusercontent.com/juvenestech/minecraft-juvenes-launcher/main/config.json' 
            r = requests.get(url)

            if r.status_code != 200:
                eel.setCode(f'ERRORE 0.{r.status_code}')
                eel.setMessage('Non è stato possibile il file di configurazione.')
                setProgress(100, 500)
                exit(0)

            r_json = json.loads(r.text)
            ### print('\033[92m' + json.dumps(r_json, indent=4) + '\033[0m')
            return r_json
        config = config()
        client_id = decode(config['client_id_encoded'])

        # 1 MSFTCODE:
        def msftCode(client_id):
            url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode'
            payload = {
                'client_id': client_id,
                'scope': 'XboxLive.signin offline_access'
            }
            headers = {'Accept-Language': 'it'}
            r = requests.get(url, headers=headers, params=payload)

            if r.status_code != 200:
                eel.setCode(f'ERRORE 1.{r.status_code}')
                eel.setMessage('Non è stato possibile ottenere il tuo codice.')
                setProgress(100, 500)
                exit(1)

            r_json = json.loads(r.text)
            ### print('\033[94m' + json.dumps(r_json, indent=4) + '\033[0m')
            return r_json
        msftCode = msftCode(client_id)
        eel.setCode(msftCode['user_code'])
        eel.setMessage(msftCode['message'])
        setProgress(100, msftCode['expires_in']*1000)

        # 2 MSFTAUTH:
        def msftAuth(device_code, interval):
            url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
            while True:
                eel.sleep(interval)
                payload = {
                    'client_id':'d203c5ba-898e-4ec7-8eda-d38685ed36c4',
                    'grant_type':'urn:ietf:params:oauth:grant-type:device_code',
                    'device_code': device_code
                }
                r = requests.post(url, data=payload)

                r_json = json.loads(r.text)
                ### print('\033[96m' + json.dumps(r_json, indent=4) + '\033[0m')

                if 'error' not in r_json:
                    error = None
                    break

                error = r_json['error']
                if error == 'slow_down':
                    interval += 5
                elif error != 'authorization_pending':
                    break

            if error is not None: 
                eel.setCode(f'ERRORE 2.{r.status_code}')
                eel.setMessage('Non è stato possibile autenticare il tuo codice.')
                setProgress(100, 500)
                exit(2)
            return r_json
        msftAuth = msftAuth(msftCode['device_code'],msftCode['interval'])
        eel.setCode('✔ '+msftCode['user_code'])
        eel.setMessage('Il tuo codice è stato autenticato.<br/>Connessione con XBOX Live in corso...')
        setProgress(0, 0)
        setProgress(100, msftAuth['expires_in']*1000)

        # 3 XBOXAUTH:
        def xboxAuth(access_token):
            url = 'https://user.auth.xboxlive.com/user/authenticate'
            payload = {
                'Properties':{
                    'AuthMethod' : 'RPS',
                    'SiteName': 'user.auth.xboxlive.com',
                    'RpsTicket': f'd={access_token}',
                },
                'RelyingParty': 'http://auth.xboxlive.com',
                'TokenType': 'JWT'
            }
            headers = {'Accept': 'application/json','Content-Type': 'application/json'}
            r = requests.post(url, headers=headers, data=json.dumps(payload))

            if r.status_code != 200: 
                eel.setCode(f'ERRORE 3.{r.status_code}')
                eel.setMessage('Non è stato possibile autenticare il tuo codice.')
                setProgress(100, 500)
                eel.setProgressError(True)
                exit(3)

            r_json = json.loads(r.text)
            ### print('\033[92m' + json.dumps(r_json, indent=4) + '\033[0m')
            return r_json
        xboxAuth = xboxAuth(msftAuth['access_token'])
        eel.setMessage('Connessione con XBOX Live stabilita.<br/>Ottenimento informazioni sul GamerTag...')
        setProgress(0, 0)

        # 4 XBOXXSTS:
        def xboxXsets(Token):
            url = 'https://xsts.auth.xboxlive.com/xsts/authorize'
            payload = {
                'Properties':{
                    'SandboxId': 'RETAIL',
                    'UserTokens': [
                        f'{Token}'
                    ]
                },
                'RelyingParty': 'rp://api.minecraftservices.com/',
                'TokenType': 'JWT'
            }
            headers = {'Accept': 'application/json','Content-Type': 'application/json'}
            r = requests.post(url, headers=headers, data=json.dumps(payload))

            if r.status_code != 200: 
                eel.setCode(f'ERRORE 4.{r.status_code}')
                eel.setMessage('Non è stato possibile ottenere informazioni sul GamerTag.')
                setProgress(100, 500)
                eel.setProgressError(True)
                exit(4)

            r_json = json.loads(r.text)
            ### print('\033[94m' + json.dumps(r_json, indent=4) + '\033[0m')
            return r_json
        xboxXsets = xboxXsets(xboxAuth['Token'])
        eel.setMessage('Ottenute informazioni sul GamerTag.<br/>Ricerca dell\'hash del GamerTag...')
        setProgress(0, 0)

        # 5 XBOXUHS:
        xboxUhs = None
        for xui in xboxXsets['DisplayClaims']['xui']:
            if 'uhs' in xui:
                xboxUhs = xui['uhs']
                break
        if xboxUhs is None:
            eel.setCode('ERRORE 5.000')
            eel.setMessage('Non è stato possibile trovare l\'hash del GamerTag.')
            setProgress(100, 500)
            eel.setProgressError(True)
            exit(5)
        eel.setMessage('Hash del GamerTag trovato.<br/>Autenticazione su Minecraft...')
        setProgress(0, 0)

        # 6 MINEAUTH:
        def mineAuth(Token, uhs):
            url = 'https://api.minecraftservices.com/launcher/login'
            payload = {
                'xtoken': f'XBL3.0 x={uhs};{Token}',
                'platform': 'PC_LAUNCHER'
            }
            headers = {'Accept': 'application/json','Content-Type': 'application/json'}
            r = requests.post(url, headers=headers, data=json.dumps(payload))

            if r.status_code != 200: 
                eel.setCode(f'ERRORE 6.{r.status_code}')
                eel.setMessage('Non è stato possibile autenticarsi su Minecraft.')
                setProgress(100, 500)
                eel.setProgressError(True)
                exit(6)

            r_json = json.loads(r.text)
            ### print('\033[96m' + json.dumps(r_json, indent=4) + '\033[0m')
            return r_json
        mineAuth = mineAuth(xboxXsets['Token'],xboxUhs)
        eel.setMessage('Autenticazione su Minecraft Completata.<br/>Verifica licenza di Minecraft...')
        setProgress(0, 0)

        # 7 MINELCNZ:
        def mineLcnz(access_token):
            url = f'https://api.minecraftservices.com/entitlements/license?requestId={uuid.uuid4()}'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            r = requests.get(url, headers=headers)

            if r.status_code != 200:
                eel.setCode(f'ERRORE 7.{r.status_code}')
                eel.setMessage('Non è stato possibile verificare la licenza di Minecraft.')
                setProgress(100, 500)
                eel.setProgressError(True)
                exit(7)

            r_json = json.loads(r.text)
            ### print('\033[92m' + json.dumps(r_json, indent=4) + '\033[0m')
            return r_json
        mineLcnz = mineLcnz(mineAuth['access_token'])
        eel.setMessage('Licenza di Minecraft verificata.<br/>Ottenimento informazioni profilo Minecraft...')
        setProgress(0, 0)

        # 8 MINEPRFL:
        def minePrfl(access_token):
            url = 'https://api.minecraftservices.com/minecraft/profile'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            r = requests.get(url, headers=headers)

            if r.status_code != 200:
                eel.setCode(f'ERRORE 8.{r.status_code}')
                eel.setMessage('Non è stato possibile ottenere le informazioni del profilo Minecraft.')
                setProgress(100, 500)
                eel.setProgressError(True)
                exit(8)

            r_json = json.loads(r.text)
            ### print('\033[94m' + json.dumps(r_json, indent=4) + '\033[0m')
            return r_json
        minePrfl = minePrfl(mineAuth['access_token'])
        eel.setCode('✔ '+minePrfl['name'])
        eel.setMessage('Informazioni profilo Minecraft ottenute.<br/>Download di Minecraft...')
        setProgress(0, 0)

        # 9 DOWNLOAD MINECRAFT:
        global minecraft_version, minecraft_directory
        minecraft_version = config['minecraft_version']
        minecraft_directory = os.path.dirname(os.path.abspath(__file__))+'\\.minecraft'
        
        minecraft_launcher_lib.install.install_minecraft_version(minecraft_version, minecraft_directory,callback = {
            'setStatus': lambda text: eel.setMessage(text),
            'setMax': setMaxProgress,
            'setProgress': setCurrentProgress
        })


        # 10 START MINECRAFT:
        global options
        options = {
            "username": minePrfl['name'],
            "uuid": minePrfl["id"],
            "token": mineAuth["access_token"],

            "launcherName": "Juvenes",
            "server": config['minecraft_server'],
            "port": config['minecraft_port'],
            "demo": config['minecraft_demo']
        }
        eel.setMessage('Download di Minecraft completato<br/>Avvio di Minecraft in corso...')
        setProgress(100, 0)
        startMinecraft()

    except Exception as e:
        print(e)
        eel.setCode(f'ERRORE')
        eel.setMessage(e)
        setProgress(100, 500)
        eel.setProgressError(True)
        exit(0)

@eel.expose       
def startMinecraft():
    global minecraft_version, minecraft_directory, options
    if minecraft_version is not None and minecraft_directory is not None and options is not None:
        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(minecraft_version, minecraft_directory, options)
        subprocess.call(minecraft_command)

eel.init('web')
eel.start('index.html',size=(400,200), block=False)
while True:
    eel.sleep(10)