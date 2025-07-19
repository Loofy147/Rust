use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use tracing::info;

/// Metrics collector for tracking ReasoningAgent performance
#[derive(Clone)]
pub struct MetricsCollector {
    inner: Arc<MetricsInner>,
}

struct MetricsInner {
    // Counters
    tasks_started: AtomicUsize,
    tasks_completed: AtomicUsize,
    tasks_failed: AtomicUsize,
    llm_calls_success: AtomicUsize,
    llm_calls_failed: AtomicUsize,
    kg_queries: AtomicUsize,
    vector_searches: AtomicUsize,
    
    // Timing metrics
    total_processing_time: AtomicU64, // in milliseconds
    llm_response_time: AtomicU64,     // in milliseconds
    
    // Detailed metrics
    task_durations: DashMap<String, Duration>,
    hourly_stats: DashMap<u64, HourlyStats>, // hour timestamp -> stats
    start_time: Instant,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HourlyStats {
    pub hour: u64,
    pub tasks_completed: usize,
    pub tasks_failed: usize,
    pub avg_duration_ms: f64,
    pub llm_calls: usize,
    pub kg_queries: usize,
    pub vector_searches: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemMetrics {
    pub uptime_seconds: u64,
    pub total_tasks_started: usize,
    pub total_tasks_completed: usize,
    pub total_tasks_failed: usize,
    pub success_rate: f64,
    pub avg_processing_time_ms: f64,
    pub avg_llm_response_time_ms: f64,
    pub total_llm_calls_success: usize,
    pub total_llm_calls_failed: usize,
    pub llm_success_rate: f64,
    pub total_kg_queries: usize,
    pub total_vector_searches: usize,
    pub current_hour_stats: Option<HourlyStats>,
}

impl MetricsCollector {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(MetricsInner {
                tasks_started: AtomicUsize::new(0),
                tasks_completed: AtomicUsize::new(0),
                tasks_failed: AtomicUsize::new(0),
                llm_calls_success: AtomicUsize::new(0),
                llm_calls_failed: AtomicUsize::new(0),
                kg_queries: AtomicUsize::new(0),
                vector_searches: AtomicUsize::new(0),
                total_processing_time: AtomicU64::new(0),
                llm_response_time: AtomicU64::new(0),
                task_durations: DashMap::new(),
                hourly_stats: DashMap::new(),
                start_time: Instant::now(),
            }),
        }
    }

    // Task metrics
    pub fn record_task_started(&self) {
        self.inner.tasks_started.fetch_add(1, Ordering::Relaxed);
        self.update_hourly_stats(|_stats| {
            // Don't increment task count here, wait for completion/failure
        });
    }

    pub fn record_task_completed(&self, duration: Duration) {
        self.inner.tasks_completed.fetch_add(1, Ordering::Relaxed);
        self.inner.total_processing_time.fetch_add(duration.as_millis() as u64, Ordering::Relaxed);
        
        let task_id = uuid::Uuid::new_v4().to_string();
        self.inner.task_durations.insert(task_id, duration);
        
        self.update_hourly_stats(|stats| {
            stats.tasks_completed += 1;
            // Update average duration
            let total_tasks = stats.tasks_completed + stats.tasks_failed;
            if total_tasks > 0 {
                let new_total_ms = stats.avg_duration_ms * (total_tasks - 1) as f64 + duration.as_millis() as f64;
                stats.avg_duration_ms = new_total_ms / total_tasks as f64;
            } else {
                stats.avg_duration_ms = duration.as_millis() as f64;
            }
        });
    }

    pub fn record_task_failed(&self, _duration: Duration) {
        self.inner.tasks_failed.fetch_add(1, Ordering::Relaxed);
        
        self.update_hourly_stats(|stats| {
            stats.tasks_failed += 1;
        });
    }

    // LLM metrics
    pub fn record_llm_success(&self) {
        self.inner.llm_calls_success.fetch_add(1, Ordering::Relaxed);
        self.update_hourly_stats(|stats| {
            stats.llm_calls += 1;
        });
    }

    pub fn record_llm_error(&self) {
        self.inner.llm_calls_failed.fetch_add(1, Ordering::Relaxed);
        self.update_hourly_stats(|stats| {
            stats.llm_calls += 1;
        });
    }

    pub fn record_llm_response_time(&self, duration: Duration) {
        self.inner.llm_response_time.fetch_add(duration.as_millis() as u64, Ordering::Relaxed);
    }

    // KG and vector metrics
    pub fn record_kg_query(&self) {
        self.inner.kg_queries.fetch_add(1, Ordering::Relaxed);
        self.update_hourly_stats(|stats| {
            stats.kg_queries += 1;
        });
    }

    pub fn record_vector_search(&self) {
        self.inner.vector_searches.fetch_add(1, Ordering::Relaxed);
        self.update_hourly_stats(|stats| {
            stats.vector_searches += 1;
        });
    }

    fn update_hourly_stats<F>(&self, update_fn: F)
    where
        F: FnOnce(&mut HourlyStats),
    {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() / 3600; // Convert to hours

        self.inner.hourly_stats
            .entry(now)
            .or_insert_with(|| HourlyStats {
                hour: now,
                tasks_completed: 0,
                tasks_failed: 0,
                avg_duration_ms: 0.0,
                llm_calls: 0,
                kg_queries: 0,
                vector_searches: 0,
            })
            .value_mut();

        if let Some(mut stats) = self.inner.hourly_stats.get_mut(&now) {
            update_fn(&mut stats);
        }
    }

