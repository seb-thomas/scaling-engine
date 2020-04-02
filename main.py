import requests
from bs4 import BeautifulSoup

response = requests.get('https://httpbin.org/ip')

print('Your IP is {0}'.format(response.json()['origin']))
result = requests.get("https://www.whitehouse.gov/briefings-statements/")
src = result.content
soup = BeautifulSoup(src, 'lxml')

urls = []
for h2_tag in soup.find_all('h2'):
    a_tag = h2_tag.find('a')
    # urls.append(a_tag.attrs['href'])
    urls.append(a_tag.text)

print(urls)
