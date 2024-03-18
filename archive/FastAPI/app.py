from flask import Flask, request, render_template
from flask_uploads import UploadSet, configure_uploads, DATA
from models import engine, ColdCall, SessionLocal
import csv
from datetime import date

app = Flask(__name__)

# Настройка загрузки файлов
numbers = UploadSet('data', DATA)
app.config['UPLOADED_DATA_DEST'] = 'uploads'
configure_uploads(app, numbers)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST' and 'csvfile' in request.files:
        filename = numbers.save(request.files['csvfile'])
        filepath = numbers.path(filename)

        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            session = SessionLocal()
            for row in reader:
                new_call = ColdCall(nomer=row[0], date_of_creation=date.today())
                session.add(new_call)
            session.commit()
            session.close()

        return "Данные успешно добавлены!"

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
