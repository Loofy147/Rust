# Kubernetes Deployment for Multi-Agent Orchestrator

## Components
- **orchestrator**: Main orchestrator (scalable, autoscaled)
- **redis**: Task/message broker
- **elasticsearch**: Vector/text search
- **neo4j**: Knowledge graph
- **prometheus**: Monitoring/metrics

## Usage
1. Build and push your orchestrator Docker image to a registry (or use local cluster).
2. Apply all manifests:
   ```bash
   kubectl apply -f k8s/redis-deployment.yaml
   kubectl apply -f k8s/elasticsearch-deployment.yaml
   kubectl apply -f k8s/neo4j-deployment.yaml
   kubectl apply -f k8s/prometheus-deployment.yaml
   kubectl apply -f k8s/orchestrator-deployment.yaml
   kubectl apply -f k8s/orchestrator-service.yaml
   ```
3. Access orchestrator API at the LoadBalancer/NodePort IP.
4. Access Prometheus dashboard at port 9090.

## Scaling
- The orchestrator deployment uses a HorizontalPodAutoscaler (HPA) for CPU-based scaling.
- You can scale agent deployments similarly for high throughput.

## Notes
- For production, use persistent volumes for Elasticsearch/Neo4j.
- Secure secrets with Kubernetes secrets or external secret managers.