import time
import json
import uuid
from datetime import datetime

from services import services
from app.startup import elastic_handler, kafka_producer, redis_handler
from queries.queries import QueryTypes
from app.config import (
    TELEGRAM_INDEX_MESSAGES as INDEX_MESSAGES,
    TELEGRAM_UPDATE_MESSAGE as UPDATE_MESSAGE,
    TELEGRAM_UPDATE_ACK_TOPIC as UPDATE_ACK_TOPIC,
)

import logging
logger = logging.getLogger(__name__)


async def create_update_job(
    search_text: str, 
    start_date: str, 
    end_date: str,
):
    """Create a new update job and return job ID immediately"""
    job_id = str(uuid.uuid4())
    
    # Initialize job status in Redis
    job_data = {
        "job_id": job_id,
        "status": "pending",
        "search_text": search_text,
        "start_date": start_date,
        "end_date": end_date,
        "created_at": datetime.now().isoformat(),
        "total_peers": 0,
        "pending_peer_ids": [],  # List of peer_ids waiting for completion
        "completed_peer_ids": [],  # List of completed peer_ids
        "failed_peer_ids": [],  # List of failed peer_ids
        "message": "Job created, starting search..."
    }
    
    # Store job data in Redis with 24 hour expiration
    redis_handler.set(f"update_telegram_posts_job:{job_id}", json.dumps(job_data))
    
    # Start the actual update process asynchronously
    import asyncio
    asyncio.create_task(update_posts_async(job_id, search_text, start_date, end_date))
    
    # Start Kafka listener for acknowledgments if not already running
    asyncio.create_task(setup_ack_listener())
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Update job created successfully"
    }


async def update_posts_async(
    job_id: str,
    search_text: str, 
    start_date: str, 
    end_date: str,
):
    timestamp = int(time.time()) - 2 * 60 * 60 # 2 hours ago
    template = services.jinja_template_generator(path=QueryTypes.TelegramUpdatePosts)

    payload = json.loads(template.render(
        search_text=search_text,
        start_date=start_date,
        end_date=end_date,
        timestamp=timestamp,
        size=100,
    ))
    logger.info(f"Payload: {json.dumps(payload, indent=4, ensure_ascii=False)}")

    results = []
    response = await elastic_handler.client.search(index=INDEX_MESSAGES, body=payload, scroll="2m")
    scroll_id = response.get("_scroll_id")
    results.extend([message["_source"] for message in response.get("hits", {}).get("hits", [])])
    while len(response.get("hits", {}).get("hits", {})) != 0:
        response = await elastic_handler.client.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = response.get("_scroll_id")
        results.extend([message["_source"] for message in response.get("hits", {}).get("hits", [])])
        logger.info(f'Results: {len(response.get("hits", {}).get("hits", []))}')

    logger.info(f"Results: {len(results)}")
    
    # Update job status - searching completed
    await update_job_status(job_id, "processing", f"Found {len(results)} messages, grouping by peers...")
    
    # Group results by PEER_ID
    grouped_results = {}
    for result in results:
        peer_id = result.get("PEER_ID")
        message_id = result.get("MESSAGE_ID")
        
        if peer_id not in grouped_results:
            grouped_results[peer_id] = []
        
        grouped_results[peer_id].append(message_id)
    
    # Convert to the desired format
    formatted_results = []
    for peer_id, message_ids in grouped_results.items():
        formatted_results.append({
            "peer_id": peer_id,
            "message_ids": message_ids
        })
    
    logger.info(f"Grouped results: {len(formatted_results)} peers")
    
    # Extract peer IDs and update job status
    peer_ids = [item["peer_id"] for item in formatted_results]
    await update_job_status(job_id, "processing", f"Processing {len(formatted_results)} peers...", 
                           total_peers=len(formatted_results), pending_peer_ids=peer_ids)

    # Process each peer's message_ids with batching to prevent flooding on telegram side
    for item in formatted_results:
        peer_id = item["peer_id"]
        message_ids = item["message_ids"]

        try:
            if len(message_ids) > 0:
                # Split large message_ids into batches of 100 to prevent flooding on telegram side
                batch_size = 100
                for i in range(0, len(message_ids), batch_size):
                    batch = message_ids[i:i + batch_size]
                    # Include job_id in the message so Telegram clients can acknowledge back
                    message_payload = {
                        "message_ids": batch,
                        "job_id": job_id,
                        "peer_id": peer_id
                    }
                    await kafka_producer.produce(
                        topic=UPDATE_MESSAGE,
                        value=message_payload,
                        key=str(peer_id)
                    )
                    logger.info(f"Sent batch {i//batch_size + 1} for peer {peer_id}: {len(batch)} messages")
                
                logger.info(f"Sent update request for peer {peer_id} with {len(message_ids)} messages")

        except Exception as e:
            logger.error(f"Error processing peer {peer_id}: {e}")
            # Mark this peer as failed immediately
            await mark_peer_completed(job_id, peer_id, "failed", str(e))

    # Mark job as "processing" - waiting for Telegram clients to complete
    await update_job_status(job_id, "processing", 
                           f"Sent update requests for {len(formatted_results)} peers. Waiting for Telegram clients to complete...")

    return formatted_results


