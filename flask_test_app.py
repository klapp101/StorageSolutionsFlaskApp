from flask import Flask, render_template, request, redirect
import pyodbc
import requests
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import xmltodict
import pyodbc
import pymssql
import sqlalchemy 
from sqlalchemy import create_engine,inspect
import urllib
import json
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

def connection():
    s = 'test\test' #Your server name 
    d = 'test_app' 
    u = 'user' #Your login
    p = 'password' #Your login password
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+s+';DATABASE='+d+';UID='+u+';PWD='+ p
    conn = pyodbc.connect(cstr)
    return conn
    
@app.route('/',methods=['GET','POST'])
def home():
    conn = connection()
    df_last_successful_run = pd.read_sql_query("SELECT [Name],[LastSuccessfulRun] FROM [testapp].[load].[OuvviProjects] WHERE [Index] IN (1,2)", conn)
    conn.close()
    return render_template('home.html',column_names=df_last_successful_run.columns.values, row_data = list(df_last_successful_run.values.tolist()),zip=zip)
    
@app.route("/test_data",methods=['GET','POST'])
def main():
    conn = connection()
    cursor = conn.cursor()
    df = pd.read_sql_query("SELECT c.[BOMPARENT],[test_code],[test_revision],[test_description],[test_notes],[test_active],[NumOpenWorkOrders],w.WOStatus FROM [testapp].[testipi].[test_create] c INNER JOIN [testapp].dim.WorkOrders w ON c.BOMPARENT = w.UNIQ_KEY WHERE c.TestTestId = 0 AND NumOpenWorkOrders > 0 AND WOStatus = 'Open'", conn)
    if request.method == 'POST':
        test_data = request.form.to_dict()
        bomparent = test_data['BOMPARENT']
        test_code = test_data['test_code']
        test_revision = test_data['test_revision']
        cursor.execute("INSERT INTO [testapp].[testapi].[testcodes] (BOMPARENT,test_code,test_revision) VALUES (?, ?, ?)",bomparent,test_code,test_revision)
        conn.commit()
        conn.close()
        return redirect('/test_data')
    return render_template('index.html',column_names=df.columns.values, row_data=list(df.values.tolist()),
                        link_column="test_data", zip=zip)

@app.route('/tests')
def show_tests():
    conn = connection()
    cursor = conn.cursor()
    df = pd.read_sql_query("SELECT [test_code] FROM [testapp].[testapi].[testcodes]", conn)
    conn.close()
    return render_template('tests.html',entries=df['test_code'])

@app.route('/deletetest/<test_code>',methods=['GET','POST'])
def delete_test(test_code):
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM [testapp].[testapi].[test_codes] WHERE test_code = ?", test_code)
    conn.commit()
    print('The following test code has been removed from the database: ' + test_code)
    conn.close()
    return redirect('/tests')

@app.route('/bom_view',methods=['GET','POST'])
def bom_view_data():
    conn = connection()
    df = pd.read_sql_query("""SELECT w.WO,bc.[B],bb.[AR],[IN],[DI],[PC],[P],[C],[Q],[M]
                            from [testapp].[jukiapi].[displayTestBOM] bb
                            inner join [testapp].[testapi].[test_codes] bc ON bb.B = bc.B
                            inner join [testapp].[testapi].displayOpenWOTestList w ON bb.B = w.B
                            order by bb.B,IN""", conn)
    conn.close()
    return render_template('bom.html',column_names=df.columns.values, row_data=list(df.values.tolist()), zip=zip)

