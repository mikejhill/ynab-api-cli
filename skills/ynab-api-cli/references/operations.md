# Operation conventions

```text
ynab-api-cli discover transactions
ynab-api-cli inspect getTransactions
ynab-api-cli transactions get-transactions --plan-id UUID --since-date 2026-01-01
ynab-api-cli call getTransactions --request @request.json
```

The equivalent uniform request is:

```json
{"path":{"plan_id":"UUID"},"query":{"since_date":"2026-01-01"}}
```

- Amounts are integer milliunits: 12.34 currency units becomes 12340. Expenses are negative. Preserve the plan's currency.
- Dates follow the inspected ISO schema. Booleans use `true` or `false`; cleared status uses its declared enum.
- An omitted field differs from explicit null. Never replace unspecified fields with null during an update.
- Preserve server_knowledge and deleted records when intentionally processing delta responses. The CLI does not maintain synchronization state.
- Splits and transfers affect linked records. Inspect their models before editing them.
- Transaction creation accepts exactly one of `transaction` or `transactions`. Direct Import is a separate mutation from creating transactions with import_id.

Create an authorized expense using a body file:

```json
{"transaction":{"account_id":"ACCOUNT_UUID","date":"2026-01-01","amount":-12340,"category_id":"CATEGORY_UUID","memo":"Authorized expense","approved":false}}
```

```text
ynab-api-cli transactions create-transaction --plan-id PLAN_UUID --body @expense.json
ynab-api-cli transactions create-transaction --plan-id PLAN_UUID --body @expense.json --execute
```

The first command previews without contacting YNAB. The second submits once. Read the returned transaction ID using get-transaction-by-id to verify the result.

`--metadata` adds HTTP status, relevant headers, and contract version. Unknown parameters and invalid schemas fail before networking; properties allowed by the contract are retained. [Official API conventions](https://api.ynab.com/#data-formats).
