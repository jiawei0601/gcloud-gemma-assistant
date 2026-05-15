class AssistantError(Exception):
    """Base exception for the AI Assistant."""
    pass

class IntelligenceProviderError(AssistantError):
    """Raised when there is an issue with the intelligence provider."""
    pass

class ModelInferenceError(IntelligenceProviderError):
    """Raised when the model inference fails."""
    pass

class DiscoveryError(AssistantError):
    """Raised when web search or scraping fails."""
    pass

class DeliveryError(AssistantError):
    """Raised when saving to Google Drive/Docs/Sheets fails."""
    pass
