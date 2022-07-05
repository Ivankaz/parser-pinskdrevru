import requests
from bs4 import BeautifulSoup
import yaml
import openpyxl
import json
import random
import time

# протокол
protocol = 'https://'
# домен
domen = 'pinskdrev.ru'
# URL
url = protocol+domen

# интернет-магазин
store = {}

# название файла YAML с добытыми данными
fileName = domen.replace('.', '') + '.yaml'

# файл лога
fileLog = open('log.txt', 'w')

# добавить сообщение в лог
def log(*message):
    message = [str(m) for m in message]
    message = ''.join(message)
    fileLog.write(message+'\n')

# сохранить объект интернет-магазина
def saveStore():
    log('Сохраняю объект интернет-магазина')

    fileYaml = open(fileName, 'w')
    yaml.dump(store, fileYaml, encoding='UTF-8', allow_unicode=True)
    fileYaml.close()

    log('Данные сохранены в файл ',fileName)

# получить код страницы
def getPage(url = None):
    # делаем паузу
    time.sleep(random.randrange(2, 4))

    page = requests.get(url)
    if page.ok:
        print('[OK]',url)
        return page.text
    else:
        print('getPage()')
        print(url,page.status_code)
        return None

# получить категории товаров
def getCategories(soup, store):
    log('Получаю категории товаров')

    # элементы категорий
    categoryElements = soup.find('div', class_='catalog_block').find_all('div', class_='catalog_block-item')

    log('- Количество категорий: ',len(categoryElements))

    # если категорий нет
    if len(categoryElements) == 0:
        return

    store['categories'] = []

    for categoryElement in categoryElements:
        # основная категория
        category = {}
        # элемент
        categoryLinkElement = categoryElement.find('div', class_='title-catalog').find('a')
        # название
        category['name'] = categoryLinkElement.get_text(strip=True)
        log('- Название категории: ',category['name'])
        # ссылка
        category['link'] = url + categoryLinkElement.get('href')
        log('- Ссылка на категорию: ',category['link'])

        getSubcategories(categoryElement, category)
        store['categories'].append(category)

# получить подкатегории товаров
def getSubcategories(soup, category):
    log('Получаю подкатегории товаров')

    # элементы подкатегорий
    subcategoryElements = soup.find('ul').find_all('a')

    log('- Количество подкатегорий: ',len(subcategoryElements))

    # если нет подкатегорий
    if len(subcategoryElements) == 0:
        return

    category['categories'] = []

    for subcategoryElement in subcategoryElements:
        # подкатегория
        subcategory = {}
        # название
        subcategory['name'] = subcategoryElement.get_text(strip=True)
        log('- Название подкатегории: ',subcategory['name'])
        # ссылка
        subcategory['link'] = url + subcategoryElement.get('href')
        log('- Ссылка на подкатегорию: ',subcategory['link'])

        category['categories'].append(subcategory)

# получить ссылки на наборы товаров
def getLinksToProductSets(category, productSetElements):
    log('Получаю ссылки на наборы товаров')
    log('- Количество наборов товаров: ',len(productSetElements))
    # если нет наборов товаров
    if len(productSetElements) == 0:
        return

    category['productSets'] = []
    
    for productSetElement in productSetElements:
        # набор товаров
        productSet = {}
        # ссылка
        productSet['link'] = url + productSetElement.find('a', recursive=False).get('href')
        log('- Ссылка на набор товаров: ',productSet['link'])
        category['productSets'].append(productSet)

# получить ссылки на товары
def getLinksToProducts(category, productElements):
    log('Получаю ссылки на товары')
    log('- Количество товаров: ',len(productElements))
    # если нет товаров
    if len(productElements) == 0:
        return

    category['products'] = []

    for productElement in productElements:
        # товар
        product = {}
        # ссылка
        product['link'] = url + productElement.find('a', class_='product-form__product-name').get('href')
        log('- Ссылка на товар: ',product['link'])
        category['products'].append(product)

# получить артикул товара
def getProductArticul(soup, product):
    log('Получаю артикул товара')
    product['articul'] = soup.find('input', attrs = {'name': 'product_id'}).get('value')
    log('- Артикул товара: ',product['articul'])

