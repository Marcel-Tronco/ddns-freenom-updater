import socket, requests, os, json, time
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
from jsonschema import validate
from typing import Union, List, NoReturn

freenom_json_schema = {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "domain": {"type": "string"},
      "domain_id": {"type": "string"},
      "current_ip": {"type": "string"},
      "records": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "line": {"type": "string"},
            "type": {"type": "string"},
            "name": {"type": "string"},
            "ttl": {"type": "string"},
            "value": {"type": "string"}
          },
          "required": ["line", "type", "name", "ttl", "value"]
        }
      }
    },
    "required": ["domain", "domain_id", "records", "current_ip"]
  }
}

# paths
data_path = '/usr/src/app/data/'
data_json_path = data_path + "freenom_data.json"

# URLs
BASE_URL="https://my.freenom.com"
CAREA_URL=f"{BASE_URL}/clientarea.php"
LOGIN_URL=f"{BASE_URL}/dologin.php"
LOGOUT_URL=f"{BASE_URL}/logout.php"
def managed_url_builder(domain_name, domain_id):
  return f"{CAREA_URL}?managedns={domain_name}&domainid={domain_id}"
GET_IP_URL="https://api.ipify.org/"

# login data
freenom_email = os.environ["FREENOM_EMAIL"]
freenom_pw = os.environ["FREENOM_PW"]
s = requests.Session()

# other globals
new_ip = ""
token = ""

# IP Handling
def is_valid_ip(ip: str) -> bool:
  try:
    socket.inet_aton(ip) #Throws Error if illegal ip address is given
  except:
    return False
  return True

def get_new_ip() -> None:
  #IP Address retrieval
  try:
    x = requests.get(GET_IP_URL)
    tmp = x.text
    # IP Address validation
    if not is_valid_ip(tmp):
      print("Error: IP sent from Api is not valid. Exiting.")
      exit()
    global new_ip
    new_ip = tmp
  except Exception as error:
    update_message = f"Error requesting the ip api: {error}\nExiting."
    print(update_message)
    exit()
  return

# File Handling
def file_loader(path: str) -> Union[str, None]:
  try:
    f = open(path, 'r')
    data = f.read()
    f.close()
    return data
  except:
    print(f"Error loading file: {path}")
    return None

def file_saver(path: str, data: str) -> bool:
  try:
    f = open(path, 'w')
    data = f.write(data)
    f.close()
    return True
  except:
    print(f"Error saving file: {path}")
    return False

def load_freenom_json() -> Union[List[dict], NoReturn]:
  data = file_loader(data_json_path)
  if not data:
    print('No freenom data available.\nExiting the script.')
    exit()
  try:
    json_data = json.loads(data)
    validate(instance=json_data, schema=freenom_json_schema)
    return json_data
  except Exception as error:
    print(f"Error: data hasn't correct format\n{error}\nExiting.")
    exit()

def save_freenom_json(freenom_json: List[dict]) -> None:
  json_str = json.dumps(freenom_json)
  saving_succeeded = file_saver(data_json_path, json_str)
  if not saving_succeeded:
    print("New data could't be saved.")
  return

def error_html_path_builder(domain: str) -> str:
  error_time = time.asctime().replace(" ", "-").replace(":", "-")
  cleaned_domain = domain.replace('.','-').replace('/', '-')
  return f"{data_path}{cleaned_domain}_error_{error_time}.html"

def save_error_html(text: str, domain_name: str) -> bool:
  return file_saver(error_html_path_builder(domain_name), text)

# Logging and communication with freenom

def get_token(url: str) -> Union[str, NoReturn]:
  r = s.get(url)
  r.raise_for_status()
  soup = BeautifulSoup(r.text, "html.parser")
  token_element = soup.find("input", {'name': 'token'})
  if not token_element or not token_element['value']:
    raise RuntimeError("there's no token on this page")
  return token_element['value']

def get_login_token(url: str = CAREA_URL) -> Union[str, NoReturn]:
  return get_token(url)

def is_logged_in(r: Union[None, requests.Response], url: str = CAREA_URL) -> bool:
        if r is None:
            r = s.get(url)
            r.raise_for_status()
        return '<section class="greeting">' in r.text

def login(username: str, password: str, url: str = LOGIN_URL) -> Union[None, NoReturn]:
  global token
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
  login_succeeded = is_logged_in(r)
  if not login_succeeded:
    print('Login failed. Exiting.')
    exit()
  return

def update_ip(domain_data_list: List[dict], domain_list: List[str]) -> List[dict]:
  updated_freenom_data = []
  for domain in domain_data_list:
    domain_name = domain["domain"]
    if domain_name in domain_list:
      payload = payload_constructor(domain)
      print(f'Doing update for {domain_name}.')
      r = s.post(managed_url_builder(domain_name, domain["domain_id"]), payload)  
      update_success = update_response_checker(r, domain_name)
      if update_success:
        domain["current_ip"] = new_ip
    updated_freenom_data.append(domain)
  return updated_freenom_data

# Data Processing

def check_necessary_updates(domains: List[dict]) -> List[str]:
  updatetandum = []
  for domain in domains:
    if domain["current_ip"] != new_ip:
      updatetandum.append(domain["domain"])
  return updatetandum

def payload_constructor(domain_json: dict) -> dict:
  records = domain_json["records"]
  converted_json = {
    "dnsaction": "modify",
    "token": token
  }
  for i in range(len(records)):
    record = records[i]
    for attribute, value in record.items():
      converted_json[f"records[{i}][{attribute}]"] = value
  converted_json["records[0][value]"] = new_ip
  return converted_json

def update_response_checker(response: requests.Response, domain_name: str) -> bool:
  try:
    # no_update_error = response.text.find('class="dnserror"') == -1
    no_changes = response.text.find('There were no changes') != -1
    succesful_change = response.text.find('class="dnssuccess"') != -1
    if succesful_change:
      update_message = f'DNS-UPDATE Successfull. IP updated to:{new_ip}'
      print(update_message)
      return True
    elif no_changes:
      print('no changes made')
      return True
    else:
      print("DNS-UPDATE unsuccessfull")
      saving_succeeded = save_error_html(response.text, domain_name)
      if not saving_succeeded:
        print('Saving the Error response didnt succeed')
      return False
  except Exception as error:
    print(error)
    return False

def __main__():
  print(f"Update at {time.asctime()}")
  domains = load_freenom_json()
  get_new_ip()
  domains_to_be_updated = check_necessary_updates(domains)
  if len(domains_to_be_updated) == 0:
    print('All domains up to date.\nExiting.')
    exit()
  login(freenom_email, freenom_pw)
  updated_domains = update_ip(domains, domains_to_be_updated)
  save_freenom_json(updated_domains)
  print('Update routine finished.')

__main__()