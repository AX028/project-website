from flask import Flask, render_template, request, redirect


app = Flask(__name__)

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/submit', methods = ['POST'])
def submit():
  name = request.form.get('name', 'N/A')
  email = request.form.get('email', 'N/A')
  phone = request.form.get('phone', 'N/A')
  message = request.form.get('message', 'N/A')

  return render_template('submit.html', name = name, email = email, phone = phone, message = message)

if __name__ == "__main__":
    app.run(debug=True)
