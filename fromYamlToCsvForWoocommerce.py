import yaml
from yaml.loader import FullLoader
import csv

# список названий характеристик
featureNames = {}

# загрузка данных интернет-магазина из файла YAML
def fromYamlToStore(yamlFileName):
    print('Загружаю данные интернет-магазина из файла YAML')

    with open(yamlFileName, 'r', encoding='utf-8') as yamlFile:
        return yaml.load(yamlFile, Loader=FullLoader)

# получить словарь с данными товара по умолчанию
def getProductRowDefault():
    # словарь с данными товара для вставки в виде строки в файл CSV
    productRow = {}

    # ID
    productRow['ID'] = ''
    # тип
    productRow['Type'] = 'variable'
    # артикул (SKU)
    productRow['SKU'] = ''
    # название
    productRow['Name'] = ''
    # статус публикации
    productRow['Published'] = 1
    # избранный
    productRow['Is featured?'] = ''
    # видимый в каталоге
    productRow['Visibility in catalog'] = 'visible'
    # краткое описание
    productRow['Short description'] = ''
    # описание
    productRow['Description'] = ''
    # дата начала продаж
    productRow['Date sale price starts'] = ''
    # дата конца продаж
    productRow['Date sale price ends'] = ''
    # облагается ли налогом
    productRow['Tax status'] = 'none'
    # класс налога
    productRow['Tax class'] = ''
    # вычитать со склада
    productRow['In stock?'] = 0
    # остатки на складе
    productRow['Stock'] = ''
    # низкое количество остатков на складе
    productRow['Low stock amount'] = ''
    # разрешить заказывать товар при отсутствии на складе
    productRow['Backorders allowed?'] = 0
    # продается по отдельности
    productRow['Sold individually?'] = 0
    # вес
    productRow['Weight (unit)'] = ''
    # длина
    productRow['Length (unit)'] = ''
    # ширина
    productRow['Width (unit)'] = ''
    # высота
    productRow['Height (unit)'] = ''
    # разрешить оставлять отзывы
    productRow['Allow customer reviews?'] = 1
    # сообщение после покупки
    productRow['Purchase Note'] = ''
    # актуальная цена (со скидкой)
    productRow['Sale price'] = ''
    # обычная цена (старая)
    productRow['Regular price'] = ''
    # категория
    productRow['Categories'] = ''
    # теги
    productRow['Tags'] = ''
    # класс доставки
    productRow['Shipping class'] = ''
    # изображения
    productRow['Images'] = ''
    # лимит скачиваний
    productRow['Download limit'] = ''
    # лимит дней, в течении которых товар доступен для скачивания
    productRow['Download expiry days'] = ''
    # родитель
    productRow['Parent'] = ''
    # товары в группе
    productRow['Grouped products'] = ''
    # распродажи
    productRow['Upsells'] = ''
    # перекрестные продажи
    productRow['Cross-sells'] = ''
    # URL внешнего товара
    productRow['External URL'] = ''
    # текст кнопки "Купить"
    productRow['Button text'] = ''
    # сортировка в меню
    productRow['Position'] = ''

    return productRow

# получить число float из строки
def getFloatFromString(s):
    # это число или точка
    isDigitOrPoint = lambda x: str.isdigit(x) or '.' == x

    floatString = ''.join(filter(isDigitOrPoint, s))
    floatResult = float(floatString) or 0
    return floatResult

# получение числового значения характеристики
def getFeatureFloat(product, featureName):
    if featureName not in product['features']:
        return ''

    featureValue = product['features'][featureName]
    featureValue = getFloatFromString(featureValue)
    return featureValue

# добавить характеристику в строку информации о товаре
def addFeatureToProductRow(productRow, name, value, visible = 1, global_ = 1):
    # индекс характеристики
    featureI = len(featureNames) + 1

    # если уже добавляли эту характеристику
    for (i, featureName) in featureNames.items():
        if featureName == name:
            # запоминаем её индекс
            featureI = i
            break
    else:
        # добавляем новую характеристику в список
        featureNames[featureI] = name

    # если значение это кортеж или список
    if (type(value) == tuple) or (type(value) == list):
        # превращаем значения в строку
        value = ', '.join(value)

    featureI = str(featureI)

    productRow['Attribute '+featureI+' visible'] = visible
    productRow['Attribute '+featureI+' global'] = global_
    productRow['Attribute '+featureI+' name'] = name
    productRow['Attribute '+featureI+' value(s)'] = value


