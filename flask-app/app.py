import json
import requests

from flask import Flask, flash, render_template, request, session, url_for, redirect
from flask_wtf import CSRFProtect
import forms

import inference


app = Flask(__name__)
app.config.from_object('config')
csrf = CSRFProtect()


@app.route('/')
def index():
    return redirect(url_for('search'))


@app.route('/search', methods=["GET", "POST"])
def search():
    form = forms.GTINForm(request.form)
    if request.form is not None:
        if form.validate_on_submit():
            gtin_upc = int(form.gtin.data)

            resp = requests.get(f"https://wnpwytxwol.execute-api.us-east-1.amazonaws.com/v1/gtin_table?gtin_upc={gtin_upc}")
            ingredients = resp.json()["body-json"]["Item"]["ingredients"]["S"]

            lang_model_resp = inference.get_lang_model_response(ingredients)
            ing_label_dict = json.loads(json.loads(lang_model_resp)['content'])

            # TODO labels of ingredients ENUM in inference and template
            return render_template("pages/summary.html", ing_label_dict=ing_label_dict)

    return render_template("forms/search.html", form=form)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
