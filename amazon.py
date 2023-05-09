import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import datetime
import time
import glob
import streamlit.components.v1 as components
from datetime import timedelta
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
import seaborn as sns
import openpyxl
from io import BytesIO

st.set_page_config(layout="wide")

st.title("amazon調べる君🤖")

name = st.sidebar.text_input("キーワード検索", value="コーヒー豆")
name = name.replace(' ','+')
name = name.replace('　','+')

snum = st.sidebar.number_input('開始ページ',step=1, value=1)
num = st.sidebar.number_input('終了ページ', value=2)
num = num+1
waittime = st.sidebar.slider('読込待機時間(秒)', 1, 10, 6)

df_list=[]
for page in range(snum,num):

    url = f"https://www.amazon.co.jp/s?k={name}&page={page}"

    # time.sleep(2)
    response = requests.get(url, timeout=3.5)
    html_content = response.content
    time.sleep(waittime)
    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('div',class_='a-section a-spacing-small puis-padding-left-small puis-padding-right-small')
    page_list = []
    for row in rows:
        try:
            item_name = row.find('a').text
            # 価格
            element = row.find('span',class_="a-offscreen")
            if element:
                price = row.find('span',class_="a-offscreen").text
            else:
                price = "なし"
            #単価
            element = row.find_all('span',class_="a-size-base a-color-secondary")
            if element:
                unit_price = row.find_all('span',class_="a-size-base a-color-secondary")[-1].text
            else:
                unit_price = "なし"
            # レビュー
            element = row.find('span',class_="a-icon-alt")
            if element:
                review = row.find('span',class_="a-icon-alt").text
            elif element is None:
                review = 0
            else:
                review = 0
            # レビュー数
            element = row.find('span',class_="a-size-base s-underline-text")
            if element:
                review_c = row.find('span',class_="a-size-base s-underline-text").text
            elif element is None:
                review_c = 0
            else:
                review_c = 0
            # 閲覧数
            element = row.find('span',class_="a-size-base a-color-secondary")
            if element:
                view = row.find('span',class_="a-size-base a-color-secondary").text
            elif element is None:
                view = 0
            else:
                view = 0
            #送料
            element = row.find('span',class_="a-color-base a-text-bold")
            if element is None:
                element = "なし"
            else:
                delivery = row.find('span',class_="a-color-base a-text-bold").text
            postage = row.find_all('span',class_="a-color-base")[-1].text
            link_list = []
            for href in row.find_all('a'):
                href = href.get('href')
                link_list.append(href)
            item_code = link_list[0]
            start = item_code.find("dp/") + 3
            end = item_code.find("?", start)
            item_code_result = item_code[start:]
            if len(item_code_result) > 10:
                end = item_code.find("?", start)
                item_code_result = item_code[start:end]
            review_url = f"https://www.amazon.co.jp/product-reviews/{item_code_result}/"
            
            d  = {
                '商品名':item_name,
                '価格':price,
                '１個単価':unit_price,
                'レビュー':review,
                'レビュ数':review_c,
                '閲覧数':view,
                '納期':delivery,
                '送料':postage,
                '型番':item_code_result,
                'レビーURL':review_url,
                'ページ':page
            }
            page_list.append(d)
            df = pd.DataFrame(page_list)
        except Exception as e:
            st.write(e)

# 読み込みを確認する為URL,データ１行目を表示
    st.write(url)
    st.write(df.head(1))
    df_list.append(df)

# リストに入ったデータフレームを結合
df_page = pd.concat(df_list)


df_review = pd.DataFrame(rev_list)
try:
    df_page['価格'] = df_page['価格'].str.replace('￥','')
    df_page['１個単価'] = df_page['１個単価'].str.replace('(','').str.replace(')','').str.replace('Amazonは日本の中小企業のブランドの商品を応援しています。食品から家電まで「日本の中小企業 応援ストア」を今すぐチェック。','').str.replace('こちらからもご購入いただけます','')
    df_page['レビュー'] = df_page['レビュー'].str.replace('5つ星のうち','')
    df_page['閲覧数'] = df_page['閲覧数'].str.replace('(','').str.replace(')','')
except Exception as e:
    st.write('検索一覧の文字置換ができませんでした  ')

        
df_page = df_page.reset_index(drop=True)

time.sleep(1)
count = len(df_page)-2
st.sidebar.subheader(f'行数:{count}')
if name != "":
    st.dataframe(df_page)

# エクセルで出力する為関数作成
def df_to_xlsx(df):
    byte_xlsx = BytesIO()
    writer_xlsx = pd.ExcelWriter(byte_xlsx, engine="xlsxwriter")
    df.to_excel(writer_xlsx, index=False, sheet_name="Sheet1")
    ##-----必要に応じてexcelのフォーマット等を設定-----##
    workbook = writer_xlsx.book
    worksheet = writer_xlsx.sheets["Sheet1"]
    format1 = workbook.add_format({"num_format": "0.00"})
    worksheet.set_column("A:A", None, format1)
    writer_xlsx.save()
    ##---------------------------------------------##
    workbook = writer_xlsx.book
    out_xlsx = byte_xlsx.getvalue()
    return out_xlsx

df_xlsx = df_to_xlsx(df_page)
st.download_button(
    label="エクセル形式 データダウンロード",
    data = df_xlsx,
    file_name= f'{name}.xlsx',
)
