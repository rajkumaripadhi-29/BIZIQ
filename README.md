# BizIQ – Business Analytics Dashboard

BizIQ is a web-based **Business Intelligence and Analytics Dashboard** that allows users to upload CSV or Excel datasets and automatically generate data summaries, visualizations, and business insights.

## Features

- Upload CSV and Excel files
- Automatic data cleaning
- Automatic detection of numeric, categorical, and date/time columns
- Dataset preview
- Automatic business visualizations
- Business insights based on the uploaded data
- Custom chart builder
- Bar, Line, Scatter, and Pie charts
- Interactive charts using Plotly
- Responsive and modern dashboard interface

## Technologies Used

- Python
- Flask
- Pandas
- NumPy
- Plotly
- OpenPyXL
- HTML5
- CSS3
- JavaScript
- Bootstrap

## 📂 Project Structure

```text
BizIQ/
│
├── app.py
├── requirements.txt
│
├── templates/
│   ├── index.html
│   └── dashboard.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
│
└── utils/
    ├── data_processor.py
    ├── insights.py
    ├── visualizer.py
    └── __init__.py
