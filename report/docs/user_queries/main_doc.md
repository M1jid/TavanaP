# User Query API Documentation

## Overview
This API allows users to create, read, update, and delete their queries defined to connect to their channel. The API is divided into two main sections:
- User management endpoints (for administrators)
- Own query endpoints (for users to manage their own queries)

## Base URL
`https://yourdomain.com/api/v2/actions/query`

## Authentication
All endpoints require authentication. Include your JWT token in the Authorization header.