from flask import Flask, render_template, request, jsonify
import requests
import re

app = Flask(__name__)

def generate_career_url(company):
    return f"https://www.{company}.com/careers"

def extract_emails(text):
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

def find_internship_section(text):
    match = re.search(r"(internship|intern)[\s\S]{0,500}", text, re.IGNORECASE)
    return match

def extract_skills(text):
    skills_keywords = [
        "python", "java", "c++", "c#", "javascript", "sql", "excel", "communication",
        "teamwork", "problem[- ]solving", "leadership", "linux", "data analysis", "machine learning"
    ]
    found_skills = set()
    for kw in skills_keywords:
        if re.search(rf"\b{kw}\b", text, re.IGNORECASE):
            found_skills.add(kw.replace("\\", ""))
    return list(found_skills)

def get_contact_page_url(company):
    patterns = [
        f"https://www.{company}.com/contact",
        f"https://www.{company}.com/contact-us",
        f"https://www.{company}.com/about/contact"
    ]
    for url in patterns:
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                return url, resp.text
        except Exception:
            continue
    return None, None

def generate_linkedin_hr_query(company):
    return f'https://www.linkedin.com/search/results/people/?keywords=HR%20%22{company}%22'

def check_company(company):
    result = {
        "company": company,
        "career_page_url": "",
        "internship_available": False,
        "required_skills": [],
        "emails_found": [],
        "linkedin_hr_query": generate_linkedin_hr_query(company)
    }
    career_url = generate_career_url(company)
    result["career_page_url"] = career_url

    try:
        resp = requests.get(career_url, timeout=8)
        if resp.status_code != 200:
            return result
        text = resp.text
    except Exception:
        return result

    internship_section = find_internship_section(text)
    if internship_section:
        result["internship_available"] = True
        section_text = internship_section.group(0)
        skills = extract_skills(section_text)
        if not skills:
            skills = extract_skills(text)
        result["required_skills"] = skills

    emails = extract_emails(text)
    if not emails:
        contact_url, contact_text = get_contact_page_url(company)
        if contact_text:
            emails = extract_emails(contact_text)
    result["emails_found"] = emails

    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    companies = data.get('companies', [])
    results = []
    for company in companies:
        company = company.strip().lower()
        if company:
            results.append(check_company(company))
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)