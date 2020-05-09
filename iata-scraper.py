from bs4 import BeautifulSoup,  NavigableString, Comment
import requests
import pandas as pd 

url = 'https://www.iatatravelcentre.com/international-travel-document-news/1580226297.htm'

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
  country = None
  published_date = None
  info = ""
  country_info_df = pd.DataFrame(columns= ['country', 'published_date', 'info'])
  country = country_container.text

  current_container = country_container

  try:
    current_container = current_container.next_sibling
    published_date = current_container
  except Exception as ex:
    print("Cannot find updated date for " + country + " error " + str(ex))

  current_container = current_container.next_sibling



  try:
    while current_container.name != 'b' :
      if ( isinstance(current_container, str)):
        info += current_container
        if (len(current_container) > 0):
          info += '\n'
      current_container = current_container.next_sibling
  except Exception as ex:
    print("Cannot find travel restrictions info for " + country + " error " + str(ex))
  country_info_df = country_info_df.append({'country': country, 'published_date': published_date, 'info': info}, ignore_index=True)
  return country_info_df  




def parse_main_text(main_text):
  all_country_info_df = pd.DataFrame(columns= ['country', 'published_date', 'info'])
  contry_b_tags = main_text.findAll('b')
  for country_b_tag in contry_b_tags:
    if country_b_tag.text == 'NOTE':
      continue
    else:
      all_country_info_df = all_country_info_df.append(get_country_info(country_b_tag), ignore_index=True)
  return all_country_info_df


main_text = get_main_text(url)
df = parse_main_text(main_text)
df.to_json('IATA_data.json')

