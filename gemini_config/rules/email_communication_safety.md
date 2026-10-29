# Email Communication Safety Guardrail

When using any email-related MCP tool (such as `email-sender-mcp` or `google-workspace` Gmail tools), you MUST strictly adhere to the following routing constraints:

1. **Internal Emails (Pre-approved):** You are fully authorized to autonomously send emails directly to the user's primary email address (configured as `USER_EMAIL` in `~/Agents/Agent 0/.env`). This is pre-approved for tasks like daily summaries, alerts, or test messages.
2. **External Emails (Blocked):** You MUST NEVER send an email to any external recipient (anyone other than the user) without obtaining explicit, human-in-the-loop confirmation first. You may draft the email or prepare it, but you must STOP and ask the user for permission before executing the send action.
