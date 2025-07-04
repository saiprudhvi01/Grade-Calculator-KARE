from flask import Flask, render_template_string, request, redirect, url_for, session
import os
import json
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key'
data_file = 'data/students.json'

# Load/Save data
def load_data():
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    return {"admins": [{"username": "admin", "password": "admin"}], "students": []}

def save_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)

# Grade Calculation
def calculate_grades(scores):
    mu = sum(scores) / len(scores)
    sigma = math.sqrt(sum((x - mu) ** 2 for x in scores) / len(scores))
    grades = []
    points = []

    for score in scores:
        if score >= mu + 1.65 * sigma:
            grades.append(('S', 10))
            points.append(10)
        elif score >= mu + 0.85 * sigma:
            grades.append(('A', 9))
            points.append(9)
        elif score >= mu + 0.12 * sigma:
            grades.append(('B', 8))
            points.append(8)
        elif score >= mu - 0.65 * sigma:
            grades.append(('C', 7))
            points.append(7)
        elif score >= mu - 1.04 * sigma:
            grades.append(('D', 6))
            points.append(6)
        elif score >= mu - 1.23 * sigma:
            grades.append(('E', 5))
            points.append(5)
        else:
            grades.append(('U', 0))
            points.append(0)

    overall = sum(points) / len(points)
    if overall >= 9:
        overall_grade = "S"
    elif overall >= 8:
        overall_grade = "A"
    elif overall >= 7:
        overall_grade = "B"
    elif overall >= 6:
        overall_grade = "C"
    elif overall >= 5:
        overall_grade = "D"
    elif overall >= 4:
        overall_grade = "E"
    else:
        overall_grade = "U"

    return grades, overall_grade

# Routes

@app.route('/', methods=['GET', 'POST'])
def login():
    data = load_data()
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for admin in data['admins']:
            if admin['username'] == username and admin['password'] == password:
                session['admin'] = username
                return redirect(url_for('admin_dashboard'))
        for student in data['students']:
            if student['username'] == username and student['password'] == password:
                session['student'] = username
                return redirect(url_for('student_dashboard'))
        error = "Invalid credentials"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    data = load_data()
    return render_template_string(ADMIN_TEMPLATE, students=data['students'])

@app.route('/create_user', methods=['POST'])
def create_user():
    if 'admin' not in session:
        return redirect(url_for('login'))
    username = request.form['username']
    password = request.form['password']
    data = load_data()
    data['students'].append({'username': username, 'password': password, 'grades': []})
    save_data(data)
    return redirect(url_for('admin_dashboard'))

@app.route('/student')
def student_dashboard():
    if 'student' not in session:
        return redirect(url_for('login'))
    return render_template_string(STUDENT_TEMPLATE)

@app.route('/calculate', methods=['POST'])
def calculate():
    if 'student' not in session:
        return redirect(url_for('login'))
    
    data = load_data()
    username = session['student']
    student = next((s for s in data['students'] if s['username'] == username), None)

    scores = []
    for i in range(1, 7):
        val = request.form.get(f'subject{i}')
        if not val:
            return "Please fill in all scores"
        scores.append(float(val))
    
    grades, overall = calculate_grades(scores)
    student['grades'] = [{'subject': f'Subject {i+1}', 'score': scores[i], 'grade': grades[i][0], 'point': grades[i][1]} for i in range(6)]
    student['overall'] = overall
    save_data(data)
    return render_template_string(RESULT_TEMPLATE, student=student)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# HTML TEMPLATES

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Login</title><style>{{style}}</style></head>
<body><div class="box">
<h2>Login</h2>
<form method="POST">
<input type="text" name="username" placeholder="Username" required><br>
<input type="password" name="password" placeholder="Password" required><br>
<button type="submit">Login</button>
</form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
</div></body></html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Admin Dashboard</title><style>{{style}}</style></head>
<body><div class="box">
<h2>Admin Dashboard</h2>
<form method="POST" action="/create_user">
<input type="text" name="username" placeholder="Student Username" required><br>
<input type="password" name="password" placeholder="Password" required><br>
<button type="submit">Create Student</button>
</form>
<h3>Registered Students</h3>
<ul>
{% for student in students %}
<li>{{ student.username }} - Overall Grade: {{ student.get('overall', 'N/A') }}</li>
{% endfor %}
</ul>
<a href="/logout">Logout</a>
</div></body></html>
'''

STUDENT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Student Dashboard</title><style>{{style}}</style></head>
<body><div class="box">
<h2>Enter Your Subject Marks</h2>
<form method="POST" action="/calculate">
{% for i in range(1, 7) %}
<input type="number" name="subject{{i}}" placeholder="Subject {{i}} Marks" step="any" required><br>
{% endfor %}
<button type="submit">Calculate Grades</button>
</form>
<a href="/logout">Logout</a>
</div></body></html>
'''

RESULT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Result</title><style>{{style}}</style></head>
<body><div class="box">
<h2>Grade Report: {{ student.username }}</h2>
<table border="1" style="margin:auto">
<tr><th>Subject</th><th>Score</th><th>Grade</th><th>Grade Point</th></tr>
{% for g in student.grades %}
<tr>
<td>{{ g.subject }}</td>
<td>{{ g.score }}</td>
<td>{{ g.grade }}</td>
<td>{{ g.point }}</td>
</tr>
{% endfor %}
</table>
<h3>Overall Grade: {{ student.overall }}</h3>
<a href="/logout">Logout</a>
</div></body></html>
'''

# Shared CSS
style = '''
body { font-family: Arial, sans-serif; background: #f0f8ff; }
.box { width: 400px; margin: auto; padding: 30px; background: white; border-radius: 20px;
       box-shadow: 0px 4px 10px rgba(0,0,0,0.2); text-align: center; margin-top: 50px; }
input { padding: 10px; margin: 10px 0; width: 90%; border: 1px solid #ccc; border-radius: 8px; }
button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 8px; }
button:hover { background: #0056b3; }
.error { color: red; }
'''

# Inject shared style into all templates
for name in list(globals()):
    if name.endswith("_TEMPLATE"):
        globals()[name] = globals()[name].replace("{{style}}", style)

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(data_file):
        save_data(load_data())
    app.run(debug=True)