async def update_job_status(job_id: str, status: str, message: str, 
                           total_peers: int = None, pending_peer_ids: list = None, 
                           completed_peer_ids: list = None, failed_peer_ids: list = None):
    """Update job status in Redis"""
    try:
        job_data = redis_handler.get(f"update_telegram_posts_job:{job_id}")
        if job_data:
            job_data["status"] = status
            job_data["message"] = message
            job_data["updated_at"] = datetime.now().isoformat()
            
            if total_peers is not None:
                job_data["total_peers"] = total_peers
            if pending_peer_ids is not None:
                job_data["pending_peer_ids"] = pending_peer_ids
            if completed_peer_ids is not None:
                job_data["completed_peer_ids"] = completed_peer_ids
            if failed_peer_ids is not None:
                job_data["failed_peer_ids"] = failed_peer_ids
                
            redis_handler.set(f"update_telegram_posts_job:{job_id}", json.dumps(job_data))
    except Exception as e:
        logger.error(f"Error updating job status: {e}")


async def mark_peer_completed(job_id: str, peer_id: int, status: str, error_message: str = None):
    """Mark a specific peer as completed or failed"""
    try:
        job_data = redis_handler.get(f"update_telegram_posts_job:{job_id}")
        if not job_data:
            logger.error(f"Job {job_id} not found when marking peer {peer_id} as {status}")
            return
        
        # Remove from pending list
        if peer_id in job_data.get("pending_peer_ids", []):
            job_data["pending_peer_ids"].remove(peer_id)
        
        # Add to appropriate completion list
        if status == "completed":
            if peer_id not in job_data.get("completed_peer_ids", []):
                job_data["completed_peer_ids"].append(peer_id)
        elif status == "failed":
            if peer_id not in job_data.get("failed_peer_ids", []):
                job_data["failed_peer_ids"].append(peer_id)
        
        # Check if job is complete
        total_peers = job_data.get("total_peers", 0)
        completed_peers = len(job_data.get("completed_peer_ids", []))
        failed_peers = len(job_data.get("failed_peer_ids", []))
        completed_total = completed_peers + failed_peers
        
        if completed_total >= total_peers and total_peers > 0:
            job_data["status"] = "completed"
            job_data["message"] = f"Job completed! {completed_peers} peers succeeded, {failed_peers} failed."
        else:
            remaining = total_peers - completed_total
            job_data["message"] = f"Processing... {completed_total}/{total_peers} peers completed ({remaining} remaining)"
        
        job_data["updated_at"] = datetime.now().isoformat()
        redis_handler.set(f"update_telegram_posts_job:{job_id}", json.dumps(job_data))
        
        logger.info(f"Peer {peer_id} marked as {status} for job {job_id}. Progress: {completed_total}/{total_peers}")
        
    except Exception as e:
        logger.error(f"Error marking peer {peer_id} as {status} for job {job_id}: {e}")


async def handle_telegram_ack(message_data: dict):
    """Handle acknowledgment from Telegram clients"""
    logger.info(f"Handling Telegram acknowledgment: {message_data}")
    try:
        job_id = message_data.get("job_id")
        peer_id = message_data.get("peer_id")
        status = message_data.get("status")  # "completed" or "failed"
        error_message = message_data.get("error_message")
        
        if not all([job_id, peer_id, status]):
            logger.error(f"Invalid acknowledgment message: {message_data}")
            return
            
        await mark_peer_completed(job_id, peer_id, status, error_message)
        
    except Exception as e:
        logger.error(f"Error handling Telegram acknowledgment: {e}")


async def get_job_status(job_id: str):
    """Get job status from Redis"""
    try:
        job_data = redis_handler.get(f"update_telegram_posts_job:{job_id}")
        if job_data:
            # Calculate counts dynamically from the lists
            completed_peers = len(job_data.get("completed_peer_ids", []))
            failed_peers = len(job_data.get("failed_peer_ids", []))
            pending_peers = len(job_data.get("pending_peer_ids", []))
            
            # Add calculated counts to the response
            job_data["completed_peers"] = completed_peers
            job_data["failed_peers"] = failed_peers
            job_data["pending_peers"] = pending_peers
            
            return job_data
        else:
            return {"error": "Job not found"}
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return {"error": "Failed to get job status"}


# Global flag to track if listener is running
_ack_listener_running = False

async def setup_ack_listener():
    """Setup Kafka listener for acknowledgments (similar to factory.py)"""
    global _ack_listener_running
    
    if _ack_listener_running:
        return
    
    _ack_listener_running = True
    
    try:
        from utils.kafka_handler import KafkaHandler
        
        kafka_handler = KafkaHandler()
        
        # Register callback function
        kafka_handler.add_listener(UPDATE_ACK_TOPIC, handle_ack_message)
        
        # Start listening
        await kafka_handler.start_listener(
            topics=[UPDATE_ACK_TOPIC],
            group_id="report_service_ack_listener"
        )
        
        logger.info("Kafka acknowledgment listener started in report service")
        
    except Exception as e:
        logger.error(f"Failed to start acknowledgment listener: {e}")
        _ack_listener_running = False


async def handle_ack_message(message):
    """Handle acknowledgment message from Kafka (similar to handle_update_message in factory.py)"""
    try:
        message_data = message.value
        await handle_telegram_ack(message_data)
    except Exception as e:
        logger.error(f"Error handling acknowledgment message: {e}")