# получение словаря с данными товара для вставки строки в файл CSV
def getProductRows(product):
    # список со словарями
    productRows = []

    # словарь с данными товара для вставки в виде строки в файл CSV
    productRow = getProductRowDefault()

    # артикул (SKU)
    productRow['SKU'] = product['articul']
    # название
    productRow['Name'] = product['fullName']
    # вес
    productRow['Weight (unit)'] = getFeatureFloat(product, 'Вес')
    # длина
    productRow['Length (unit)'] = getFeatureFloat(product, 'Длина (мм)')
    # ширина
    productRow['Width (unit)'] = getFeatureFloat(product, 'Ширина (мм)')
    # высота
    productRow['Height (unit)'] = getFeatureFloat(product, 'Высота (мм)')
    # изображения
    productRow['Images'] = ', '.join(product['images'])
    # характеристики
    for (featureName, featureValue) in product['features'].items():
        addFeatureToProductRow(productRow, featureName, featureValue)

    productRows.append(productRow)

    for variation in product['variations'].values():
        variationRow = productRow.copy()

        # тип
        variationRow['Type'] = 'variation'
        # артикул родительского товара
        variationRow['Parent'] = product['articul']
        # артикул вариации
        variationRow['SKU'] = variation['articul']
        # изображения
        variationRow['Images'] = ', '.join(variation['images'])
        # цены
        if variation['oldPrice'] == 0:
            variationRow['Regular price'] = variation['currentPrice']
            variationRow['Sale price'] = ''
        else:
            variationRow['Sale price'] = variation['currentPrice']
            variationRow['Regular price'] = variation['oldPrice']
        # материал
        if 'material_name' in variation:
            addFeatureToProductRow(variationRow, 'Материал', variation['material_name'])
        # цвет
        if 'color_name' in variation:
            addFeatureToProductRow(variationRow, 'Цвет', variation['color_name'])
        # обивка
        """
        if 'onlay_name' in variation:
            addFeatureToProductRow(variationRow, 'Обивка', variation['onlay_name'])
        """

        productRows.append(variationRow)

    return productRows

# проверить наличие всех полей в массиве
def checkFieldnames(fieldnames, keys):
    for key in keys:
        if key not in fieldnames:
            fieldnames.append(key)

# сохранение товаров в файл CSV
def fromStoreToCsvForWoocommerce(store, csvFileName):
    print('Сохраняю товары в файл CSV')

    # если нет категорий
    if 'categories' not in store:
        print('- Нет категорий товаров')
        return

    # названия столбцов
    fieldnames = []

    # строки
    rows = []

    for category in store['categories']:
        if 'categories' not in category:
            continue

        for subcategory in category['categories']:
            if 'products' in subcategory:
                for product in subcategory['products']:
                    productRows = getProductRows(product)
                    
                    for productRow in productRows:
                        # добавляем недостающие названия столбцов в массив fieldnames
                        checkFieldnames(fieldnames, productRow.keys())
                        # категория
                        productRow['Categories'] = category['name'] + ' > ' + subcategory['name']

                    rows.extend(productRows)

    with open(csvFileName, 'w', encoding='utf-8') as csvFile:
        # диалект CSV для импорта в WooCommerce
        csv.register_dialect(
                'csvForWoocommerce',
                delimiter=';',
                quotechar='"',
                quoting=csv.QUOTE_NONNUMERIC
                )

        writer = csv.DictWriter(csvFile, dialect='csvForWoocommerce', fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)

        print(f"- Товары сохранены в файл {csvFileName}")

if __name__ == '__main__':
    # название файла YAML с данными
    yamlFileName = 'pinskdrevru.yaml'

    # название файла CSV
    csvFileName = 'pinskdrevru.csv'

    # объект интернет-магазина
    store = fromYamlToStore(yamlFileName)

    fromStoreToCsvForWoocommerce(store, csvFileName)


