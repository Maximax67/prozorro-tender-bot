# Prozorro Tender Bot

Telegram bot for monitoring new procurements on prozorro.gov.ua.

## Features

- Hourly checking for new tenders via Vercel Cron
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
   - The same variables as in `.env.example`, plus `WEBHOOK_URL=https://your-app.vercel.app` and `WEBHOOK_SECRET=some_random_secret_string`
   - `MODE=webhook`
3. Deploy: `vercel --prod`

### Securing the Cron Endpoint

Cron triggers a `GET /cron/check-tenders` request. For authorization, the following header is required: `Authorization: Bearer <CRON_SECRET>`.

To trigger it manually:

```bash
curl -X GET https://your-app.vercel.app/cron/check-tenders \
  -H "Authorization: Bearer your_cron_secret"
```

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
