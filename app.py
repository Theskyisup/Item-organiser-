from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def Logins():
    if request.method == 'POST':
        name = request.form["username"]
        name2 = request.form["password"]
        if name == "BOB" and name2 == "1234":
            return render_template('classitem.html')
        return render_template('IncorLogin.html')
          
    return render_template('Login.html')

@app.route('/itemwebsite', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['username']
        return f"Hello {name}, POST request received"
    return render_template('name.html')

@app.route('/item', methods=['GET', 'POST'])
def website():
    if request.method == 'POST':
        placeholder = request.form['itemname']
        return f"Item {placeholder} added successfully"
    return render_template('classitem.html')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'




if __name__ == '__main__':
    app.run(debug=True)