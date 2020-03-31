import requests
from bs4 import BeautifulSoup

# response = requests.get('https://httpbin.org/ip')

# print('Your IP is {0}'.format(response.json()['origin']))
result = requests.get("https://www.google.com/")
src = result.content
soup = BeautifulSoup(src, 'lxml')

# print(result.status_code)
# print(result.headers)

links = soup.find_all("a")
for link in links:
    if "About" in link.text:
        print(link)
        print(link.text)
        print(link.attrs['href'])