@app.route('/create_tests',methods=['GET','POST'])
def create_tests():
    data = {
        'f': 'login',
        'username': 'USER',
        'password': 'AUTOSMD'
    }

    url = 'http://127.0.0.1:5000/?'
    url = requests.get(url,params=data)
    xml_parse = xmltodict.parse(url.text)
    api_token = xml_parse['resp']['out']['token']
    print('API Token Received!')

    conn = connection()
    df = pd.read_sql_query("""SELECT test_code,test_revision,ITEMID,QUANTITY,MANUFACTURER,MPN
                            FROM [testapp].[testapi].testcodes bc
                            inner join [testapp].testapi.test_create_items i ON bc.B = i.B
                            inner join [testapp].testapi.test_create_filters f ON i.B = f.B AND i.k = f.k
                            """,conn)
    df['size'] = df.groupby(['test_code', 'I_ID'])['test_code'].transform('size')
    df['rank'] = df.groupby('I_ID').cumcount()+1
    unique_values = df['test_code'].unique()
    test_list = []
    test_list_with_errors = []
    for val in unique_values:
        final_list = []
        item_list = []
        grouped = df.groupby('test_code')
        test_group = grouped.get_group(val)
        for i, series in test_group.iterrows():
            if series['rank'] == 1 and series['size'] == 1:
                item_list = []
                solo_item = str(series['I_ID']) + ',' + str(series['Q']) + ',,,' + '(' + series['M'] + ',' + series['NUM'] + ')|'
                item_list.append(solo_item)
                final_list.append(''.join(item_list))
            elif series['rank'] == 1:
                item_list = []
                first_item = str(series['I_ID']) + ',' + str(series['Q']) + ',,,' + '(' + series['M'] + ',' + series['NUM'] + ')'
                item_list.append(first_item)
            elif series['rank'] == 2 and series['size'] == 2:
                last_item_for_second_rank = ',[{' + str(series['I_ID']) + ',' + '(' + series['M'] + ',' + series['NUM'] + ')}]|'
                item_list.append(last_item_for_second_rank)
                final_list.append(''.join(item_list))
            elif series['rank'] == series['size']:
                last_item = ',{' + str(series['I_ID']) + ',' + '(' + series['M'] + ',' + series['NUM'] + ')}]|'
                item_list.append(last_item)
                final_list.append(''.join(item_list))
            elif series['size'] > 2 and series['rank'] == 2:
                second_item = ',[{' + str(series['I_ID']) + ',' + '(' + series['M'] + ',' + series['NUM'] + ')}'
                item_list.append(second_item)
            else:
                nth_item = ',{' + str(series['I_ID']) + ',' + '(' + series['M'] + ',' + series['NUM'] + ')}'
                item_list.append(nth_item)

            test_group['item_slug'] = ''
            for i,series in test_group.iterrows():
                for j in final_list:
                    if str(series['I_ID']) in str(j):
                        test_group['item_slug'][i] = j
                    else:
                        continue

        test_group = test_group.drop_duplicates('I_ID').reset_index(drop=True)
        test_list.append(test_group['test_code'].unique())
        final_slug = ''.join(final_list)[:-1]
        try:
            data = {
                'f': 'test_create',
                'tkn': api_token,
                'test_code': test_group['test_code'],
                'test_revision': test_group['test_revision'],
                'test_description': test_group['test_code'] + str('_CREATED_FROM_CREATE_TEST_BUTTON'),
                'items': final_slug}

            url_item_list = f'http://127.0.0.1:5000/?'
            url = requests.post(url_item_list,params=data)
            xml_parse = xmltodict.parse(url.text)
            test_list.append(xml_parse['test']['test']['test_id'])
        except Exception as e:
            xml_parse = xmltodict.parse(url.text)
            test_list_with_errors.append(str(xml_parse['test']['test']))


    test_id_df = pd.DataFrame(test_list)
    test_id_df.rename(columns={0:'test_id'},inplace=True)

    test_list_with_errors_df = pd.DataFrame(test_list_with_errors)
    test_list_with_errors_df.rename(columns={0:'test_id_w_error'},inplace=True)
    return render_template('tests_created.html',entries=test_id_df['test_id'], errors=test_list_with_errors_df['test_id_w_error'])

if(__name__ == "__main__"):
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True)
