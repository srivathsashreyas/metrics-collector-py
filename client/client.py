import grpc
from grpc_config.out import metrics_pb2_grpc, metrics_pb2
from google.protobuf.json_format import MessageToDict
from fastapi import FastAPI
import os

app = FastAPI()


@app.get("/raw-data")
def retrieve_raw_data():
    # TODO: add logic to set limit via query params
    raw_data_response = stub.GetRawData(metrics_pb2.RawDataRequest(limit=10))
    # convert protobuf message to dictionary before returning
    return MessageToDict(raw_data_response)


@app.get("/metrics")
def retrieve_metrics():
    metrics_response = stub.GetMetrics(metrics_pb2.MetricsRequest())
    # convert protobuf message to dictionary before returning
    return MessageToDict(metrics_response)


grpc_server = (
    "localhost:50051" if "GRPC_SERVER" not in os.environ else os.environ["GRPC_SERVER"]
)

## main (initialize channel to connect to grpc server and create stub to
# call grpc server methods)
channel = grpc.insecure_channel(grpc_server)
stub = metrics_pb2_grpc.MetricsServiceStub(channel)
