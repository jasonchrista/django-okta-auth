import json

import jwt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def login_successful(request):
    id_token = request.session.get("id_token")
    payload = jwt.decode(id_token, options={"verify_signature": False}) if id_token else {}
    return render(request, "login-successful.html", {"payload": json.dumps(payload, indent=4)})
