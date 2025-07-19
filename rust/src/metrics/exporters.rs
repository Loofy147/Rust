use crate::metrics::collector::MetricsCollector;
use serde_json;

/// Prometheus metrics exporter (optional feature)
#[cfg(feature = "prometheus")]
pub struct PrometheusExporter {
    metrics: MetricsCollector,
}

#[cfg(feature = "prometheus")]
impl PrometheusExporter {
    pub fn new(metrics: MetricsCollector) -> Self {
        Self { metrics }
    }

    pub fn export_prometheus_format(&self) -> String {
        let system_metrics = self.metrics.get_system_metrics();

        format!(r#"
# HELP reasoning_agent_tasks_total Total number of tasks processed
# TYPE reasoning_agent_tasks_total counter
reasoning_agent_tasks_total{{status="started"}} {}
reasoning_agent_tasks_total{{status="completed"}} {}
reasoning_agent_tasks_total{{status="failed"}} {}

# HELP reasoning_agent_processing_duration_seconds Average task processing duration
# TYPE reasoning_agent_processing_duration_seconds gauge
reasoning_agent_processing_duration_seconds {}

# HELP reasoning_agent_llm_calls_total Total number of LLM calls
# TYPE reasoning_agent_llm_calls_total counter
reasoning_agent_llm_calls_total{{status="success"}} {}
reasoning_agent_llm_calls_total{{status="failed"}} {}

# HELP reasoning_agent_llm_duration_seconds Average LLM response time
# TYPE reasoning_agent_llm_duration_seconds gauge
reasoning_agent_llm_duration_seconds {}

# HELP reasoning_agent_kg_queries_total Total knowledge graph queries
# TYPE reasoning_agent_kg_queries_total counter
reasoning_agent_kg_queries_total {}

# HELP reasoning_agent_vector_searches_total Total vector searches
# TYPE reasoning_agent_vector_searches_total counter
reasoning_agent_vector_searches_total {}

# HELP reasoning_agent_uptime_seconds System uptime
# TYPE reasoning_agent_uptime_seconds gauge
reasoning_agent_uptime_seconds {}
"#,
            system_metrics.total_tasks_started,
            system_metrics.total_tasks_completed,
            system_metrics.total_tasks_failed,
            system_metrics.avg_processing_time_ms / 1000.0,
            system_metrics.total_llm_calls_success,
            system_metrics.total_llm_calls_failed,
            system_metrics.avg_llm_response_time_ms / 1000.0,
            system_metrics.total_kg_queries,
            system_metrics.total_vector_searches,
            system_metrics.uptime_seconds
        )
    }
}

pub struct JsonExporter {
    metrics: MetricsCollector,
}

impl JsonExporter {
    pub fn new(metrics: MetricsCollector) -> Self {
        Self { metrics }
    }

    pub fn export_json(&self) -> serde_json::Result<String> {
        let metrics = self.metrics.get_system_metrics();
        serde_json::to_string_pretty(&metrics)
    }
}