# получить полное название товара
def getProductFullName(soup, product):
    log('Получаю полное название товара')
    product['fullName'] = soup.find('h1', attrs = {'itemprop': 'name'}).get_text(strip=True)
    log('- Полное название товара: ',product['fullName'])

# получить артикул вариации товара
def getProductVariationArticul(variation):
    log('Получаю артикул вариации товара')
    variation['articul'] = variation.pop('id')
    log('- Артикул вариации товара: ',variation['articul'])

# подготовить значение цены товара
def preparePrice(price):
   return float(price) if price != None else 0

# получить все цены вариации товара
def getProductVariationPrices(variation):
    log('Получаю цены вариации товара')

    # актуальная цена
    variation['currentPrice'] = 0
    # старая цена
    variation['oldPrice'] = 0
    # базовая цена
    variation['basePrice'] = 0

    if 'price' not in variation:
        log('- Нет информации о ценах')
        return

    if (variation['price']):
        variationPrices = variation.pop('price')
        # актуальная цена
        variation['currentPrice'] = preparePrice(variationPrices['price'])
        # старая цена
        variation['oldPrice'] = preparePrice(variationPrices['old_price'])
        # базовая цена
        variation['basePrice'] = preparePrice(variationPrices['base_price'])

    log('- Актуальная цена: ',variation['currentPrice'])
    log('- Старая цена: ',variation['oldPrice'])
    log('- Базовая цена: ',variation['basePrice'])

# получить вариации товара
def getProductVariations(soup, product):
    log('Получаю вариации товара')

    # код
    soupCode = soup.prettify()
    f = open('soupCode.html', 'w')
    f.write(soupCode)
    f.close()

    # шаблон строки перед объектом с вариациями
    startSubstring = 'offers['+str(product['articul'])+'] = '
    log('- Шаблон строки перед объектом с вариациями: ',startSubstring)
    # шаблон строки после объекта с вариациями
    endSubstring = ';'
    log('- Шаблон строки после объекта с вариациями: ',endSubstring)
    # позиция начального шаблона
    positionStartSubstring = soupCode.find(startSubstring)
    log('- Позиция начального шаблона: ',positionStartSubstring)
    # позиция конечного шаблона
    positionEndSubstring = soupCode.find(endSubstring, positionStartSubstring)
    # начальная позиция объекта с вариациями
    log('- Позиция конечного шаблона: ',positionEndSubstring)
    startPositionVariationsObject = positionStartSubstring+len(startSubstring)
    log('- Позиция начала объекта с вариациями: ',startPositionVariationsObject)
    # конечная позиция объекта с вариациями
    endPositionVariationsObject = positionEndSubstring
    log('- Позиция конца объекта с вариациями: ',endPositionVariationsObject)
    # объект с вариациями
    variationsObject = soupCode[startPositionVariationsObject:endPositionVariationsObject].strip()
    log('- Объект с вариациями: ',variationsObject)
    # вариации
    variations = json.loads(variationsObject)

    for variation in variations.values():
        log('- Вариация: ',variation)

        getProductVariationArticul(variation)
        getProductVariationPrices(variation)

        variation['images'] = []

    product['variations'] = variations
    
# получить изображения товара
def getProductImages(soup, product):
    log('Получаю изображения товара')

    product['images'] = []

    imageElements = soup.find('div', attrs={'id': 'header_slider_view'}).find_all('div', class_=['item'])

    # если нет изображений товара
    if len(imageElements) == 0:
        log('- Изображений товара нет')
        return

    for imageElement in imageElements:
        try:
            # артикул, к которому относится изображение
            imageArticul = imageElement.find('div', class_='item_inn').get('data-offer')
            # ссылка на изображение
            imageUrl = url + imageElement.find('img').get('data-img')

            if imageArticul in product['variations'].keys():
                product['variations'][imageArticul]['images'].append(imageUrl)
                log('- Изображение вариации товара: ',imageUrl)
            else:
                product['images'].append(imageUrl)
                log('- Изображение товара: ',imageUrl)
        except Exception:
            print('Ошибка получения изображения для элемента с классом\n',imageElement.get('class'))

