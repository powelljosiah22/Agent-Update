# Email Communication Safety Guardrail

When using any email-related tool (such as the native `gmail` plugin/CLI or `email-sender-mcp`), you MUST strictly adhere to the following routing constraints:

1. **Internal Emails (Pre-approved):** You are fully authorized to autonomously send emails directly to the user (e.g., `user@example.com`). This is pre-approved for tasks like daily summaries, alerts, or test messages.
2. **External Emails (Blocked):** You MUST NEVER send an email to any external recipient (anyone other than the user) without obtaining explicit, human-in-the-loop confirmation first. You may draft the email or prepare it, but you must STOP and ask the user for permission before executing the send action.
