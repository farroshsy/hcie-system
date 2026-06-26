"""
API Documentation Enhancement Utilities

Provides utilities for enhancing API documentation with examples,
schemas, and additional metadata for better developer experience.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class DocumentationExample(BaseModel):
    """API documentation example"""
    name: str = Field(description="Example name")
    description: Optional[str] = Field(default=None, description="Example description")
    request: Dict[str, Any] = Field(description="Example request payload")
    response: Dict[str, Any] = Field(description="Example response")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Example headers")


class APIEndpointMetadata(BaseModel):
    """Metadata for API endpoint documentation"""
    endpoint: str = Field(description="Endpoint path")
    method: str = Field(description="HTTP method")
    summary: str = Field(description="Endpoint summary")
    description: Optional[str] = Field(default=None, description="Detailed description")
    tags: List[str] = Field(default_factory=list, description="Endpoint tags")
    examples: List[DocumentationExample] = Field(default_factory=list, description="Usage examples")
    rate_limit: Optional[str] = Field(default=None, description="Rate limit information")
    authentication: Optional[str] = Field(default=None, description="Authentication requirements")
    response_codes: Dict[int, str] = Field(default_factory=dict, description="Response code descriptions")
    deprecated: bool = Field(default=False, description="Whether endpoint is deprecated")
    deprecation_message: Optional[str] = Field(default=None, description="Deprecation message if deprecated")


class DocumentationBuilder:
    """
    Builder for enhanced API documentation.
    
    Provides utilities for creating comprehensive API documentation
    with examples, schemas, and metadata.
    """
    
    def __init__(self):
        """Initialize documentation builder."""
        self.endpoints: Dict[str, APIEndpointMetadata] = {}
    
    def add_endpoint(
        self,
        endpoint: str,
        method: str,
        summary: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        examples: Optional[List[DocumentationExample]] = None,
        rate_limit: Optional[str] = None,
        authentication: Optional[str] = None,
        response_codes: Optional[Dict[int, str]] = None,
        deprecated: bool = False,
        deprecation_message: Optional[str] = None
    ) -> APIEndpointMetadata:
        """
        Add endpoint documentation.
        
        Args:
            endpoint: Endpoint path
            method: HTTP method
            summary: Endpoint summary
            description: Detailed description
            tags: Endpoint tags
            examples: Usage examples
            rate_limit: Rate limit information
            authentication: Authentication requirements
            response_codes: Response code descriptions
            deprecated: Whether endpoint is deprecated
            deprecation_message: Deprecation message if deprecated
            
        Returns:
            APIEndpointMetadata object
        """
        key = f"{method.upper()}:{endpoint}"
        
        metadata = APIEndpointMetadata(
            endpoint=endpoint,
            method=method.upper(),
            summary=summary,
            description=description,
            tags=tags or [],
            examples=examples or [],
            rate_limit=rate_limit,
            authentication=authentication,
            response_codes=response_codes or {},
            deprecated=deprecated,
            deprecation_message=deprecation_message
        )
        
        self.endpoints[key] = metadata
        logger.info(f"Added documentation for endpoint: {key}")
        
        return metadata
    
    def add_example(
        self,
        endpoint: str,
        method: str,
        example: DocumentationExample
    ):
        """
        Add an example to an endpoint.
        
        Args:
            endpoint: Endpoint path
            method: HTTP method
            example: Example to add
        """
        key = f"{method.upper()}:{endpoint}"
        
        if key in self.endpoints:
            self.endpoints[key].examples.append(example)
            logger.info(f"Added example to endpoint: {key}")
        else:
            logger.warning(f"Endpoint {key} not found, cannot add example")
    
    def get_endpoint_documentation(
        self,
        endpoint: str,
        method: str
    ) -> Optional[APIEndpointMetadata]:
        """
        Get documentation for an endpoint.
        
        Args:
            endpoint: Endpoint path
            method: HTTP method
            
        Returns:
            APIEndpointMetadata if found, None otherwise
        """
        key = f"{method.upper()}:{endpoint}"
        return self.endpoints.get(key)
    
    def get_all_endpoints(self) -> List[APIEndpointMetadata]:
        """Get all endpoint documentation."""
        return list(self.endpoints.values())
    
    def get_endpoints_by_tag(self, tag: str) -> List[APIEndpointMetadata]:
        """
        Get endpoints by tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of endpoints with the specified tag
        """
        return [
            endpoint for endpoint in self.endpoints.values()
            if tag in endpoint.tags
        ]
    
    def generate_openapi_extension(self) -> Dict[str, Any]:
        """
        Generate OpenAPI extension with custom documentation.
        
        Returns:
            Dictionary with OpenAPI extension data
        """
        extensions = {
            "x-custom-documentation": {
                "endpoints": {}
            }
        }
        
        for key, metadata in self.endpoints.items():
            extensions["x-custom-documentation"]["endpoints"][key] = {
                "summary": metadata.summary,
                "description": metadata.description,
                "tags": metadata.tags,
                "rate_limit": metadata.rate_limit,
                "authentication": metadata.authentication,
                "examples": [
                    {
                        "name": example.name,
                        "description": example.description,
                        "request": example.request,
                        "response": example.response
                    }
                    for example in metadata.examples
                ]
            }
        
        return extensions


def create_example(
    name: str,
    request: Dict[str, Any],
    response: Dict[str, Any],
    description: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> DocumentationExample:
    """
    Create a documentation example.
    
    Args:
        name: Example name
        request: Example request payload
        response: Example response
        description: Example description
        headers: Example headers
        
    Returns:
        DocumentationExample object
    """
    return DocumentationExample(
        name=name,
        description=description,
        request=request,
        response=response,
        headers=headers
    )


def enhance_openapi_schema(
    openapi_schema: Dict[str, Any],
    documentation_builder: DocumentationBuilder
) -> Dict[str, Any]:
    """
    Enhance OpenAPI schema with custom documentation.
    
    Args:
        openapi_schema: Original OpenAPI schema
        documentation_builder: Documentation builder with custom docs
        
    Returns:
        Enhanced OpenAPI schema
    """
    # Add custom documentation extension
    custom_docs = documentation_builder.generate_openapi_extension()
    openapi_schema.update(custom_docs)
    
    # Add enhanced descriptions to paths
    for key, metadata in documentation_builder.endpoints.items():
        method, path = key.split(":")
        
        if path in openapi_schema.get("paths", {}):
            path_obj = openapi_schema["paths"][path]
            
            if method.lower() in path_obj:
                operation = path_obj[method.lower()]
                
                # Update description if not set
                if metadata.description and not operation.get("description"):
                    operation["description"] = metadata.description
                
                # Add custom fields
                operation["x-rate-limit"] = metadata.rate_limit
                operation["x-authentication"] = metadata.authentication
                
                # Add examples
                if metadata.examples:
                    operation["x-examples"] = [
                        {
                            "name": example.name,
                            "description": example.description,
                            "request": example.request,
                            "response": example.response
                        }
                        for example in metadata.examples
                    ]
    
    return openapi_schema