    pub fn get_system_metrics(&self) -> SystemMetrics {
        let uptime = self.inner.start_time.elapsed().as_secs();
        let tasks_started = self.inner.tasks_started.load(Ordering::Relaxed);
        let tasks_completed = self.inner.tasks_completed.load(Ordering::Relaxed);
        let tasks_failed = self.inner.tasks_failed.load(Ordering::Relaxed);
        let llm_success = self.inner.llm_calls_success.load(Ordering::Relaxed);
        let llm_failed = self.inner.llm_calls_failed.load(Ordering::Relaxed);
        
        let success_rate = if tasks_started > 0 {
            tasks_completed as f64 / tasks_started as f64 * 100.0
        } else {
            0.0
        };

        let llm_success_rate = if (llm_success + llm_failed) > 0 {
            llm_success as f64 / (llm_success + llm_failed) as f64 * 100.0
        } else {
            0.0
        };

        let total_processing_time = self.inner.total_processing_time.load(Ordering::Relaxed);
        let avg_processing_time = if tasks_completed > 0 {
            total_processing_time as f64 / tasks_completed as f64
        } else {
            0.0
        };

        let total_llm_time = self.inner.llm_response_time.load(Ordering::Relaxed);
        let avg_llm_time = if llm_success > 0 {
            total_llm_time as f64 / llm_success as f64
        } else {
            0.0
        };

        // Get current hour stats
        let current_hour = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() / 3600;
        let current_hour_stats = self.inner.hourly_stats.get(&current_hour).map(|s| s.clone());

        SystemMetrics {
            uptime_seconds: uptime,
            total_tasks_started: tasks_started,
            total_tasks_completed: tasks_completed,
            total_tasks_failed: tasks_failed,
            success_rate,
            avg_processing_time_ms: avg_processing_time,
            avg_llm_response_time_ms: avg_llm_time,
            total_llm_calls_success: llm_success,
            total_llm_calls_failed: llm_failed,
            llm_success_rate,
            total_kg_queries: self.inner.kg_queries.load(Ordering::Relaxed),
            total_vector_searches: self.inner.vector_searches.load(Ordering::Relaxed),
            current_hour_stats,
        }
    }

    pub fn get_hourly_stats(&self, hours: usize) -> Vec<HourlyStats> {
        let current_hour = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() / 3600;

        let mut stats = Vec::new();
        for i in 0..hours {
            let hour = current_hour.saturating_sub(i as u64);
            if let Some(hour_stats) = self.inner.hourly_stats.get(&hour) {
                stats.push(hour_stats.clone());
            } else {
                stats.push(HourlyStats {
                    hour,
                    tasks_completed: 0,
                    tasks_failed: 0,
                    avg_duration_ms: 0.0,
                    llm_calls: 0,
                    kg_queries: 0,
                    vector_searches: 0,
                });
            }
        }
        
        stats.reverse(); // Oldest first
        stats
    }

    pub fn print_summary(&self) {
        let metrics = self.get_system_metrics();
        
        info!("=== ReasoningAgent Metrics Summary ===");
        info!("Uptime: {}s", metrics.uptime_seconds);
        info!("Tasks: {} started, {} completed, {} failed", 
              metrics.total_tasks_started, 
              metrics.total_tasks_completed, 
              metrics.total_tasks_failed);
        info!("Success Rate: {:.1}%", metrics.success_rate);
        info!("Avg Processing Time: {:.1}ms", metrics.avg_processing_time_ms);
        info!("LLM Calls: {} success, {} failed (success rate: {:.1}%)", 
              metrics.total_llm_calls_success, 
              metrics.total_llm_calls_failed, 
              metrics.llm_success_rate);
        info!("Avg LLM Response Time: {:.1}ms", metrics.avg_llm_response_time_ms);
        info!("KG Queries: {}", metrics.total_kg_queries);
        info!("Vector Searches: {}", metrics.total_vector_searches);
        
        if let Some(current_stats) = &metrics.current_hour_stats {
            info!("Current Hour: {} tasks completed, {} failed", 
                  current_stats.tasks_completed, 
                  current_stats.tasks_failed);
        }
    }

    pub fn export_metrics_json(&self) -> serde_json::Result<String> {
        let metrics = self.get_system_metrics();
        serde_json::to_string_pretty(&metrics)
    }

    /// Reset all metrics (useful for testing)
    pub fn reset(&self) {
        self.inner.tasks_started.store(0, Ordering::Relaxed);
        self.inner.tasks_completed.store(0, Ordering::Relaxed);
        self.inner.tasks_failed.store(0, Ordering::Relaxed);
        self.inner.llm_calls_success.store(0, Ordering::Relaxed);
        self.inner.llm_calls_failed.store(0, Ordering::Relaxed);
        self.inner.kg_queries.store(0, Ordering::Relaxed);
        self.inner.vector_searches.store(0, Ordering::Relaxed);
        self.inner.total_processing_time.store(0, Ordering::Relaxed);
        self.inner.llm_response_time.store(0, Ordering::Relaxed);
        self.inner.task_durations.clear();
        self.inner.hourly_stats.clear();
    }
}
