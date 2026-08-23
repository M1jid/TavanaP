"""
Monitoring Dashboard API for Telegram data collection
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

from app.startup import elastic_handler
from .monitoring_queries import (
    ACCOUNT_STATUS_QUERY,
    CHANNEL_COLLECTION_STATS,
    ERROR_ANALYSIS_QUERY,
    PERFORMANCE_METRICS,
    REAL_TIME_ACTIVITY,
    ACCOUNT_HEALTH_CHECK,
    MESSAGE_COLLECTION_TRENDS,
    RETRY_ANALYSIS
)

router = APIRouter(prefix="/monitoring", tags=["Telegram Monitoring"])

@router.get("/dashboard/overview")
async def get_dashboard_overview():
    """Get overall system health overview"""
    try:
        # Account status
        account_response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=ACCOUNT_STATUS_QUERY
        )
        
        # Error analysis
        error_response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=ERROR_ANALYSIS_QUERY
        )
        
        # Performance metrics
        performance_response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=PERFORMANCE_METRICS
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "accounts": account_response.get("aggregations", {}).get("accounts", {}).get("buckets", []),
            "errors": error_response.get("aggregations", {}),
            "performance": performance_response.get("aggregations", {}),
            "status": "healthy"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")

@router.get("/accounts/status")
async def get_accounts_status():
    """Get status of all accounts"""
    try:
        response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=ACCOUNT_STATUS_QUERY
        )
        
        accounts = []
        for bucket in response.get("aggregations", {}).get("accounts", {}).get("buckets", []):
            account_id = bucket["key"]
            latest_status = bucket.get("latest_status", {}).get("hits", {}).get("hits", [])
            
            if latest_status:
                latest = latest_status[0]["_source"]
                accounts.append({
                    "account_id": account_id,
                    "status": latest.get("status"),
                    "operation": latest.get("operation"),
                    "message": latest.get("message"),
                    "timestamp": latest.get("timestamp"),
                    "status_counts": bucket.get("status_counts", {}).get("buckets", []),
                    "operation_counts": bucket.get("operation_counts", {}).get("buckets", [])
                })
        
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get accounts status: {str(e)}")

@router.get("/channels/stats")
async def get_channels_stats():
    """Get channel collection statistics"""
    try:
        response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=CHANNEL_COLLECTION_STATS
        )
        
        channels = []
        for bucket in response.get("aggregations", {}).get("channels", {}).get("buckets", []):
            channels.append({
                "channel_username": bucket["key"],
                "total_messages": bucket.get("total_messages", {}).get("value", 0),
                "collection_events": bucket.get("collection_events", {}).get("value", 0),
                "latest_collection": bucket.get("latest_collection", {}).get("value_as_string")
            })
        
        return {"channels": channels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get channels stats: {str(e)}")

@router.get("/errors/analysis")
async def get_error_analysis():
    """Get error analysis"""
    try:
        response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=ERROR_ANALYSIS_QUERY
        )
        
        return {
            "error_types": response.get("aggregations", {}).get("error_types", {}).get("buckets", []),
            "error_by_account": response.get("aggregations", {}).get("error_by_account", {}).get("buckets", []),
            "error_timeline": response.get("aggregations", {}).get("error_timeline", {}).get("buckets", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get error analysis: {str(e)}")

@router.get("/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics"""
    try:
        response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=PERFORMANCE_METRICS
        )
        
        return response.get("aggregations", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/activity/realtime")
async def get_realtime_activity():
    """Get real-time activity (last hour)"""
    try:
        response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=REAL_TIME_ACTIVITY
        )
        
        activities = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit["_source"]
            activities.append({
                "timestamp": source.get("timestamp"),
                "account_id": source.get("account_id"),
                "operation": source.get("operation"),
                "status": source.get("status"),
                "message": source.get("message"),
                "channel_username": source.get("channel_username"),
                "message_count": source.get("message_count")
            })
        
        return {"activities": activities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get realtime activity: {str(e)}")

@router.get("/health/accounts")
async def get_accounts_health():
    """Get account health status"""
    try:
        response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=ACCOUNT_HEALTH_CHECK
        )
        
        accounts = []
        for bucket in response.get("aggregations", {}).get("accounts", {}).get("buckets", []):
            account_id = bucket["key"]
            last_activity = bucket.get("last_activity", {}).get("value_as_string")
            success_rate = bucket.get("success_rate", {})
            operations_count = bucket.get("operations_count", {}).get("value", 0)
            
            # Calculate success rate
            success_count = success_rate.get("buckets", {}).get("success", {}).get("doc_count", 0)
            failed_count = success_rate.get("buckets", {}).get("failed", {}).get("doc_count", 0)
            total_count = success_count + failed_count
            success_percentage = (success_count / total_count * 100) if total_count > 0 else 0
            
            accounts.append({
                "account_id": account_id,
                "last_activity": last_activity,
                "success_rate": round(success_percentage, 2),
                "operations_count": operations_count,
                "success_count": success_count,
                "failed_count": failed_count
            })
        
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get accounts health: {str(e)}")

@router.get("/trends/messages")
async def get_message_trends():
    """Get message collection trends"""
    try:
        response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=MESSAGE_COLLECTION_TRENDS
        )
        
        trends = []
        for bucket in response.get("aggregations", {}).get("hourly_collection", {}).get("buckets", []):
            trends.append({
                "timestamp": bucket["key_as_string"],
                "total_messages": bucket.get("total_messages", {}).get("value", 0),
                "unique_channels": bucket.get("unique_channels", {}).get("value", 0)
            })
        
        return {"trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get message trends: {str(e)}")

@router.get("/retry/analysis")
async def get_retry_analysis():
    """Get retry analysis"""
    try:
        response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=RETRY_ANALYSIS
        )
        
        return response.get("aggregations", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get retry analysis: {str(e)}")

@router.get("/alerts")
async def get_alerts():
    """Get system alerts based on monitoring data"""
    try:
        # Get accounts with no activity in last 30 minutes
        no_activity_query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"timestamp": {"gte": "now-30m"}}}
                    ]
                }
            },
            "size": 0,
            "aggs": {
                "active_accounts": {
                    "cardinality": {
                        "field": "account_id.keyword"
                    }
                }
            }
        }
        
        response = await elastic_handler.client.search(
            index="telegram-monitoring",
            body=no_activity_query
        )
        
        active_accounts = response.get("aggregations", {}).get("active_accounts", {}).get("value", 0)
        
        alerts = []
        
        if active_accounts == 0:
            alerts.append({
                "level": "critical",
                "message": "No accounts have been active in the last 30 minutes",
                "timestamp": datetime.now().isoformat()
            })
        elif active_accounts < 3:  # Assuming you have 5 accounts
            alerts.append({
                "level": "warning",
                "message": f"Only {active_accounts} accounts are active",
                "timestamp": datetime.now().isoformat()
            })
        
        return {"alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")
