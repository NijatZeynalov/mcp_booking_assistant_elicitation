## Hotel Booking MCP Assistant with Elicitation

How to pair the Model Context Protocol with a local Llama 3  model to handle a hotel booking flow that explicitly relies on elicitation. The MCP server exposes a single `book_room` tool that understands dates and room classes. When the requested room is sold out (or details are missing), the server performs elicitation via `ctx.elicit()` to gather alternative instructions before returning either a `[SUCCESS]` or `[CANCELLED]` message.


### Requirements

- Python 3.10+
- `fastmcp` >= 0.2.0
- `pydantic` >= 2.0
- Local Ollama installation with the `llama3` family available

### LLM vs. Server Responsibilities

- LLM only handles the conversation: it interprets user intent and decides when/how to call the MCP tool, and it responds to elicitation prompts issued by the server.
- Server  holds the business rules: it validates payloads, reads `data/rooms.json`, determines success/cancellation, and crafts every message used during elicitation.
- Because of this split, the final booking outcome is deterministic and reproducible, while the user experience still feels natural thanks to the LLM-managed dialogue.

Install the Python dependencies in your environment:

```bash
pip install fastmcp pydantic
```

### Running the MCP Server

```bash
python server/main.py
```

By default FastMCP exposes an SSE endpoint at `http://localhost:8000/sse`. Point your Ollama configuration to this endpoint:

`~/.ollama/config.json`

```json
{
  "mcp": {
    "servers": [
      {
        "name": "hotel-booking",
        "type": "sse",
        "url": "http://localhost:8000/sse"
      }
    ]
  }
}
```

Restart `ollama serve` after editing the configuration, then run your preferred MCP-aware interface. Llama 3 will discover the `book_room` tool and call it whenever a booking action is needed.

### Elicitation Flow

1. User: "Book a deluxe room on 2025-12-31."
2. The Python server checks `data/rooms.json` and finds zero deluxe rooms for that date.
3. The server calls `ctx.elicit()` with the `BookingPreferences` schema to ask the LLM for another date or room type (or to confirm cancellation).
4. The LLM converses with the user and sends structured data back, e.g., "Try a standard room instead."
5. The server re-checks inventory and responds with deterministic text such as:

   ```
   [SUCCESS] Booked for 2025-12-31 (standard)
   ```

If the user declines to provide alternatives (`checkAlternative = False`), the server responds with:

```
[CANCELLED] No booking made
```


The script calls the booking logic directly and uses a local prompt/response handler to simulate `ctx.elicit()`. This is handy for validating the happy path and elicitation scenarios described in the test plan.

### Test Scenarios

| # | Input                                      | Expected Result                                                   |
|---|--------------------------------------------|-------------------------------------------------------------------|
| 1 | `Book a standard room on 2026-01-01`       | `[SUCCESS] Booked for 2026-01-01 (standard)`                      |
| 2 | `Book a deluxe room on 2025-12-31`         | Elicitation asking for another date or room type                  |
| 3 | User replies with `checkAlternative=false` | `[CANCELLED] No booking made`                                     |
| 4 | User provides alternative date/type        | `[SUCCESS] Booked for <new_date> (<new_type>)` if inventory exists |


