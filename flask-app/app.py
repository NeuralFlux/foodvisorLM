import os
import json
import requests
from urllib import parse
import time

from functools import wraps
from flask import Flask, flash, render_template, request, session, url_for, redirect
from flask_wtf import CSRFProtect
import forms

import inference
import bcode_reader


app = Flask(__name__)
app.config.from_object('config')
csrf = CSRFProtect()

PORT = app.config.get("PORT")
SCHEME_DICT = {f"localhost:{PORT}": "http"}


def login_required(f):

    @wraps(f)
    def login_enforcer(*args, **kwargs):
        if not "email" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return login_enforcer


@app.route('/')
def index():
    login_missing = "email" not in session
    return render_template("pages/index.html", login_missing=login_missing)

@app.route('/login')
def login():
    if "code" in request.args:
        auth_code = request.args.get("code")
        url = "https://foodvisor-lm.auth.us-east-1.amazoncognito.com/oauth2/token"

        parsed_url = parse.urlparse(request.url)
        scheme = SCHEME_DICT.get(parsed_url.netloc, 'https')
        safe_redirect_url = parse.quote(
            f"{scheme}://{parsed_url.netloc}{url_for('login')}",
            safe=""
        )

        payload = f'client_id=4fsa9c9emuj8up23oekojflnt8&grant_type=authorization_code&redirect_uri={safe_redirect_url}&code={auth_code}'
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload).json()

        session["id_token"] = response["id_token"]
        session["access_token"] = response["access_token"]
        session["refresh_token"] = response["refresh_token"]

        url = "https://foodvisor-lm.auth.us-east-1.amazoncognito.com/oauth2/userInfo"
        headers = {
            'Authorization': f'Bearer {session["access_token"]}'
        }
        response = requests.request("GET", url, headers=headers, data={}).json()

        session["email"] = response["email"]

        return redirect(url_for('search'))
    else:
        parsed_url = parse.urlparse(request.url)
        scheme = SCHEME_DICT.get(parsed_url.netloc, 'https')
        safe_redirect_url = parse.quote(
            f"{scheme}://{parsed_url.netloc}{url_for('login')}",
            safe=""
        )

        return redirect(f"https://foodvisor-lm.auth.us-east-1.amazoncognito.com/login?client_id=4fsa9c9emuj8up23oekojflnt8&response_type=code&scope=email+openid&redirect_uri={safe_redirect_url}")


@app.route('/logout')
@login_required
def logout():
    if "email" in session.keys():
        session.pop("email")
        session.pop("id_token")
        session.pop("access_token")
        session.pop("refresh_token")

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
    resp = requests.get(f"https://wnpwytxwol.execute-api.us-east-1.amazonaws.com/v2/history?user_email={session['email']}")
    history = resp.json()["Items"]

    # sample DynamoDB response
    # {"Items":[{"stringified_labels_json":{"S":"str"},"created_at":\
    # {"N":"str"},"gtin_upc":{"S":"str"},"user_email":{"S":"str"}}]}
    for idx in range(len(history)):
        for key in history[idx].keys():
            for dtype in history[idx][key].keys():
                history[idx][key] = history[idx][key][dtype]
            if key == "stringified_labels_json":
                # FIXME json string alternatives
                history[idx][key] = json.loads(history[idx][key].replace("'", "\""))

    return render_template('pages/history.html', history=history)


@app.route('/search', methods=["GET", "POST"])
@login_required
def search():
    # NOTE generalize function in `snapshot.js` for form data
    # NOTE as of now, only tested on Mozilla Firefox 120.0
    form = forms.GTINForm(request.form)
    if request.form is not None:
        if form.validate_on_submit():
            b64_str = form.barcode_image.data
            barcode = bcode_reader.detect_bcode(b64_str)

            gtin_upc = int(barcode.rjust(14, "0"))
            print(gtin_upc)

            resp = requests.get(f"https://wnpwytxwol.execute-api.us-east-1.amazonaws.com/v1/gtin_table?gtin_upc={gtin_upc}")
            ingredients = resp.json()["body-json"]["Item"]["ingredients"]["S"]

            lang_model_resp = inference.get_lang_model_response(ingredients)
            ing_label_dict = json.loads(json.loads(lang_model_resp)['content'])

            # add to user history
            #FIXME find stringified json alternatives
            created_at = int(time.time())
            labels_json = parse.quote(json.dumps(ing_label_dict).replace("\"", "'"), safe="")
            url = f"https://wnpwytxwol.execute-api.us-east-1.amazonaws.com/v2/history?user_email={session['email']}&created_at={created_at}&gtin_upc={gtin_upc}&stringified_labels_json={labels_json}"
            print(url)
            user_hist_resp = requests.post(url)
            print(user_hist_resp.content)

            # TODO labels of ingredients ENUM in inference and template
            return render_template("pages/summary.html", ing_label_dict=ing_label_dict)

    return render_template("forms/search.html", form=form)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)
