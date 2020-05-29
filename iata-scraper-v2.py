from bs4 import BeautifulSoup,  NavigableString, Comment
import requests
import pandas as pd 
import pycountry
import pdb
import json
import re
from datetime import date
from tokenize import tokenize, untokenize, NUMBER, STRING, NAME, OP
import numpy
import demjson
from dotenv import load_dotenv
import os
import sys
from pathlib import Path  # python3 only

load_dotenv()

try:
  env = sys.argv[1]
  if (env != 'dev') & (env != 'prod'):
    raise Exception('Invalid value env value: ' + env)
except IndexError:
  raise Exception("Enter env variable `iata-scraper-v2.py dev`")

url = 'https://www.iatatravelcentre.com/international-travel-document-news/1580226297.htm'
all_countries_file = open('all_countries.json')
all_countries_json = json.load(all_countries_file)



countries_info = {}

scraping_error = []

def get_script_text(iata_url):
  main_text = None
  try:
    response = requests.get(url)
    if response.status_code == 200:
      html = response.text
      soup = BeautifulSoup(html, 'lxml')
      main_text = soup.find('div', {'id': 'svgMap'}).next_sibling.next_sibling
      return main_text
  finally:
    return main_text

def parse_raw_script(script_text):
  main_text = get_script_text(url).prettify()
  left_text = main_text.split('var svgMapDataGPD = ')
  text = left_text[1].split("new svgMap")[0].strip()
  return text

def handle_edge_case(country_alpha_2):
  unsupported_countries = ['XK']
  return country_alpha_2 in unsupported_countries

def process_a_country_dictionary(country_alpha_2, country_object):
  if handle_edge_case(country_alpha_2):
    return
  country_name = pycountry.countries.get(alpha_2=country_alpha_2).name
  body_text = country_object["gdp"]
  country_soup = BeautifulSoup(body_text, 'lxml')
  ban_description = ""
  try:
    full_ban_description = country_soup.find('p').text
    ban_description_soup = country_soup.find('br').next_sibling
    while ban_description_soup != None :
      if ( ban_description_soup.name == None):
        ban_description += ban_description_soup
      else:
        ban_description += ban_description_soup.text
      try:
        ban_description_soup = ban_description_soup.next_sibling
      except AttributeError: 
        break
    
    published_date_pattern = "^\s*(3[01]|[12][0-9]|0?[1-9])\.(1[012]|0?[1-9])\.((?:19|20)\d{2})\s*$"
    published_date = full_ban_description[10:20]
    valid_date = re.match(published_date_pattern, published_date)

    if not valid_date:
      raise Exception('Invalid publised_date: ' + published_date)

    country_info_json = {}
    country_info_json['published_date'] = published_date
    country_info_json['ISO2'] = country_alpha_2
    country_info_json['info'] = ban_description

    #find possible related countries
    possible_bannees = []

    for possible_country in all_countries_json:
      if possible_country in ban_description:
        if possible_country.upper() != country_name.upper():
          bannee_possible_iso2 = None
          try:
            bannee_possible_iso2 = pycountry.countries.search_fuzzy(possible_country)
          except NameError:
            next
          possible_bannees.append(bannee_possible_iso2[0].alpha_2)
    country_info_json["possible_bannees"] = possible_bannees
    countries_info[country_name] = country_info_json  

  except Exception as e:
    error = {}
    error['country_alpha_2'] = country_alpha_2
    error['scrape_data'] = country_soup.text
    error['python error message'] = e
    scraping_error.append(error)

def process_all_countries_dictionary(js_object_dictionary):
  countries_dict = js_object_dictionary["values"]
  for country_alpha_2 in countries_dict:
    print("Processing: " + country_alpha_2 )
    process_a_country_dictionary(country_alpha_2, countries_dict[country_alpha_2])

def send_slack_message(message):
  body = {
    "text": message
  }
  headers = {
    'Content-Type': 'application/json',
  }
  response = requests.post(os.getenv('SLACK_URL'), data=json.dumps(body), headers=headers)


def post_to_db():
  request_payload = {}
  request_payload['date'] = date.today().strftime("%d.%m.%Y")
  request_payload['scrape_data'] = countries_info
  request_payload['scraping_error'] = scraping_error

  with open('IATA_data_v2.json', 'w') as outfile:
    json.dump(request_payload, outfile)
  
  host = None
  
  if (env == 'prod'):
    host = os.getenv('PROD')
  elif env == 'dev':
    host = os.getenv('DEV')
  else:
    print('Invalid env: ' + env)
    #Send error message to be
  
  endpoint = host + '/api/v1/scraper/iata'
  headers = {
    'Content-Type': 'application/json',
    'X-TRAVELNOGO-KEY': os.getenv('X_TRAVELNOGO_KEY')
  }
  response = requests.post(endpoint, data=json.dumps(request_payload), headers=headers, timeout=300)
  return response.status_code


    
send_slack_message('Starting scraper in ' + env )
script_text = get_script_text(url)
json_object_text = parse_raw_script(script_text)
all_country_info_dictionary = demjson.decode(json_object_text)
process_all_countries_dictionary(all_country_info_dictionary)
send_slack_message('Finished scraping. Sending data to server...')
code = post_to_db()
print(code)
send_slack_message('Sever responded with: ' + str(code))