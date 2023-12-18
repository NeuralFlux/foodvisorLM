import os
import json
import requests
from urllib import parse

from functools import wraps
from flask import Flask, flash, render_template, request, session, url_for, redirect
from flask_wtf import CSRFProtect
import forms

import inference


app = Flask(__name__)
app.config.from_object('config')
csrf = CSRFProtect()

PORT = app.config.get("PORT")
SCHEME_DICT = {f"localhost:{PORT}": "http"}


def login_required(f):

    @wraps(f)
    def login_enforcer(*args, **kwargs):
        if not "sid" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return login_enforcer


@app.route('/')
def index():
    return render_template("pages/index.html", login_missing=True)

@app.route('/login')
def login():
    if "code" in request.args:
        session["sid"] = request.args.get("code")
        return redirect(url_for('search'))
    else:
        parsed_url = parse.urlparse(request.url)
        scheme = SCHEME_DICT.get(parsed_url.netloc, 'https')
        safe_redirect_url = parse.quote(
            f"{scheme}://{parsed_url.netloc}{url_for('login')}",
            safe=""
        )
        safe_redirect_url = parse.quote(request.url, safe="")
        return redirect(f"https://foodvisor-lm.auth.us-east-1.amazoncognito.com/login?client_id=4fsa9c9emuj8up23oekojflnt8&response_type=code&scope=email+openid&redirect_uri={safe_redirect_url}")


@app.route('/logout')
@login_required
def logout():
    if "sid" in session.keys():
        session.pop("sid")

        parsed_url = parse.urlparse(request.url)
        scheme = SCHEME_DICT.get(parsed_url.netloc, 'https')
        safe_redirect_url = parse.quote(
            f"{scheme}://{parsed_url.netloc}{url_for('index')}",
            safe=""
        )
        return redirect(f"https://foodvisor-lm.auth.us-east-1.amazoncognito.com/logout?client_id=4fsa9c9emuj8up23oekojflnt8&logout_uri={safe_redirect_url}")



@app.route('/history')
@login_required
def history():
    resp = requests.get(f"https://wnpwytxwol.execute-api.us-east-1.amazonaws.com/v1/history")
    history = resp.json()["body-json"]["Items"]

    return render_template('pages/history.html', history=history)


@app.route('/search', methods=["GET", "POST"])
@login_required
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
    app.run(host='0.0.0.0', port=PORT)
