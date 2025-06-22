from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/swagger'
API_URL = '/static/openapi.yaml'

bp = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Retrorecon Swagger',
        'displayRequestDuration': True,
        'tryItOutEnabled': True,
    },
)