# получить характеристики товара
def getProductFeatures(soup, product):
    log('Получаю характеристики товара')

    product['features'] = {}

    try:
        # элементы характеристик
        featureElements = soup.find('div', class_='charcs').find_all('li', class_='charcs__item')

        for featureElement in featureElements:
            # название
            featureName = featureElement.find(class_='charcs__key').get_text(strip=True).replace(':', '')
            log('- Название характеристики: ',featureName)
            # значение
            featureValue = featureElement.find(class_='charcs__value').get_text(strip=True)
            log('- Значение характеристики: ',featureValue)

            product['features'][featureName] = featureValue
    except Exception:
        pass
    
    try:
        # элементы дополнительных характеристик
        additionalFeatureElements = soup.find('ul', class_='extra-info').find_all('li', class_='extra-info__item')

        for additionalFeatureElement in additionalFeatureElements:
            # название
            additionalFeatureName = additionalFeatureElement.find(class_='extra-info__key').get_text(strip=True).replace(':', '')
            log('- Название характеристики: ',additionalFeatureName)
            # значение
            additionalFeatureValue = additionalFeatureElement.find(class_='extra-info__value').get_text(strip=True)
            log('- Значение характеристики: ',additionalFeatureValue)

            product['features'][additionalFeatureName] = additionalFeatureValue
    except Exception:
        pass

# получить информацию о товаре
def getProduct(product):
    log('Получаю информацию о товаре')
    productPage = getPage(product['link'])
    productSoup = BeautifulSoup(productPage, 'lxml')

    getProductArticul(productSoup, product)

    # детальная информация о товаре
    productDetail = productSoup.find('div', class_='cart_item_detail')
    getProductFullName(productDetail, product)

    getProductVariations(productSoup, product)

    getProductImages(productDetail, product)

    getProductFeatures(productDetail, product)

    log(product)

# получить информацию о товарах
def getProducts(category):
    log('Получаю информацию о товарах')
    # если нет товаров
    if 'products' not in category:
        log('- Товаров нет')
        return

    i = 0
    countProducts = len(category['products'])
    
    for product in category['products']:
        getProduct(product)

        saveStore()

        i += 1
        print('- Спарсил товар ',i,'/',countProducts)

        """
        askShowNext = str(input('Продолжить? [Y/n] :> '))
        if askShowNext == 'n':
            break
        """

# получить информацию о наборах товаров
def getProductSets(category):
    log('Получаю информацию о наборах товаров')
    # если нет наборов товаров
    if 'productSets' not in category:
        log('- Наборов товаров нет')
        return

    for productSet in category['productSets']:
        getProduct(productSet)

        askShowNext = str(input('Продолжить? [Y/n] :> '))
        if askShowNext == 'n':
            break

# каталог с категориями
catalogPage = getPage(url+'/catalog/')
catalogSoup = BeautifulSoup(catalogPage, 'lxml')

getCategories(catalogSoup, store)

i = 0
for category in store['categories']:
    if i >= 1:
        break
    i += 1

    log('- Категория: ',category['name'])

    # если нет подкатегорий
    if 'categories' not in category:
        continue

    j = 0
    for subcategory in category['categories']:
        if j >= 2:
            break
        j += 1

        log('- Подкатегория: ',subcategory['name'])

        """
        askFindProducts = str(input('Найти товары в подкатегории?'))
        if askFindProducts == 'n':
            break
        """

        subcategoryPage = getPage(subcategory['link'])
        subcategorySoup = BeautifulSoup(subcategoryPage, 'lxml')

        # элементы товаров
        productElements = subcategorySoup.find_all('div', class_='items_list_block__item')

        # получить ссылки на товары
        getLinksToProducts(subcategory, productElements)

        # элементы наборов товаров
        productSetElements = []
        tmp = subcategorySoup.find('div', class_='items')
        if tmp != None:
            productSetElements = tmp.find_all('div', class_='item')
        tmp = None

        # получить ссылки на наборы товаров
        getLinksToProductSets(subcategory, productSetElements)

i = 0
for category in store['categories']:
    if i >= 1:
        break
    i += 1

    print('- Категория: ',category['name'])

    # если нет подкатегорий
    if 'categories' not in category:
        continue

    j = 0
    for subcategory in category['categories']:
        if j >= 2:
            break
        j += 1

        print('- Подкатегория: ',subcategory['name'])
        getProducts(subcategory)
        #getProductSets(subcategory)

fileLog.close()
