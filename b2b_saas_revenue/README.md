# B2B SaaS Revenue and Retention - Your Business Dashboard

## What this is
Your private business analytics dashboard. It shows you what is happening in your business, helps you decide what to do about it, and tracks whether you are on target - all in one place.

## Your 3 sections
**UNDERSTAND** - See your key numbers, charts and any unusual patterns
**DECIDE** - Read insights and recommendations written in plain English
**MONITOR** - Track forecasts, set targets and get alerts automatically

## New here? Start with the User Manual tab
Click "User Manual" in the sidebar. It explains every section in plain English.

## Deployment Checklist
- [ ] npm install (run once - generates package-lock.json)
- [ ] wrangler.toml: name = "b2b_saas_revenue", main before [site], bucket = "./dist"
- [ ] npm run build -> check the dist/ folder was created
- [ ] npx wrangler deploy -> note the live URL
- [ ] npx wrangler secret put FORECAST_LOOKUP -> paste the single line from forecast_lookup.json (in this folder)
- [ ] Test: open the live URL -> dashboard loads with data
- [ ] Test: open the live URL/mcp -> MCP manifest appears

## How to run locally
1. npm install
2. npm run dev -> open http://localhost:5173
(The forecast lookup falls back to the local data file when the live service is not running.)

## How to deploy
1. npm run build
2. npx wrangler deploy
-> Live at your workers.dev address (shown after deploy)

## MCP Integration (for Claude)
Add your-live-url/mcp to Claude as an MCP connector. Claude can then read your live business data (read-only).

## How to update your dashboard
Run the pipeline: python main.py, then python export_for_frontend.py.
Then re-run: python generate_react_frontend.py, then npm run build and npx wrangler deploy.

## Support
Contact the team that delivered this dashboard.
