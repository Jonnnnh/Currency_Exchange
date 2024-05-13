import xml.etree.ElementTree as ET
import requests
from datetime import datetime
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField
from wtforms.validators import InputRequired
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv('.env')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

if app.config['SECRET_KEY'] is None:
    raise ValueError("No SECRET_KEY set for Flask application")

def parse_xml_currency_data():
    today_date = datetime.now().strftime("%d/%m/%Y")
    url = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={today_date}"

    response = requests.get(url)
    root = ET.fromstring(response.content)

    currencies = {}
    for valute in root.findall('Valute'):
        char_code = valute.find('CharCode').text
        value = float(valute.find('Value').text.replace(',', '.'))
        nominal = int(valute.find('Nominal').text)
        currencies[char_code] = (value / nominal, valute.find('Name').text)
    return currencies


def convert_currency(amount: int, currency1: str, currency2: str):
    currencies = parse_xml_currency_data()
    rate1 = currencies[currency1][0]
    rate2 = currencies[currency2][0]
    converted_amount = (amount * rate1) / rate2
    return converted_amount


def get_currencies():
    currencies = parse_xml_currency_data()
    currency_choices = [(code, f"{code} - {name}") for code, (rate, name) in currencies.items()]
    return currency_choices


class CurrencyConvertFunaskForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        currency_choices = get_currencies()
        self.currency1.choices = currency_choices
        self.currency2.choices = currency_choices

    amount = IntegerField("Amount", validators=[InputRequired()])
    currency1 = SelectField("Currency From", validators=[InputRequired()])
    currency2 = SelectField("Currency To", validators=[InputRequired()])
    submit = SubmitField("Convert")


@app.route('/', methods=['GET', 'POST'])
def home():
    form = CurrencyConvertFunaskForm()
    if form.validate_on_submit():
        amount = form.amount.data
        currency1 = form.currency1.data
        currency2 = form.currency2.data

        if currency1 == currency2:
            error = "Please choose different currencies."
            return render_template('index.html', form=form, error=error)

        converted_amount = convert_currency(amount, currency1, currency2)
        converted_data = {
            'amount': amount,
            'currency1': currency1,
            'currency2': currency2,
            'converted_amount': converted_amount
        }
        return render_template('index.html', form=form, converted_data=converted_data)

    return render_template('index.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
