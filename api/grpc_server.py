import grpc
from concurrent import futures
import protos.agent_pb2_grpc as agent_pb2_grpc
import protos.agent_pb2 as agent_pb2

class AgentServicer(agent_pb2_grpc.AgentServicer):
    def Health(self, request, context):
        return agent_pb2.HealthReply(status="ok")
    def GetData(self, request, context):
        # TODO: Load from storage
        return agent_pb2.DataReply(data=["stub"])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_pb2_grpc.add_AgentServicer_to_server(AgentServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()