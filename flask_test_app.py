from flask import Flask, render_template, request

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

@app.route('/button', methods = ['GET'])
def my_link():
#   person = request.form.get('human')
    if request.method == 'GET':
        return 'Board has been created for: ' + request.args.get('agent_id')

if __name__ == '__main__':
  app.run(debug=True)
