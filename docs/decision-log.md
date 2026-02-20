# Decision Log (MVP)

## Confirmed
- Timezone: `Asia/Seoul`
- Delivery: once daily at `08:00`
- Recipient model: single recipient in MVP
- Target collection: broad web search (no fixed domain list)
- Core keyword: `sh 공사 마곡 분양`
- Related content policy:
  - Expand with: `마곡, SH, 서울주택도시공사, 분양, 공급, 청약, 공고, 입주자모집`
  - Prioritize direct core-keyword matches
  - Relevance scoring with related-keyword hits
- Daily item limit: `Top 10`
- Duplicate policy: skip similar/identical items within `7 days`
- Summary style: detailed summary
- LLM summarizer: `OpenAI API`
- MVP runtime: local machine
- Failure alerting: backlog (not in MVP)

## Backlog
- Multi-recipient support
- Failure alerting channel
- Cloud migration

