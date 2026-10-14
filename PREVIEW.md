# Online preview

This branch prepares the existing Django API and the companion Next.js web app for a short-lived Render demo. It calls the real OpenAI API; there are no canned answers.

## Deploy

1. Sign into Render with GitHub and allow access to both `sen-ol/aifred-backend` and `sen-ol/aifred-web`.
2. Create a Blueprint from this repository, select branch `codex/online-demo`, and use `render.yaml`.
3. Check that both web services and PostgreSQL use the **Free** plan. Free PostgreSQL expires after **30 days**. Export any needed data before then; this is not production storage.
4. Enter a newly issued OpenAI project key into the secret `OPENAI_API_KEY` field. Do not paste it into GitHub, the mobile app, or chat. Revoke any old key committed to source history.
5. Deploy, wait for both services to become healthy, then open the web service's HTTPS `onrender.com` address and choose **Sohbete Başla**.

No domain purchase is needed. Render can wake a sleeping service in about a minute. Both services share the workspace's monthly free instance hours. OpenAI usage is billed separately. With no payment method, exceeding Render's free bandwidth allowance suspends service instead of billing overages. Review the dashboard before confirming deployment.

## Behavior

- The initial `alfred` advisor is seeded if missing. Existing prompts are preserved.
- It is explicitly a preview: current hotel prices, availability and policies are not loaded or verified.
- Guests can chat without creating an account. Their last 20 messages are supplied from the current browser page, and are not saved to the database. Reloading clears guest history.
- Authenticated conversations are stored under their owner and advisor.
- Chat uses `gpt-6-luna` with reasoning `none`, a 1,200 output-token ceiling, a 4,000-character input limit, and a 25-second provider timeout. Model and reasoning are environment settings.
- The application sends no OpenAI storage request (`store=False`); provider retention policies still apply.
- DRF throttling is best-effort, per process. The web proxy's requests can share one IP quota. It is not an account-wide spending cap.
- No users or admin passwords are seeded. Login is available for accounts created separately; the main demo does not require login.
- Web chat passes through Next.js to the backend; API credentials stay server-side.
- Auto-deploy is off. Use Manual Deploy when updating these preview branches.

## Checks

GitHub Actions runs Django checks, regression tests with a mocked provider, and static-file collection. The web repository runs lint and a production build. These checks do not prove that the supplied API key has access to the selected model.

After deployment: open `/health/`, load the home page, send a Turkish hotel question, send a follow-up referring to the first answer, and confirm a provider error is displayed rather than leaving the send button disabled.

Sources: [Render free services](https://render.com/docs/free), [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
