# Prompt version and rollback evidence

Prompt name: `day13-chat` (Langfuse text prompt)

The same input was used for all four requests:
`Summarize the observability workflow for an AI API.`

| Scenario | Trace ID | Correlation ID | Label | Version | Source |
|---|---|---|---|---:|---|
| baseline | `feb051272112cf4e7a34c672936e6593` | `req-827c4af0` | `baseline` | 1 | `langfuse` |
| candidate | `29c8dc49dc7ec3f5d85ddac42b004958` | `req-e5be504f` | `candidate` | 2 | `langfuse` |
| promoted production | `92d76bf113a7d36eec717b64d2b68e25` | `req-ad7ea2cf` | `production` | 2 | `langfuse` |
| production rollback | `ce69d0d3a0e440a426b5443753683eb7` | `req-57861656` | `production` | 1 | `langfuse` |

Final label state was verified read-only:

- version 1: `baseline`, `production`
- version 2: `candidate`, `latest`

This leaves production safely rolled back to version 1.
