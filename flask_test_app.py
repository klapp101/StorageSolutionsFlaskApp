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

if(__name__ == "__main__"):
    app.run(debug=True)
