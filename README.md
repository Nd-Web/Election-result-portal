# Bincom Election Results Portal — Delta State 2011

A production-quality Django web application for managing and viewing 2011 Nigerian
election results for Delta State. Polling units roll up into Wards → LGAs → States.

---

## Tech Stack

- **Backend**: Django 4.2+ (Class-Based Views, Django ORM, Django Forms)
- **Database**: MySQL via `mysqlclient`
- **Frontend**: Bootstrap 5, Chart.js
- **Forms**: django-crispy-forms + crispy-bootstrap5

---

## Prerequisites

- Python 3.9+
- MySQL Server running locally
- The `bincom_test` database already imported (see below)

---

## Setup Instructions

### 1. Clone / unzip the project

```bash
cd bincom_project
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Import the SQL database

Start your MySQL server, then run:

```bash
mysql -u root -p < path/to/bincom_test.sql
```

Or using MySQL Workbench: File → Run SQL Script → select the `.sql` file.

### 5. Configure database credentials

Open `bincom_project/settings.py` and update the `DATABASES` block if needed:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bincom_test',
        'USER': 'root',
        'PASSWORD': '',       # update if your MySQL root has a password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 6. Run the development server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

> **Note:** No `migrate` command is needed — all tables already exist in `bincom_test`
> and all models use `managed = False`.

---

## Pages & Features

### Home — `/`
Landing page with hero section and three feature cards linking to each main page.

### Question 1 — Polling Unit Results (`/polling-unit/`)
- Select any polling unit in Delta State from a dropdown.
- View per-party vote totals in a sortable table.
- Horizontal bar chart (Chart.js) of results.
- Winning party row highlighted in green.
- Total votes cast displayed.

### Question 2 — LGA Aggregated Results (`/lga-results/`)
- Select any LGA in Delta State from a dropdown.
- Votes are **summed from polling unit results** (not the `announced_lga_results` table).
- Bar chart (Chart.js) of aggregated party totals.
- Shows total votes and number of polling units counted.
- Winning party highlighted in green.

### Question 3 — Store New Polling Unit Results (`/add-result/`)
- Select any polling unit that does **not** yet have results.
- Enter vote scores per party (dynamically generated from existing party list).
- Full form validation: at least one score > 0, total ≤ 5000, no duplicate entries.
- All inserts wrapped in `transaction.atomic()` — all-or-nothing save.
- On success, redirects to the polling unit results page showing the new data.

---

## Project Structure

```
bincom_project/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── bincom_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── elections/
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── forms.py
└── templates/
    ├── base.html
    └── elections/
        ├── home.html
        ├── polling_unit.html
        ├── lga_results.html
        └── add_result.html
```
