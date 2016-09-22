# Copyright (C) 2010-2013 Claudio Guarnieri.
# Copyright (C) 2014-2016 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect

from bin.utils import json_error_response
from controllers.submission.submission import SubmissionController

from bin.utils import api_post, json_default_response

results_db = settings.MONGO

class SubmissionApi:
    @api_post
    def presubmit(request, body):
        files = request.FILES.getlist("files[]")
        data = []

        if files:
            for f in files:
                data.append({
                    "name": f.name,
                    "data": f.file,
                })
            submit_type = "files"
        else:
            submit_type = body["type"]

            if submit_type != "url" or "data" not in body:
                return json_error_response("type not \"url\"")

            data = body["data"].split("\n")

        if submit_type == "url" or submit_type == "files":
            submit_id = SubmissionController.presubmit(
                submit_type=submit_type, data=data
            )
            return redirect('submission/pre', submit_id=submit_id)

        return json_error_response("submit failed")

    @api_post
    def submit(request, body):
        if "selected_files" not in body or "form" not in body or "submit_id" not in body:
            return json_error_response("Bad parameters")

        data = {
            "selected_files": body["selected_files"],
            "form": {
                "_checkboxes": {}
            }
        }

        for option in ["route", "package", "timeout", "options", "priority", "custom", "tags"]:
            if option not in body["form"]:
                return json_error_response("Expected %s in parameter \"form\", none found" % option)
            else:
                val = body["form"][option].lower()
                if val == "none" or val == "":
                    body["form"][option] = None

                data["form"][option] = body["form"][option]

        cbs = data["form"]["_checkboxes"]
        for checkbox_option in ["free", "process_memory", "memory", "enforce_timeout", "human", "services"]:
            if checkbox_option not in body["form"]:
                cbs[checkbox_option] = False
            else:
                if body["form"][checkbox_option] == "on":
                    cbs[checkbox_option] = True
                else:
                    cbs[checkbox_option] = False

        # do something with `data`
        controller = SubmissionController(submit_id=body["submit_id"])
        tasks = controller.submit(data)

        return JsonResponse({"status": True, "data": ""}, encoder=json_default_response)

    @api_post
    def filetree(request, body):
        submit_id = body.get("submit_id", 0)

        controller = SubmissionController(submit_id=submit_id)
        data = controller.get_files(astree=True)

        return JsonResponse({"status": True, "data": data}, encoder=json_default_response)