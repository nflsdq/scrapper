import time
import json
import threading
from flask import Flask, render_template_string
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
DATA_FILE = "last_data.json"
URL = "https://pddikti.kemdiktisaintek.go.id/detail-pt/zg_3icnMAaPL1deiDeyfCBFGe1UuKmRv6Gcc94w5VGsMQqQXzV6K8fppmw7TRqsWgBLB6g=="

def get_table_data():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(URL)
    time.sleep(3)
    
    try:
        select_element = driver.find_element(By.NAME, "pagination")
        select = Select(select_element)
        select.select_by_value("semua")
        time.sleep(3)
    except:
        driver.quit()
        return []
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    
    rows = soup.select("tbody tr")
    results = [(row.find_all("td")[1].text.strip(), row.find_all("td")[9].text.strip()) for row in rows if len(row.find_all("td")) >= 10]
    return results

def load_last_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except:
        return {}

def save_data(data):
    print("Menyimpan data ke last_data.json:", data)  # Debugging
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

def check_for_changes():
    print("Thread monitoring perubahan data berjalan...")
    while True:
        new_data = get_table_data()
        last_data = load_last_data()
        print("Data terbaru:", new_data)
        print("Data terakhir:", last_data)

        if new_data and new_data != last_data:
            print("Data berubah! Menyimpan data terbaru.")
            save_data(new_data)
        else:
            print("Tidak ada perubahan data.")

        time.sleep(3600)  # Cek setiap 1 jam

def schedule_scraping():
    while True:
        check_for_changes()
        time.sleep(3600)

scraping_thread = threading.Thread(target=schedule_scraping, daemon=True)
scraping_thread.start()

@app.route('/')
def index():
    data = get_table_data()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Scraping Notifier</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h2 class="mb-4">Data Program Studi</h2>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>No</th>
                        <th>Program Studi</th>
                        <th>Jumlah Mahasiswa</th>
                    </tr>
                </thead>
                <tbody>
                    {% for index, (prodi, jumlah) in enumerate(data, start=1) %}
                    <tr>
                        <td>{{ index }}</td>
                        <td>{{ prodi }}</td>
                        <td>{{ jumlah }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    ''', data=data, enumerate=enumerate)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
