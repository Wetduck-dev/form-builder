Dynamic Form Builder

A dynamic web application that allows users to create custom forms, manage questions and options, collect responses, and view results in a structured dashboard.

This project is designed to demonstrate full‑stack web development concepts including dynamic UI interactions, asynchronous requests, and backend form management.
Features

    Create and manage forms
    Add multiple types of questions
    Dynamically add/remove options
    Drag & drop question ordering
    Real‑time form preview
    Submit responses
    Results dashboard
    Dynamic UI using JavaScript

Tech Stack

Backend

    Python
    Flask

Frontend

    HTML
    CSS
    JavaScript

Libraries

    SortableJS (drag & drop)

Database

    SQLite

Screenshots
Form Builder
![Form Builder](screenshots/builder.png)

Results Dashboard
![Dashboard](screenshots/dashboard.png)
View collected responses and results.

Installation

Clone the repository

                                                                    text
git clone https://github.com/Wetduck-dev/form-builder.git

Move into the project directory

                                                                    text
cd form-builder

Create a virtual environment

                                                                    text
python -m venv venv

Activate the virtual environment

Linux / macOS

                                                                    text
source venv/bin/activate

Windows

                                                                    text
venv\Scripts\activate

Install dependencies

                                                                    text
pip install -r requirements.txt

Run the application

                                                                    text
python app.py

Open in browser

                                                                    text
http://127.0.0.1:5000/admin

username: admin
password:Admin1234

Project Structure

                                                                    text
form-builder
│
├── templates
│   ├── base.html
│   ├── dashboard.html
│   ├── create_form.html
│   ├── form_renderer.html
│   └── results.html
│
├── static
│   ├── css
│   │   └── main.css
│   └── js
│       └── main.js
│
├── app.py
├── requirements.txt
└── README.md

Future Improvements

    User authentication
    Form sharing via public links
    Export results (CSV / Excel)
    REST API for forms
    Analytics for responses
    Docker support

Contributing

Contributions, issues, and feature requests are welcome.

Feel free to fork the project and submit a pull request.
License

This project is open source and available under the MIT License.
