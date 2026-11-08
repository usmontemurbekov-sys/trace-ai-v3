# TRACE V3 — Arctic · Server-side research beta

TRACE V3 preserves the Arctic UI, pricing/rewards previews, text upload, report downloads, and Cloudflare Web Analytics. The AI-text classifier runs through a **Python FastAPI server** instead of downloading a large browser model.

## Real ML engine

- Trained model: `rasbt/ai-text-detector-logreg` (Apache-2.0 licensed, small TF-IDF + logistic regression classifier).
- Results are **experimental model scores, not probabilities of AI authorship**, and must never be used to discipline or accuse a student.
- No payment integration, real referrals, accounts, or scan-credit enforcement yet.
- This proof of concept does **not intentionally log/store submitted text**, but the hosting provider receives submitted text in transit and server logs and monitoring practices must be reviewed before inviting students to upload assignments.
- Model is sourced from a third party in joblib format. Joblib is executable Python serialization; review and pin a trusted revision before any production use.

## Easiest zero-dollar beta launch (Render)

1. Create a **new GitHub repository** and upload the contents of this folder (including `render.yaml`; exclude any virtualenv).
2. Visit https://dashboard.render.com and choose **New > Blueprint**, connect the GitHub repository and deploy `render.yaml`. Choose the **Free** plan; verify price is $0 before confirming.
   - Alternatively select **New > Web Service**, choose the repository, Python runtime and Free plan, build command `pip install -r requirements.txt && python download_model.py`, start command `uvicorn app:app --host 0.0.0.0 --port $PORT`.
3. Wait until the deployment becomes live. Render will give you a unique `https://<name>.onrender.com` URL.
4. Visit `https://<name>.onrender.com/api/health`. It should say `"model_ready":true`. If not, inspect build/server logs.
5. Visit that Render URL. The full Arctic TRACE V3 frontend is served together with the API. Paste 40+ words and click Analyze.
6. **To preserve your existing Cloudflare Workers URL:** change `const API_BASE = '';` near the bottom of `index.html` to `const API_BASE = 'https://<name>.onrender.com';`, and upload *only that updated HTML* to Cloudflare under your existing `trace-ai-detector` Worker. It will then call the Render API. (CORS is preconfigured for your Workers URL.)

Free Render services sleep after ~15 minutes without requests and can need about a minute to wake up; the first prediction after a cold start may therefore be slow. Free plan is for prototyping, not production. Costs can change; confirm current terms before deploying. Source: https://render.com/docs/free

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python download_model.py
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/api/health .

## Security + product caveats

Public beta endpoint is unauthenticated and has no user quotas or rate limits yet. Add abuse protection, privacy notices, service-side throttles, and audit-friendly monitoring **before** promoting to large audiences. Avoid user-supplied proprietary or student personal information. Keep the platform in research beta until independently benchmarked.
