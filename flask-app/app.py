import json
import requests
import pprint

from functools import wraps
from flask import Flask, flash, render_template, request, session, url_for, redirect
from flask_wtf import CSRFProtect
import forms

import inference


app = Flask(__name__)
app.config.from_object('config')
csrf = CSRFProtect()


def login_required(f):

    @wraps(f)
    def login_enforcer(*args, **kwargs):
        if not "sid" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return login_enforcer


@app.route('/')
def index():
    return render_template("pages/index.html")

@app.route('/login')
def login():
    print("login")
    print(request.args)
    if "code" in request.args:
        session["sid"] = request.args.get("code")
        return redirect(url_for('search'))
    else:
        from urllib.parse import urlparse, quote
        o = urlparse(request.base_url)
        
        host = o.hostname
        if host == "localhost":
            host = f"http://{host}:5000"
        else:
            host = "https://" + host

        safe_redirect_url = quote(f"https://{host}{url_for('login')}", safe="")
        return redirect(f"https://foodvisor-lm.auth.us-east-1.amazoncognito.com/oauth2/authorize?client_id=4fsa9c9emuj8up23oekojflnt8&response_type=code&scope=email+openid&redirect_uri={safe_redirect_url}")


@login_required
@app.route('/logout')
def logout():
    return redirect(url_for('index'))
    try:
        session.pop("sid")
    except:
        pass

    from urllib.parse import urlparse, quote
    o = urlparse(request.base_url)
    
    host = o.hostname
    if host == "localhost":
        host = f"http://{host}:5000"
    else:
        host = "https://" + host

    safe_redirect_url = quote(f"https://{host}{url_for('index')}", safe="")
    return redirect(f"https://foodvisor-lm.auth.us-east-1.amazoncognito.com/oauth2/authorize?client_id=4fsa9c9emuj8up23oekojflnt8&response_type=code&scope=email+openid&logout_uri={safe_redirect_url}")



@login_required
@app.route('/history')
def history():
    try:
        resp = requests.get(f"https://wnpwytxwol.execute-api.us-east-1.amazonaws.com/v1/history")
        history = resp.json()["body-json"]["Item"]["last_one"]
    except:
        history = None

    print(history, resp.content)
    return render_template('pages/history.html', history=history)


@login_required
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
