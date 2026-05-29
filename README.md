# Prozorro Tender Bot

Telegram bot for monitoring new procurements on prozorro.gov.ua.

## Features

- Checking for new tenders via cron job
- Sending notifications with procurement details and attached documents
- Manual check using the `/check` command
- State management via Upstash Redis (serverless-friendly)

## Installation (Local)

1. Clone the repository
2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Copy `.env.example` to `.env` and fill in the required values:

    - `BOT_TOKEN` — your Telegram bot token
    - `CHAT_ID` — chat ID for notifications
    - `MESSAGE_THREAD_ID` — chat topic/thread ID for notifications
    - `CRON_SECRET` — a custom secret to protect the cron endpoint
    - `UPSTASH_REDIS_REST_URL` + `UPSTASH_REDIS_REST_TOKEN` — obtained from dashboard.upstash.com
    - `BUYER_ID` — EDRPOU (tax ID) of the procuring entity
    - `MODE=polling`

4. Run the bot:

    ```bash
    python run_polling.py
    ```

## Deployment to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Set up all environment variables in your Vercel project (Settings → Environment Variables):
   - The same variables as in `.env.example`, plus `WEBHOOK_URL=https://your-app.vercel.app`, `WEBHOOK_SECRET=some_random_secret_string` (optional), and `WEBHOOK_MANAGE_TOKEN=your_admin_secret_string` (optional)
   - `MODE=webhook`
3. Deploy: `vercel --prod`

### Webhook Management

Since this application runs in a serverless ecosystem, the webhook is **not** configured automatically during application startup. You must manually trigger the registration after a deployment or when environment variables change.

Both administrative routes require an `Authorization` header utilizing your `WEBHOOK_MANAGE_TOKEN`.

**To Setup the Webhook:**

```bash
curl -X POST https://your-app.vercel.app/webhook/setup \
  -H "Authorization: Bearer your_webhook_manage_token"
```

**To Delete the Webhook:**

```bash
curl -X POST https://your-app.vercel.app/webhook/delete \
  -H "Authorization: Bearer your_webhook_manage_token"
```

### Securing the Cron Endpoint

Cron triggers a `GET /cron/check-tenders` request. For authorization, the following header is required: `Authorization: Bearer <CRON_SECRET>`.

To trigger it manually:

```bash
curl -X GET https://your-app.vercel.app/cron/check-tenders \
  -H "Authorization: Bearer your_cron_secret"
```

For production you can setup cron job via [cron-job.org](https://cron-job.org).

## Bot Commands

| Command | Description |
| --- | --- |
| `/start` | Welcome message and list of commands |
| `/check` | Check for new procurements immediately |
| `/status` | View the last processed tender |

## Notes

- The bot only stores the ID of the last processed tender (not the entire database).
- On the first run, it processes no more than the 5 most recent tenders.
- Document files are downloaded into RAM and immediately forwarded to Telegram.
- For Vercel deployment, consider increasing the function timeout, as 10 seconds might not be enough.
- Ensure that "Vercel Authentication" is disabled in the Deployment Protection settings.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENCE) file for details.
