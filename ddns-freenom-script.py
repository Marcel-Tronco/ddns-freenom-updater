import socket, requests, os, json
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
freenom_email = os.environ["FREENOM_EMAIL"]
freenom_pw = os.environ["FREENOM_PW"]
freenom_domain_name = os.environ["FREENOM_DOMAIN_NAME"]
freenom_domain_id = os.environ["FREENOM_DOMAIN_ID"]
dns_data_dict = json.loads(os.environ["DNS_JSON"])
BASE_URL="https://my.freenom.com"
BASE_URL="https://my.freenom.com"
CAREA_URL=f"{BASE_URL}/clientarea.php"
LOGIN_URL=f"{BASE_URL}/dologin.php"
LOGOUT_URL=f"{BASE_URL}/logout.php"
MANAGED_URL=f"{CAREA_URL}?managedns={freenom_domain_name}&domainid={freenom_domain_id}"
GET_IP_URL="https://api.ipify.org/"
updateMade = False

current_ip = ''
new_ip = ''
s = requests.Session()
token = None
update_message = 'No update message yet'

def get_token(url: str):
  r = s.get(url)
  r.raise_for_status()
  soup = BeautifulSoup(r.text, "html.parser")
  token = soup.find("input", {'name': 'token'})
  if not token or not token['value']:
    raise RuntimeError("there's no token on this page")
  return token['value']

def get_login_token(url: str = CAREA_URL):
  return get_token(url)

def is_logged_in(r: None, url: str = CAREA_URL):
        if r is None:
            r = s.get(url)
            r.raise_for_status()
        return '<section class="greeting">' in r.text

def login(username: str, password: str, url: str = LOGIN_URL) -> bool:
  token = get_login_token()
  payload = {
    'token': token,
    'username': username,
    'password': password,
    'rememberme': ''
    }
  host_name = urlparse(url).hostname
  r = s.post(url, payload, headers={'Host': host_name, 'Referer': CAREA_URL})
  r.raise_for_status()
  return is_logged_in(r)

# load current ip
f = open("current_ip.txt", 'r')
current_ip = f.read()
f.close()
try:
  socket.inet_aton(current_ip)
  print(f"retrieved ip: {current_ip}")
except:
  print(f"Couldn't retrieve saved ip: {current_ip}")
  current_ip = ''

#IP Address retrieval
try:
  x = requests.get(GET_IP_URL)
  new_ip = x.text
  # IP Address validation
  socket.inet_aton(new_ip) #Throws Error if illegal ip address is given
  print('Gathered IP', new_ip)
except Exception as error:
  update_message = f"Error retrieving IP-Address: {error}"
  print(update_message)
  exit()
if current_ip != new_ip:
  print('Starting Login')
  #login
  try:
      login_result = login(freenom_email, freenom_pw)
      if not login_result:
        raise Exception('login failed')
  except:
    update_message = 'login failed'
    print(update_message)
    exit()
else:
  print('no update necessary.')
  exit()
payload = dns_data_dict
payload['token'] = token
payload["records[0][value]"] = new_ip
print('Doing update')
r = s.post(MANAGED_URL, payload)
try:
  no_update_error = r.text.find('class="dnserror"') == -1
  succesful_change = r.text.find('class="dnssuccess"') != -1
  print(no_update_error, succesful_change)
  if no_update_error and succesful_change:
    update_message = f'DNS-UPDATE Successfull. IP updated to:{new_ip}'
    print(update_message)
  elif current_ip != '':
      update_message = f"DNS-UPDATE unsuccessfull - no_update_error: {no_update_error}, succesful_change:{succesful_change}"
      print(update_message)
      exit()
  elif r.text.find('There were no changes') != -1:
    print('no changes made')

except:
  update_message = 'Error while updating'
  print(update_message)
  exit()

current_ip = new_ip
f = open('current_ip.txt', 'w')
f.write(current_ip)
f.close()
print('finished')