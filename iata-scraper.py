from bs4 import BeautifulSoup,  NavigableString, Comment
import requests
import pandas as pd 

base_url = 'https://www.iatatravelcentre.com/international-travel-document-news/1580226297.htm'
df = pd.DataFrame(columns= ['country', 'info'])


def parse(full_url):
  page_content = BeautifulSoup(full_url.content, 'lxml')
  containers = page_content.findAll('b', {'style': 'user-select: auto;'})
  df = pd.DataFrame(columns= ['country'])
  print(containers)
  for item in containers:
    try:
      country = item.find('b', {'style': 'user-select: auto'}).text.replace('\n', '')
      print(country)
      print(item)
    except:
      country = None
    df = df.append({'country': country}, ignore_index=True)
  df.to_csv('iata_countries.csv')
  return df

get_url = requests.get(base_url, timeout=5)
page_content = BeautifulSoup(get_url.content, 'lxml')
container = page_content.find('div', {'class': 'middle'})



for country_data in container.findAll('br'):
  try:
    print(country_data)
    print(country_data.next_sibling.strip())
  except:
    print("Cannot get")


# #data are all the countries
# #print(data)

# print(container.b.body)

# print(container.b.next_sibling.strip())
