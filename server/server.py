import grpc
from concurrent import futures
from grpc_config.out import metrics_pb2_grpc, metrics_pb2
from db.connect import get_redis_conn


class MetricsServiceServicer(metrics_pb2_grpc.MetricsServiceServicer):

    def __init__(self, redis_client):
        self.rdb = redis_client

    def GetRawData(self, request, context):
        # retrieve the last/latest n records from redis
        n = request.limit
        records = self.rdb.lrange("raw_data", -n, -1)

        # return the records as the response
        return metrics_pb2.RawDataResponse(records=records)

    def GetMetrics(self, request, context):
        # retrieve metrics information
        records = self.rdb.hgetall("metrics")

        metrics = []
        for action, count in records.items():
            metrics.append(metrics_pb2.Metric(action=action, count=int(count)))

        # return the records as the response
        return metrics_pb2.MetricsResponse(metrics=metrics)


def serve():
    # create the grpc server with worker threads to process incoming requests
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # retrieve the redis client reference
    redis_client = get_redis_conn()
    # bind the MetricsServiceServicer object to the grpc server
    # so that client calls are processed appropriately
    metrics_pb2_grpc.add_MetricsServiceServicer_to_server(
        MetricsServiceServicer(redis_client), server
    )

    # start the server and wait until terminated
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


serve()
