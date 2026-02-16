"""
Configuration settings for the AI Mock Interview platform.
All model and voice settings are centralized here.

This uses Replit AI Integrations for OpenAI access - no API key required.
"""

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
# Using gpt-5-mini for cost effectiveness in interview scenarios
OPENAI_MODEL = "gpt-5-mini"

# Voice settings - using gpt-audio for TTS and STT
TTS_VOICE = "alloy"

TOTAL_QUESTIONS = 1

SENIORITY_LEVELS = ["Junior", "Mid", "Senior"]

DEMO_MODE = False
