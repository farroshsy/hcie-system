"""
Batch Operations Utilities

Provides support for batch processing of API operations to reduce overhead
and improve performance for bulk operations.
"""

from typing import Generic, TypeVar, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BatchOperationStatus(str, Enum):
    """Status of batch operations"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"


class BatchOperationResult(BaseModel, Generic[T]):
    """Result of a single operation within a batch"""
    index: int = Field(description="Index in the original batch")
    success: bool = Field(description="Whether the operation succeeded")
    data: Optional[T] = Field(default=None, description="Result data if successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    operation_id: Optional[str] = Field(default=None, description="Unique identifier for this operation")


class BatchResponse(BaseModel, Generic[T]):
    """Response for batch operations"""
    batch_id: str = Field(description="Unique identifier for this batch")
    status: BatchOperationStatus = Field(description="Overall batch status")
    total_operations: int = Field(description="Total number of operations in batch")
    successful_operations: int = Field(description="Number of successful operations")
    failed_operations: int = Field(description="Number of failed operations")
    results: List[BatchOperationResult[T]] = Field(description="List of individual operation results")
    processing_time_ms: Optional[float] = Field(default=None, description="Total processing time in milliseconds")
    
    class Config:
        arbitrary_types_allowed = True


class BatchRequest(BaseModel, Generic[T]):
    """Request for batch operations"""
    operations: List[T] = Field(description="List of operations to perform")
    batch_id: Optional[str] = Field(default=None, description="Optional batch ID (will be generated if not provided)")
    continue_on_error: bool = Field(default=True, description="Continue processing even if some operations fail")
    
    class Config:
        arbitrary_types_allowed = True


async def execute_batch_operations(
    operations: List[Any],
    operation_handler,
    continue_on_error: bool = True,
    batch_id: Optional[str] = None
) -> BatchResponse:
    """
    Execute a batch of operations with error handling.
    
    Args:
        operations: List of operations to execute
        operation_handler: Async function to handle each operation
        continue_on_error: Whether to continue processing after errors
        batch_id: Optional batch ID (will be generated if not provided)
    
    Returns:
        BatchResponse with results and status
    """
    import time
    import uuid
    
    if batch_id is None:
        batch_id = str(uuid.uuid4())
    
    start_time = time.time()
    results = []
    successful_count = 0
    failed_count = 0
    
    for index, operation in enumerate(operations):
        try:
            # Execute the operation
            result_data = await operation_handler(operation)
            
            # Record success
            results.append(BatchOperationResult(
                index=index,
                success=True,
                data=result_data,
                operation_id=f"{batch_id}_{index}"
            ))
            successful_count += 1
            
        except Exception as e:
            # Record failure
            results.append(BatchOperationResult(
                index=index,
                success=False,
                error=str(e),
                operation_id=f"{batch_id}_{index}"
            ))
            failed_count += 1
            
            # Stop processing if continue_on_error is False
            if not continue_on_error:
                logger.error(f"Batch operation failed at index {index}, stopping processing")
                break
    
    # Determine overall status
    total_operations = len(operations)
    if failed_count == 0:
        status = BatchOperationStatus.COMPLETED
    elif successful_count == 0:
        status = BatchOperationStatus.FAILED
    else:
        status = BatchOperationStatus.PARTIALLY_COMPLETED
    
    processing_time_ms = (time.time() - start_time) * 1000
    
    return BatchResponse(
        batch_id=batch_id,
        status=status,
        total_operations=total_operations,
        successful_operations=successful_count,
        failed_operations=failed_count,
        results=results,
        processing_time_ms=processing_time_ms
    )


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


async def execute_chunked_operations(
    items: List[Any],
    operation_handler,
    chunk_size: int = 100,
    continue_on_error: bool = True
) -> List[BatchResponse]:
    """
    Execute operations in chunks to handle large batches efficiently.
    
    Args:
        items: List of items to process
        operation_handler: Async function to handle each operation
        chunk_size: Size of each chunk
        continue_on_error: Whether to continue processing after errors
    
    Returns:
        List of BatchResponse objects (one per chunk)
    """
    chunks = chunk_list(items, chunk_size)
    batch_responses = []
    
    for chunk_index, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {chunk_index + 1}/{len(chunks)} with {len(chunk)} items")
        
        batch_response = await execute_batch_operations(
            operations=chunk,
            operation_handler=operation_handler,
            continue_on_error=continue_on_error,
            batch_id=f"chunk_{chunk_index}"
        )
        
        batch_responses.append(batch_response)
    
    return batch_responses
