import os
import random
import re
from urllib.parse import urljoin
import numpy as np
import pandas as pd
import requests
import six
import tensorflow as tf
from flask import Flask, render_template, request, session
from flask_bootstrap import Bootstrap
#from google.cloud import translate_v2 as translate
from PIL import Image
from bs4 import BeautifulSoup


with open('veg20.csv') as f:
    sclass = f.readlines()

model = tf.keras.models.load_model('model_20.h5')

app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"gKey.json"
bootstrap = Bootstrap(app)

def get_soup(url):
    response = requests.get(url, timeout=10)
    return BeautifulSoup(response.text, 'html.parser')

# def translate_text(target, text):
#     translate_client = translate.Client()
#     if isinstance(text, six.binary_type):
#         text = text.decode("utf-8_sig")
#     result = translate_client.translate(text, target_language=target)
#     return result["translatedText"]

def process_page1(url, recipe_id):
    soup = get_soup(url)

    title_elem = soup.find(class_="recipe-title-and-myfoder")
    title = title_elem.find('h1').text.strip() if title_elem.find('h1') else None
    #title = translate_text("en", title)

    pic_elem = soup.find(class_="published")
    img_tags = pic_elem.find_all('img')
    img_url = urljoin(url, img_tags[0]['src']) if img_tags else None

    items = {"recipe_id": recipe_id, "dish_img_path": img_url, "title": title}
    return items

def process_page2(url):
    result_dict = []
    items = []
    orders = []
    soup = get_soup(url)

    title_elem = soup.find(class_="recipe-title-and-myfoder")
    title = title_elem.find('h1').text.strip() if title_elem.find('h1') else None
    #title = translate_text("en", title)
    result_dict.append({'title': title})

    text_elem = soup.find('div', class_='description_text')
    text = text_elem.text.strip() if text_elem else None
    #text = translate_text("en", text)
    result_dict.append({'text': text})
    
    img_elem = soup.find(class_="published")
    img_tags = img_elem.find_all('img')
    img_url = urljoin(url, img_tags[0]['src']) if img_tags else "../static/HTMLmaterial/NoImage.jpg"
    result_dict.append({'dish_img_path': img_url})
    
    content_elem = soup.find(class_="content")
    result_text = ''.join(span.get_text(strip=True) for span in content_elem.find_all('span'))
    #result_text = translate_text("en", result_text)
    result_dict.append({'result_text': result_text})

    name_elements = soup.find_all('span', class_='name')
    quantity_elements = soup.find_all('div', class_='ingredient_quantity amount')

    for name_element, quantity_element in zip(name_elements, quantity_elements):
        material = name_element.text.strip()
        quantity = quantity_element.text.strip()
        items.append({'material': material, 'quantity': quantity})
        #material = translate_text("en", name_element.text.strip())
        #quantity = translate_text("en", quantity_element.text.strip())

    ol_element = soup.find('ol', class_='steps_wrapper')
    li_elements = ol_element.find_all('li')
    for li in li_elements:
        img_tags = li.find_all('img')
        img_url = urljoin(url, img_tags[0]['src']) if img_tags else "../static/HTMLmaterial/NoImage.jpg"
        exps = li.find_all('p')
        exp = exps[0].text.strip() if exps else None
        #exp = translate_text("en", exps[0].text.strip()) if exps else None
        orders.append({'img': img_url, 'exp': exp})

    kotu_elem = soup.find('div', class_='text_content')
    kotu_text = kotu_elem.text.strip() if kotu_elem else None
    #kotu_text = translate_text("en", kotu_elem.text.strip()) if kotu_elem else None
    result_dict.append({'kotu_text': kotu_text})

    return result_dict, items, orders

def search_recipes(df, vegetables):
    df_lower = df.apply(lambda x: x.lower() if isinstance(x, str) else x)
    vegetables_lower = [veg.lower() for veg in vegetables]
    matching_recipes = df_lower[df_lower[["veg_1", "veg_2", "veg_3", "veg_4", "veg_5"]].apply(
        lambda row: all(veg in row.values for veg in vegetables_lower), axis=1)]
    return matching_recipes['recipe_id'].tolist()

def alpha(text):
    return re.sub(r'^[\d,]+','', text)

@app.route('/')
def upload_file():
    session['items'] = []
    session['veg_list'] = []
    vegTypes = [alpha(line).strip().capitalize() for line in sclass]
    return render_template('main.html',vegTypes = vegTypes)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        return render_template('choose.html', items=session['items'], veg_list=session['veg_list'])
    
    files = request.files.getlist('upload')
    processed_images = []
    favs_list = request.form.getlist('fav')

    for file in files:
        file_name = file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        file.save(save_path)
        img = Image.open(save_path)
        img = img.convert('RGB')
        img = img.resize((221, 221))
        img = np.array(img)/255.0
        img = np.expand_dims(img, axis=0)
        processed_images.append(img)

    veg_list = []
    for img in processed_images:
        pred = model.predict(img)
        result = alpha(sclass[np.argmax(pred)]).strip()
        veg_list.append(result)
        
    session['veg_list'] = ', '.join(veg_list)

    df = pd.read_csv('recipe_dataset.csv')
    print(favs_list)
    print(veg_list)
    
    if favs_list:
        df = df[df["category"].isin(favs_list)]
    recipe_idss = search_recipes(df, veg_list)
    
    recipe_ids = []

    while len(recipe_ids) < 5:
        if len(recipe_idss) >= 5:
            recipe_ids.extend(random.sample(recipe_idss, 5 - len(recipe_ids)))
        else:
            recipe_ids.extend(recipe_idss[:len(recipe_idss)])
            print(recipe_ids)
            selected_veg = random.choice(veg_list)
            veg_list.remove(selected_veg)
            recipe_idss = search_recipes(df, veg_list)
            print(veg_list)
    print(recipe_ids)

    items = []
    for recipe_id in recipe_ids:
        load_url = f"https://cookpad.com/recipe/{recipe_id}"
        items.append(process_page1(load_url, recipe_id))

    session['items'] = items
    return render_template('choose.html', items=session['items'], veg_list=session['veg_list'])

@app.route('/predict/recipe', methods=['GET'])
def output(): 
    target_id = request.args.get("value")
    print(target_id)
    load_url = f"https://cookpad.com/recipe/{target_id}"
    recipe_dict, items, orders = process_page2(load_url)
    return render_template('recipe.html', recipe_dict=recipe_dict, items=items, orders=orders)

if __name__ == '__main__':
    app.secret_key = "123456789"
    app.run(debug=True)
