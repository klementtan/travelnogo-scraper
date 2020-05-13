from bs4 import BeautifulSoup,  NavigableString, Comment
import requests
import pandas as pd 
import pycountry
import pdb
import json
from datetime import date

url = 'https://www.iatatravelcentre.com/international-travel-document-news/1580226297.htm'
end_of_page_identifier = "If any new travel restrictions will be imposed, we will ensure that Timatic is updated accordingly. We are monitoring this outbreak very closely and we will keep you posted on the developments."
all_countries_file = open('all_countries.json')
all_countries_json = json.load(all_countries_file)

countries_info = {}

def get_main_text(iata_url):
  main_text = None
  try:
    response = requests.get(url)
    if response.status_code == 200:
      html = response.text
      soup = BeautifulSoup(html, 'lxml')
      main_text = soup.find('div', {'class': 'middle'})
  except Exception as ex:
    print(str(ex))
  finally:
    return main_text

def get_country_info(country_container):
  #Setup variables
  country = None
  published_date = None
  info = ""
  country_info_df = pd.DataFrame(columns= ['country', 'published_date', 'info'])
  country_info_json = {}

  #Get the country name
  country = country_container.text
  country_info_json[country] = {}
  
  #Add ISO2 code
  try:
    country_object =  pycountry.countries.search_fuzzy(country)[0]
    country_info_json[country]['ISO2'] = country_object.alpha_2
  except:
    country_info_json[country]['error'] = 'Cannot identify the country'
    country_info_json[country]['ISO2'] = "NA"



  current_container = country_container

  #Get published date
  try:
    current_container = current_container.next_sibling
    if (isinstance(current_container, str)):
      if 'published' in current_container:
        published_date = current_container.split("published ")[1]
      else:
        published_date = current_container
  except Exception as ex:
    print("Cannot find updated date for " + country + " error " + str(ex))

  country_info_json[country]["published_date"] = published_date

  #get the info
  current_container = current_container.next_sibling
  try:
    while current_container.name != 'b' :

      #reach end of page

      if end_of_page_identifier in current_container:
        break

      #extract the info 

      if ( isinstance(current_container, str)):
        info += current_container
        if (len(current_container) > 0):
          info += '\n'
      
      # to account for bad html formatting on iata

      if current_container.next_sibling == None:
        parent = current_container.parent
        info = parent.next_sibling.text
        break
      current_container = current_container.next_sibling
  except Exception as ex:
    print("Cannot find travel restrictions info for " + country + " error " + str(ex))

  #Add related_countries

  possible_bannees = []

  for possible_country in all_countries_json:
    if possible_country in info:
      if possible_country.upper() != country.upper():
        possible_bannees.append(pycountry.countries.search_fuzzy(possible_country)[0].alpha_2)
  
  country_info_json[country]["possible_bannees"] = possible_bannees
  country_info_json[country]["info"] = info
  countries_info.update(country_info_json)

  country_info_df = country_info_df.append({'country': country, 'published_date': published_date, 'info': info}, ignore_index=True)
  return country_info_df  




def parse_main_text(main_text):
  all_country_info_df = pd.DataFrame(columns= ['country', 'published_date', 'info'])
  contry_b_tags = main_text.findAll('b')
  for num,country_b_tag in enumerate(contry_b_tags, start=1):
    print(str(num) + '/' + str(len(contry_b_tags)))
    if country_b_tag.text == 'NOTE':
      continue
    else:
      all_country_info_df = all_country_info_df.append(get_country_info(country_b_tag), ignore_index=True)
  return all_country_info_df


main_text = get_main_text(url)
df = parse_main_text(main_text)

request_payload = {}
request_payload['date'] = date.today().strftime("%d.%m.%Y")
request_payload['scrape_data'] = countries_info

with open('IATA_data.json', 'w') as outfile:
  json.dump(request_payload, outfile)


backend_url = 'https://61d6f57d.ngrok.io'

# try:
#   response = requests.post(url + '/api/v1/scrapper/iata', data=request_payload)
#   if response.status_code == 200:
#     #update slack
# except Exception e:
#   #updatew slack
  