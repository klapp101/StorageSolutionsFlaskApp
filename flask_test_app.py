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
    
@app.route("/",methods=['GET','POST'])
def main():
    conn = connection()
    cursor = conn.cursor()
    df = pd.read_sql_query("SELECT [test_code],[test_revision],[test_description],[test_notes],[test_active],[NumOpenWorkOrders],w.WOStatus FROM [test_app].[test_api].[test_create] c INNER JOIN [test_app].dim.WorkOrders w ON c.TESTPARENT = w.TEST_KEY WHERE c.TestBoardId = 0 AND NumOpenWorkOrders > 0 AND WOStatus = 'Open'", conn)
    df_last_successful_run = pd.read_sql_query("SELECT [Name],[LastSuccessfulRun] FROM [test_app].[load].[OuvviProjects] WHERE [Index] IN (1,2)", conn)
    if request.method == 'POST':
        test_code = request.form.to_dict()
        test_code = test_code['test_code']
        cursor.execute("INSERT INTO [test_app].[test_api].[testcodes] (test_code) VALUES (?)", test_code)
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('index.html',column_names=df.columns.values, row_data=list(df.values.tolist()),
                        link_column="test_code", zip=zip, entry_column_names=df_last_successful_run.columns.values, entry_row_data=list(df_last_successful_run.values.tolist()))

@app.route('/tests')
def show_tests():
    conn = connection()
    cursor = conn.cursor()
    df = pd.read_sql_query("SELECT [test_code] FROM [test_app].[test_api].[testcodes]", conn)
    conn.close()
    return render_template('tests.html',entries=df['test_code'])

@app.route('/deletetest/<test_code>',methods=['GET','POST'])
def delete_test(test_code):
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM [test_app].[test_api].[testcodes] WHERE test_code = ?", test_code)
    conn.commit()
    print('The following test code has been removed from the database: ' + test_code)
    conn.close()
    return redirect('/tests')

if(__name__ == "__main__"):
    app.run(debug=True)
