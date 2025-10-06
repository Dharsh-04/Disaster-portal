from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from models import db, Volunteer, NGO, Request
from geopy.distance import geodesic
import json
import os

app = Flask(__name__)
app.secret_key = "secret123"

# Use SQLite in Render for simplicity (local DB file)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URL", "sqlite:///disaster_portal.db"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.template_filter('split')
def split_filter(value, sep=','):
    if not value:
        return []
    return [v.strip() for v in value.split(sep)]

# ----------------------------------------------------
# HOME PAGE
# ----------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

# ----------------------------------------------------
# VOLUNTEER ROUTES
# ----------------------------------------------------
@app.route('/volunteer_home')
def volunteer_home():
    return render_template('volunteer_home.html')

@app.route('/volunteer/register', methods=['GET', 'POST'])
def volunteer_register():
    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            skills_json = json.loads(data['skills'])
            skills_list = [s['value'] for s in skills_json if 'value' in s]
            skills_clean = ','.join(skills_list)
        except Exception:
            skills_clean = data['skills']

        new_vol = Volunteer(
            full_name=data['full_name'],
            email=data['email'],
            phone=data['phone'],
            skills=skills_clean,
            location=data['location'],
            availability=data['availability']
        )
        db.session.add(new_vol)
        db.session.commit()
        return redirect(url_for('volunteer_login'))
    return render_template('volunteer_register.html')

@app.route('/volunteer_login', methods=['GET', 'POST'])
def volunteer_login():
    if request.method == 'POST':
        email = request.form['email']
        v = Volunteer.query.filter_by(email=email).first()
        if v:
            session['volunteer_id'] = v.id
            return redirect(url_for('volunteer_dashboard'))
        return "Volunteer not found. Please register."
    return render_template('volunteer_login.html')

@app.route('/volunteer_dashboard')
def volunteer_dashboard():
    if 'volunteer_id' not in session:
        return redirect(url_for('volunteer_login'))

    vol = Volunteer.query.get(session['volunteer_id'])
    skills_clean = []

    if vol.skills:
        try:
            # Try to decode Tagify JSON
            data = json.loads(vol.skills)
            if isinstance(data, list) and all('value' in d for d in data):
                skills_clean = [d['value'].strip() for d in data]
            else:
                # Fallback if it’s a comma-separated string
                cleaned = vol.skills.replace('"value":"', '').replace('"', '').replace('{', '').replace('}', '')
                skills_clean = [s.strip() for s in cleaned.split(',')]
        except Exception:
            # Handle partially broken or semi-JSON strings like '"value":"medical,cooking,driving"'
            cleaned = vol.skills.replace('"value":"', '').replace('"', '').replace('{', '').replace('}', '')
            skills_clean = [s.strip() for s in cleaned.split(',')]

    return render_template(
        'volunteer_dashboard.html',
        volunteer=vol,
        matches=[],
        skills_list=skills_clean
    )


@app.route('/volunteer_logout')
def volunteer_logout():
    session.pop('volunteer_id', None)
    return redirect(url_for('home'))

# ----------------------------------------------------
# NGO ROUTES
# ----------------------------------------------------
@app.route('/ngo_home')
def ngo_home():
    return render_template('ngo_home.html')

@app.route('/ngo_register', methods=['GET', 'POST'])
def ngo_register():
    if request.method == 'POST':
        data = request.form
        new_ngo = NGO(
            name=data['name'],
            contact_person=data['contact_person'],
            email=data['email'],
            phone=data['phone']
        )
        db.session.add(new_ngo)
        db.session.commit()
        return redirect(url_for('ngo_login'))
    return render_template('ngo_register.html')

@app.route('/ngo_login', methods=['GET', 'POST'])
def ngo_login():
    if request.method == 'POST':
        email = request.form['email']
        ngo = NGO.query.filter_by(email=email).first()
        if ngo:
            session['ngo_id'] = ngo.id
            return redirect(url_for('ngo_dashboard'))
        return "NGO not found. Please register."
    return render_template('ngo_login.html')

@app.route('/ngo_dashboard')
def ngo_dashboard():
    if 'ngo_id' not in session:
        return redirect(url_for('ngo_login'))

    ngo = NGO.query.get(session['ngo_id'])
    requests = Request.query.filter_by(ngo_id=ngo.id).all()
    return render_template('ngo_dashboard.html', ngo=ngo, requests=requests)

@app.route('/request/new', methods=['GET', 'POST'])
def request_new():
    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            skills_json = json.loads(data['required_skills'])
            skills_list = [s['value'] for s in skills_json if 'value' in s]
            skills_clean = ','.join(skills_list)
        except Exception:
            skills_clean = data['required_skills']

        new_req = Request(
            ngo_id=session['ngo_id'],
            title=data['title'],
            description=data['description'],
            required_skills=skills_clean,
            required_volunteers=data['required_volunteers'],
            location=data['location']
        )
        db.session.add(new_req)
        db.session.commit()
        return redirect(url_for('ngo_dashboard'))
    return render_template('request_form.html')

@app.route('/ngo/request/<int:req_id>/matches')
def ngo_request_matches(req_id):
    req = Request.query.get(req_id)
    volunteers = Volunteer.query.filter_by(status='available').all()

    matches = []
    for v in volunteers:
        v_skills = [s.strip().lower() for s in v.skills.split(',')]
        r_skills = [s.strip().lower() for s in req.required_skills.split(',')]
        skill_overlap = len(set(v_skills) & set(r_skills))
        if skill_overlap > 0:
            score = skill_overlap / len(r_skills)
            matches.append({
                "volunteer": v.full_name,
                "email": v.email,
                "phone": v.phone,
                "skills": v.skills,
                "score": round(score, 2)
            })
    matches = sorted(matches, key=lambda x: x['score'], reverse=True)
    return render_template('match_results.html', req=req, matches=matches)

@app.route('/ngo_logout')
def ngo_logout():
    session.pop('ngo_id', None)
    return redirect(url_for('home'))

# ----------------------------------------------------
# RUN APP
# ----------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

