use serde::Deserialize;
use validator::{Validate, ValidationError};
use regex::Regex;

#[derive(Debug, Deserialize, Validate)]
pub struct TaskRequest {
    #[validate(length(min = 1, max = 10000, message = "Task must be between 1 and 10000 characters"))]
    #[validate(custom = "validate_no_malicious_content")]
    pub content: String,

    #[validate(range(min = 1, max = 100))]
    pub max_results: Option<usize>,

    #[validate(custom = "validate_model_name")]
    pub model: Option<String>,
}

fn validate_no_malicious_content(content: &str) -> Result<(), ValidationError> {
    let malicious_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
    ];

    for pattern in &malicious_patterns {
        let regex = Regex::new(pattern).unwrap();
        if regex.is_match(content) {
            return Err(ValidationError::new("malicious_content"));
        }
    }
    Ok(())
}

fn validate_model_name(model: &str) -> Result<(), ValidationError> {
    // This is a placeholder for a more complex validation,
    // for example, checking against a list of available models.
    if model.len() > 50 {
        return Err(ValidationError::new("model_name_too_long"));
    }
    Ok(())
}
