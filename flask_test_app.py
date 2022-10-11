from flask import Flask, render_template, request

app = Flask(__name__)

headings = ('Name','Salary','Position')

data = (
    ('Jonathan','Data Scientist','$100,000'),
    ('Will','Data Analyst','$90,000'),
    ('Michael','Data Engineer','$120,000')
)

test_data = {'name':'ryan'}

@app.route('/')
def table():
    return render_template('table.html',headings=headings,data=data)

@app.route('/button', methods = ['POST'])
def my_link():
    if request.method == 'POST':
        result = request.form
        return result

if __name__ == '__main__':
  app.run(debug=True)
