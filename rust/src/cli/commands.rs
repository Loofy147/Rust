use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "reasoning-agent")]
#[command(about = "A sophisticated reasoning agent with knowledge graphs and LLM integration")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Start the reasoning agent server
    Serve {
        #[arg(short, long, default_value = "127.0.0.1")]
        host: String,
        #[arg(short, long, default_value = "8080")]
        port: u16,
    },
    /// Process a single task
    Process {
        /// The task to process
        task: String,
    },
    /// Show system information
    Info,
}
