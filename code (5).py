```python
core_agents_code = """
import enum

class AgentCapability(enum.Enum):
    \"\"\"
    Énumération des capacités que différents types d'agents peuvent posséder.
    \"\"\"
    DATA_PREPROCESSING = 'data_preprocessing'
    FEATURE_ENGINEERING = 'feature_engineering'
    MODEL_CONSTRUCTION = 'model_construction'
    TRAINING = 'training'
    EVALUATION = 'evaluation'
    COORDINATION = 'coordination'
    SYSTEM_HEALTH = 'system_health'
    DEPLOYMENT = 'deployment'
    REPO_CLONE = 'repo_clone'
    MICROSERVICES = 'microservices'
    SECURITY_SCAN = 'security_scan'
    TESTING = 'testing'
    PERFORMANCE_MONITORING = 'performance_monitoring'
    ORCHESTRATION = 'orchestration' # Nouvelle capacité pour l'Agent Orchestrateur

class Agent:
    \"\"\"
    Classe de base pour tous les agents du système.
    Définit les attributs et méthodes fondamentales pour la communication et l'exécution de tâches.
    \"\"\"
    def __init__(self, agent_id: str, capabilities: list[AgentCapability]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.inbox = []  # Boîte de réception pour les messages entrants
        self.outbox = [] # Boîte d'envoi pour les messages sortants
        print(f"Agent {self.agent_id} initialisé avec les capacités : {[cap.value for cap in capabilities]}")

    def send_message(self, recipient_id: str, message: dict):
        \"\"\"
        Simule l'envoi d'un message à un autre agent.
        Dans une implémentation réelle, cela interagirait avec un système de messagerie global.
        \"\"\"
        print(f"Agent {self.agent_id} envoie un message à {recipient_id} : {message}")
        # La logique réelle d'envoi nécessiterait un registre global ou un service de messagerie

    def receive_message(self):
        \"\"\"
        Récupère le prochain message de la boîte de réception de l'agent.
        \"\"\"
        if self.inbox:
            message = self.inbox.pop(0)
            print(f"Agent {self.agent_id} a reçu un message : {message}")
            return message
        return None

    def process_message(self, message: dict):
        \"\"\"
        Logique de traitement générique pour les messages reçus.
        Cette méthode doit être surchargée par les sous-classes d'agents spécifiques.
        \"\"\"
        raise NotImplementedError(f"process_message non implémenté pour l'agent {self.agent_id}")

    def execute_task(self, task_description: str):
        \"\"\"
        Logique d'exécution des tâches assignées à l'agent.
        Cette méthode doit être surchargée par les sous-classes d'agents spécifiques.
        \"\"\"
        raise NotImplementedError(f"execute_task non implémenté pour l'agent {self.agent_id}")

    def __repr__(self):
        \"\"\"
        Représentation textuelle de l'objet Agent.
        \"\"\"
        return f"<Agent(id={self.agent_id}, capabilities={[cap.value for cap in self.capabilities]})>"


class OrchestrationAgent(Agent):
    \"\"\"
    L'Agent Orchestrateur est un agent spécialisé responsable de la gestion,
    du déploiement, de la surveillance et de la coordination des autres agents
    au sein du système multi-agents. Il agit comme un ingénieur architecte IA.
    \"\"\"
    def __init__(self, agent_id: str = "OrchestratorAgent", registered_agents: dict = None):
        \"\"\"
        Initialise l'Agent Orchestrateur.

        Args:
            agent_id (str): L'identifiant unique de l'orchestrateur.
            registered_agents (dict): Un dictionnaire pour maintenir un registre des agents gérés.
        \"\"\"
        super().__init__(agent_id, [AgentCapability.ORCHESTRATION])
        self.registered_agents = registered_agents if registered_agents is not None else {}
        print(f"{self.agent_id} est prêt à orchestrer le système d'agents.")

    def register_agent(self, agent_instance: Agent) -> bool:
        \"\"\"
        Enregistre une instance d'agent auprès de l'Orchestrateur.

        Args:
            agent_instance (Agent): L'instance de l'agent à enregistrer.

        Returns:
            bool: True si l'enregistrement a réussi, False sinon (si l'agent est déjà enregistré).
        \"\"\"
        if agent_instance.agent_id in self.registered_agents:
            print(f"Agent {agent_instance.agent_id} est déjà enregistré.")
            return False
        self.registered_agents[agent_instance.agent_id] = agent_instance
        print(f"Agent {agent_instance.agent_id} enregistré avec succès.")
        return True

    def unregister_agent(self, agent_id: str) -> bool:
        \"\"\"
        Désenregistre un agent du système géré par l'Orchestrateur.

        Args:
            agent_id (str): L'identifiant de l'agent à désenregistrer.

        Returns:
            bool: True si le désenregistrement a réussi, False sinon.
        \"\"\"
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
            print(f"Agent {agent_id} désenregistré.")
            return True
        print(f"Agent {agent_id} non trouvé dans le registre pour le désenregistrement.")
        return False

    def deploy_agent(self, agent_class: type, agent_id: str, *args, **kwargs) -> "Agent | None":
        \"\"\"
        Déploie (crée une instance de) un nouvel agent et l'enregistre.

        Args:
            agent_class (type): La classe de l'agent à déployer.
            agent_id (str): L'identifiant unique du nouvel agent.
            *args, **kwargs: Arguments supplémentaires à passer au constructeur de l'agent.

        Returns:
            Agent: L'instance de l'agent nouvellement déployé, ou None si une erreur s'est produite.
        \"\"\"
        print(f"Déploiement de l'agent {agent_id} de type {agent_class.__name__}...")
        try:
            # Pass capabilities through kwargs if they are provided
            new_agent_kwargs = kwargs.copy()
            if 'capabilities' not in new_agent_kwargs:
                new_agent_kwargs['capabilities'] = []

            new_agent = agent_class(agent_id, *args, **new_agent_kwargs)
            self.register_agent(new_agent)
            print(f"Agent {agent_id} déployé et enregistré.")
            return new_agent
        except Exception as e:
            print(f"Erreur lors du déploiement de l'agent {agent_id} : {e}")
            return None

    def get_agent_by_capability(self, capability: AgentCapability) -> list[Agent]:
        \"\"\"
        Recherche et retourne une liste d'agents possédant une capacité donnée.

        Args:
            capability (AgentCapability): La capacité à rechercher.

        Returns:
            list[Agent]: Une liste d'instances d'agents ayant la capacité spécifiée.
        \"\"\"
        return [
            agent for agent in self.registered_agents.values()
            if capability in agent.capabilities
        ]

    def assign_task_to_agents(self, task_description: str, target_capability: AgentCapability):
        \"\"\"
        Assigner une tâche à tous les agents qui possèdent une certaine capacité.

        Args:
            task_description (str): La description de la tâche à assigner.
            target_capability (AgentCapability): La capacité requise pour l'agent pour cette tâche.
        \"\"\"
        eligible_agents = self.get_agent_by_capability(target_capability)
        if not eligible_agents:
            print(f"Aucun agent avec la capacité '{target_capability.value}' trouvé pour cette tâche.")
            return

        print(f"Assignation de la tâche '{task_description}' aux agents avec la capacité '{target_capability.value}'.")
        for agent in eligible_agents:
            # L'orchestrateur "envoie" la tâche en l'ajoutant à la boîte de réception de l'agent
            agent.inbox.append({"type": "task", "description": task_description, "from": self.agent_id})
            print(f"Tâche envoyée à l'agent {agent.agent_id}.")

    def monitor_agent_status(self, agent_id: str):
        \"\"\"
        Surveille l'état d'un agent spécifique.

        Args:
            agent_id (str): L'identifiant de l'agent à surveiller.
        \"\"\"
        agent = self.registered_agents.get(agent_id)
        if agent:
            print(f"Statut de l'agent {agent_id}: Actif. Boîte de réception: {len(agent.inbox)} messages en attente.")
            # Des métriques plus complexes (utilisation CPU/RAM, temps de réponse)
            # pourraient être ajoutées ici dans une implémentation réelle.
        else:
            print(f"Agent {agent_id} non trouvé dans le registre pour la surveillance.")

    def process_message(self, message: dict):
        \"\"\"
        L'orchestrateur traite les messages qui lui sont spécifiquement destinés.
        Exemples : requêtes de déploiement, rapports de statut.

        Args:
            message (dict): Le message reçu par l'orchestrateur.
        \"\"\"
        message_type = message.get("type")
        sender_id = message.get("from")
        print(f"{self.agent_id} traitant un message de type '{message_type}' de {sender_id}.")

        if message_type == "deploy_request":
            agent_class_name = message.get("agent_class")
            new_agent_id = message.get("new_agent_id")
            print(f"Requête de déploiement reçue pour un agent de type '{agent_class_name}' avec ID '{new_agent_id}'.")
            # Dans un système réel, il faudrait une logique pour mapper agent_class_name à la classe Python
            # et appeler self.deploy_agent(class_reelle, new_agent_id)
        elif message_type == "status_report":
            agent_id = message.get("agent_id")
            status = message.get("status")
            print(f"Rapport de statut reçu de l'agent {agent_id} : {status}")
        else:
            print(f"Type de message non reconnu par l'Orchestrateur : {message_type}")

    def execute_task(self, task_description: str):
        \"\"\"
        L'Orchestrateur exécute des tâches liées à la gestion du système global.

        Args:
            task_description (str): La description de la tâche à exécuter.
        \"\"\"
        print(f"L'Orchestrateur exécute la tâche : {task_description}")
        if "déployer nouveau type d'agent" in task_description.lower():
            # Exemple de logique : Déployer un agent fictif pour démonstration
            print("Tentative de déploiement d'un agent de test via une tâche d'orchestration...")
            class TempTestAgent(Agent): # Définition locale pour la démo
                def __init__(self, agent_id, capabilities, **kwargs):
                    super().__init__(agent_id, capabilities)
                def process_message(self, message): print(f"{self.agent_id} traite: {message}")
                def execute_task(self, task_desc): print(f"{self.agent_id} exécute: {task_desc}")

            self.deploy_agent(TempTestAgent, "OrchestratedTestAgent_001", capabilities=[])
        # Ajoutez ici d'autres logiques de tâches d'orchestration
"""

with open("core_agents.py", "w", encoding="utf-8") as f:
    f.write(core_agents_code)

print("Le fichier core_agents.py a été sauvegardé avec succès.")
