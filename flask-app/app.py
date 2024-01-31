import os
import json
import requests
from urllib import parse
import time
from datetime import datetime
import re
import base64

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

def get_sanitized_redirect_url(source, dest):
    """generates a safe URL for the AUTH_ENDPOINT payload
    based on source URL protocol

    Args:
        source (str): request.url
        dest (str): url_for(<REDIRECTION DESTINATION>)
    """
    parsed_url = parse.urlparse(source)
    scheme = SCHEME_DICT.get(parsed_url.netloc, 'https')
    safe_redirect_url = parse.quote(
        f"{scheme}://{parsed_url.netloc}{dest}",
        safe=""
    )

    return safe_redirect_url

@app.route('/')
def index():
    login_missing = "email" not in session
    return render_template("pages/index.html", login_missing=login_missing)

@app.route('/login')
def login():
    if "code" in request.args:
        # store user session vars and email
        auth_code = request.args.get("code")
        url = f"{app.config.get('AUTH_ENDPOINT')}/oauth2/token"
        safe_redirect_url = get_sanitized_redirect_url(
            source=request.url,
            dest=url_for('login')
        )

        payload = f'client_id={app.config.get("AUTH_CLIENT_ID")}&grant_type=authorization_code&redirect_uri={safe_redirect_url}&code={auth_code}'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.request("POST", url, headers=headers, data=payload).json()

        session["id_token"] = response["id_token"]
        session["access_token"] = response["access_token"]
        session["refresh_token"] = response["refresh_token"]

        url = f"{app.config.get('AUTH_ENDPOINT')}/oauth2/userInfo"
        headers = {
            'Authorization': f'Bearer {session["access_token"]}'
        }
        response = requests.request("GET", url, headers=headers, data={}).json()
        session["email"] = response["email"]

        return redirect(url_for('search'))
    else:
        safe_redirect_url = get_sanitized_redirect_url(
            source=request.url,
            dest=url_for('login')
        )

        return redirect(f"{app.config.get('AUTH_ENDPOINT')}/login?client_id={app.config.get('AUTH_CLIENT_ID')}&response_type=code&scope=email+openid&redirect_uri={safe_redirect_url}")


@app.route('/logout')
@login_required
def logout():
    if "email" in session.keys():
        session.pop("email")
        session.pop("id_token")
        session.pop("access_token")
        session.pop("refresh_token")

        safe_redirect_url = get_sanitized_redirect_url(
            source=request.url,
            dest=url_for('index')
        )
        return redirect(f"{app.config.get('AUTH_ENDPOINT')}/logout?client_id={app.config.get('AUTH_CLIENT_ID')}&logout_uri={safe_redirect_url}")
    

@app.route('/similar_products', methods=["POST"])
@login_required
def similar_products():
    # sanitize and regex product_text for only alnum
    # commas, dashes, slashes
    # basic auth
    # deploy endpoint
    gtin_upc = int(request.form.get('gtin_upc'))
    product_text = re.sub(r'[^a-zA-Z0-9, &-/]', '', request.form.get('product_text'))

    opensearch_user = app.config.get('OPENSEARCH_USER')
    opensearch_pwd = app.config.get('OPENSEARCH_PWD')
    base64_str = base64.b64encode(f"{opensearch_user}:{opensearch_pwd}".encode('utf-8')).decode()
    headers = {
        'Authorization': f'Basic {base64_str}'
    }

    product_text = parse.quote(product_text)
    resp = requests.post(f"{app.config.get('API_ENDPOINT')}/similar-products?product_text={product_text}", headers=headers)
    resp_json = resp.json()
    products = []
    if "hits" in resp_json.keys() and len(resp_json["hits"]["total"]) > 0:
        products = resp_json["hits"]["hits"][1:4]
    return render_template('pages/similar_products.html', gtin=gtin_upc, products=products)


@app.route('/history')
@login_required
def history():
    resp = requests.get(f"{app.config.get('API_ENDPOINT')}/history?user_email={session['email']}")
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
                history[idx][key] = json.loads(parse.unquote(history[idx][key]).replace("'", "\""))
            elif key == "created_at":
                history[idx][key] = datetime.fromtimestamp(int(history[idx][key]) - 3600 * 5).strftime('%H:%M:%S on %d %B, %Y')

    return render_template('pages/history.html', history=history)


@app.route('/search', methods=["GET", "POST"])
@login_required
def search():
    # NOTE generalize function in `snapshot.js` for form data
    # NOTE as of now, only tested on Mozilla Firefox 120.0
    form = forms.GTINForm(request.form)
    similarity_form = forms.SimilarityForm()
    if request.form is not None:
        if form.validate_on_submit():
            gtin_upc = form.barcode_val.data

            # look for barcode only if number is not present
            if gtin_upc == '':
                b64_str = form.barcode_image.data
                barcode = bcode_reader.detect_bcode(b64_str)

                if barcode is None:
                    flash("Invalid barcode, please try again", category="error")
                    return redirect(url_for('search'))
                gtin_upc = int(barcode.rjust(14, "0"))

            resp = requests.get(f"{app.config.get('API_ENDPOINT')}/gtin-table?gtin_upc={gtin_upc}")
            resp_json = resp.json()

            if "Item" not in resp_json.keys():
                return render_template("pages/summary.html")

            ingredients = resp_json["Item"]["ingredients"]["S"]
            title = {
                "owner": resp_json["Item"]["brand_owner"]["S"],
                "name": resp_json["Item"]["brand_name"]["S"],
                "subbrand": resp_json["Item"]["subbrand_name"]["S"],
                "description": resp_json["Item"]["description"]["S"],
                "ingredients": resp_json["Item"]["ingredients"]["S"]
            }

            lang_model_resp = inference.get_lang_model_response(ingredients)
            ing_label_dict = json.loads(json.loads(lang_model_resp)['content'])

            # add to user history
            #FIXME find stringified json alternatives
            created_at = int(time.time())
            labels_json = parse.quote(json.dumps(ing_label_dict).replace("\"", "'"), safe="")
            url = f"{app.config.get('API_ENDPOINT')}/history?user_email={session['email']}&created_at={created_at}&gtin_upc={gtin_upc}&stringified_labels_json={labels_json}"
            requests.post(url)

            similarity_form.gtin_upc.data = gtin_upc
            similarity_form.product_text.data = title["description"] + " " + title["ingredients"]

            # TODO labels of ingredients ENUM in inference and template
            return render_template("pages/summary.html", ing_label_dict=ing_label_dict, title=title,
                                   gtin_upc=gtin_upc, form=similarity_form)

    return render_template("forms/search.html", form=form)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)
