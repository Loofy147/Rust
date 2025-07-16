default_config = {
    'agents': [
        {
            'id': 'architect_agent',
            'capabilities': ['code_analysis', 'architecture_design']
        },
        {
            'id': 'performance_agent',
            'capabilities': ['performance_optimization', 'testing_orchestration']
        },
        {
            'id': 'security_agent',
            'capabilities': ['security_audit']
        },
        {
            'id': 'doc_agent',
            'capabilities': ['documentation_generation']
        },
        {
            'id': 'test_agent',
            'capabilities': ['testing_orchestration']
        },
        {
            'id': 'deploy_agent',
            'capabilities': ['deployment_management']
        }
    ],
    'monitoring_interval': 5,
    'learning_rate': 0.1
}