"""Hosted App 進入點:uvicorn main:app"""
from bridge.app import create_app

app = create_app()
