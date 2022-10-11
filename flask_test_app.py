from flask import Flask, render_template

app = Flask(__name__)

headings = ('Name','Salary','Position')

data = (
    ('Jonathan','Data Scientist','$100,000'),
    ('Will','Data Analyst','$90,000'),
    ('Michael','Data Engineer','$120,000')
)

@app.route('/')
def table():
    return render_template('table.html',headings=headings,data=data)