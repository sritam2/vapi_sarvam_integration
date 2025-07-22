# vapi_sarvam_integration
This repo is meant for all the development work needed in order to establish a proxy server between VAPI and sarvamAI because there needs to be a glue layer between vapi and sarvamAI

# Summary Report of Issues and Resolutions

## 1. Custom STT Transcript Aggregation and Turn-Taking

**Issue:**  
When integrating a custom STT with Vapi, only customer transcripts (`"channel": "customer"`) were being sent. As a result:

- Vapi aggregated all customer utterances together.
- Turn-taking was not segmented properly. Turn taking was NOT happening at all and VAPI was always giving accumulated transcripts to LLM 
because it thought that always customer is speaking and assistant turn never came up.
- Assistant (bot) messages and transcripts were not visible in the dashboard or logs, although the assistant's voice could be heard in audio playback.

**Resolution:**  
The issue was due to not emitting assistant transcripts (`"channel": "assistant"`).  
Vapi requires **both** customer and assistant transcripts to:

- Segment turns correctly.
- Show the full conversation in the dashboard and logs.

Once your custom STT integration started emitting assistant channel transcripts, turn-taking and transcript segmentation worked as expected.
VAPI properly understood when customer turn ended and when assistant turn started. As a result VAPI gave to LLM the last received transcript and not the entire accumulated transcript for processing, which is what we aimed for

---

## 2. Debouncing and Transcript Finalization

**Issue:**  
Clarification was requested on the concept of *debouncing* and on whether to send finalized or transient (interim) transcripts to Vapi.

**Resolution:**  
- **Debouncing** refers to waiting for a pause in speech before emitting a transcript, rather than sending fragmented mini-transcripts too frequently.
- Your STT server should handle interim transcripts internally.
- **Only finalized transcripts** should be sent to Vapi for optimal flow and accurate conversation tracking.

---

## 3. RAG and Tool Integration

**Issue:**  
You wanted to build a customer-care / sales conversational AI by integrating:

- Retrieval-Augmented Generation (RAG)
- External tools (e.g., CRM, email APIs)

**Resolution:**  
Vapi supports this through [custom tool calling](https://docs.vapi.ai/customization/tool-calling-integration), which enables:

- External data lookups and integrations
- Triggering APIs from conversations
- Intelligent workflow automation backed by your LLM

### 📚 References:

- 📘 [Custom LLM Tool Calling Integration](https://docs.vapi.ai/customization/tool-calling-integration)
- 📢 [Discord Thread: Is it possible to customize VAPI's RAG implementation?](https://discord.com/channels/1211482211119796234/1257668792037675029)

---

## 4. Community Videos

**Issue:**  
Inquiry about availability of community-created videos or tutorials.

**Resolution:**  
Currently, there are no officially documented video resources or community video tutorials mentioned in the Vapi documentation.

---
