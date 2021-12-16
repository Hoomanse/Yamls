from flask import Flask, request
from flask_swagger_ui import get_swaggerui_blueprint

import aws_s3_service
import master

app = Flask(__name__)


@app.route("/long-report", methods=['POST'])
def create_long_report():
    report_file_name = master.create_long_report(request.get_data())
    return aws_s3_service.upload_file('../out/' + report_file_name, report_file_name)


if __name__ == '__main__':
    SWAGGER_URL = '/index.html'
    API_URL = '/static/long_report.json'
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Long Report Generator"
        }
    )
    app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
    app.run(threaded=False, debug=True, host='0.0.0.0', port=5000)
