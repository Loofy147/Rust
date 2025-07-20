use libloading::{Library, Symbol};
use std::collections::HashMap;
use std::ffi::OsStr;
use thiserror::Error;

use crate::plugins::traits::LLMPlugin;

#[derive(Error, Debug)]
pub enum PluginError {
    #[error("Failed to load plugin library: {0}")]
    Load(#[from] libloading::Error),

    #[error("Invalid plugin")]
    InvalidPlugin,
}

pub struct DynamicPluginManager {
    loaded_plugins: HashMap<String, Library>,
}

impl DynamicPluginManager {
    pub fn new() -> Self {
        Self {
            loaded_plugins: HashMap::new(),
        }
    }

    pub fn load_plugin<P: AsRef<OsStr>>(&mut self, path: P, name: String) -> Result<(), PluginError> {
        unsafe {
            let lib = Library::new(path)?;

            // Verify plugin interface
            let create_plugin: Symbol<fn() -> Box<dyn LLMPlugin>> = lib.get(b"create_plugin")?;
            let plugin = create_plugin();

            // Validate plugin
            if plugin.get_model_name().is_empty() {
                return Err(PluginError::InvalidPlugin);
            }

            self.loaded_plugins.insert(name, lib);
            Ok(())
        }
    }

    pub async fn hot_reload_plugin(&mut self, name: &str) -> Result<(), PluginError> {
        if let Some(_) = self.loaded_plugins.remove(name) {
            // Reload plugin from file
            let plugin_path = format!("plugins/{}.so", name);
            self.load_plugin(plugin_path, name.to_string())?;
        }
        Ok(())
    }
}
