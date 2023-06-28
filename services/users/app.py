from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response, content_types
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
from model.users import UserModel
from uuid import uuid4
import json

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()
metrics = Metrics(namespace="Powertools")

@app.get("/users/<id>")
@tracer.capture_method
def get_user(id) -> Response:
    logger.info(f"get user {id}")

    try:
        user = UserModel.get(id)
        return Response(
            status_code = 200,
            content_type= content_types.APPLICATION_JSON,
            body = json.dumps({"data" : user.attribute_values})
        )
    except UserModel.DoesNotExist:
        return Response(
            status_code = 404,
            content_type= content_types.APPLICATION_JSON,
            body=json.dumps({ "message": f"user[{id}]: not found"})
        ) 

@app.post("/users")
@tracer.capture_method()
def post_user() -> Response:
    body = app.current_event.json_body

    user = UserModel(str(uuid4()))
    user.first_name = body.get("first_name")
    user.last_name = body.get("last_name")
    user.email = body.get("email")
    user.address = body.get("address")

    user.save()
    logger.info("user saved.")
    return Response(
        status_code = 200,
        content_type=content_types.APPLICATION_JSON,
        body = { "id" : f"{user.id}" }
    )

# Enrich logging with contextual information from Lambda
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
# Adding tracer
# See: https://awslabs.github.io/aws-lambda-powertools-python/latest/core/tracer/
@tracer.capture_lambda_handler
# ensures metrics are flushed upon request completion/failure and capturing ColdStart metric
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
