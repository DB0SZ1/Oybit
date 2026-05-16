class OybitBaseError(Exception): pass

# Meta
class MetaTokenExpiredError(OybitBaseError): pass
class MetaRateLimitError(OybitBaseError): pass
class MetaInvalidParamError(OybitBaseError): pass
class MetaBlockedError(OybitBaseError): pass
class MetaAPIError(OybitBaseError): pass
class MetaModerationError(OybitBaseError): pass

# LinkedIn
class LinkedInTokenExpiredError(OybitBaseError): pass
class LinkedInRateLimitError(OybitBaseError): pass
class LinkedInInvalidPayloadError(OybitBaseError): pass

# OpenRouter
class OpenRouterRateLimitError(OybitBaseError): pass
class OpenRouterModelUnavailableError(OybitBaseError): pass
class OpenRouterContextWindowError(OybitBaseError): pass

# MiroFish
class MiroFishSimulationError(OybitBaseError): pass
class MiroFishEmptyOutputError(OybitBaseError): pass
class GraphRAGConfigError(OybitBaseError): pass

# Rendering
class CarouselRenderError(OybitBaseError): pass
class VideoRenderError(OybitBaseError): pass
class FontNotFoundError(OybitBaseError): pass
class SlideOverflowError(OybitBaseError): pass

# Publishing
class PostAlreadyPublishedError(OybitBaseError): pass
class PostRemovedByPlatformError(OybitBaseError): pass
class PostSuppressedError(OybitBaseError): pass

# File system
class PersonaFileNotFoundError(OybitBaseError): pass
class SimulationLogCorruptedError(OybitBaseError): pass
class VolumeNotMountedError(OybitBaseError): pass
