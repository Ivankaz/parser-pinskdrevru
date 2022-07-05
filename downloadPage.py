import requests
from bs4 import BeautifulSoup

url = str(input('URL :> '))

nameFile = str(input('С каким названием сохранить страницу?\n:> '))

page = requests.get(url)

soup = BeautifulSoup(page.text, 'lxml')

textPage = soup.prettify()

f = open(nameFile, 'w')
f.write(textPage)
f.close()


