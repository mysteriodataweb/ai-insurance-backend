# AI Insurance Platform — LinkedIn Project Description

## Option 1 (Short)

Built an AI-powered insurance claims platform that automates claim intake, triage, and risk analysis. Used LLMs for structured data extraction, built a rule-based risk scoring engine with explainable signals, and implemented human-in-the-loop workflows for high-risk decisions. Stack: Next.js, FastAPI, PostgreSQL, Groq LLM.

## Option 2 (Detailed)

Designed and built an AI Insurance Operations Platform that demonstrates how AI can transform insurance claims processing.

Key features:
• AI Claims Agent — Extracts structured information from unstructured claim descriptions using an LLM (Groq), with validated JSON output, deterministic missing-field checks and targeted follow-up questions
• Risk Scoring Engine — Rule-based system evaluating claims across 7 signal categories (amount tiers, amount mismatch, missing fields, AI confidence, reporting delay, repeat claimants) with human-readable explanations
• Operations Dashboard — Real-time claim queue with filters, KPIs, and claim detail views for operations teams
• Human-in-the-Loop — Enforced review workflow; high-risk claims need escalation and a second reviewer (four-eyes rule)
• Audit Trail — Complete logging of all actions for compliance and governance

Impact: claims are triaged automatically on submission; missing information is detected instantly and every decision is traceable.

Stack: Next.js, TypeScript, Tailwind CSS, Python, FastAPI, PostgreSQL, Groq LLM API, SQLAlchemy, pytest
