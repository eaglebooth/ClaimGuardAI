# ClaimGuardAI Frontend Design Notes

Reference: https://saazai.framer.website/

Observed direction:

- Dark SaaS surface with high-contrast cream text.
- Lime/mint accent moments rather than a purple-dominant palette.
- Large compressed hero typography and rounded 8px glass panels.
- Soft radial light, subtle grid/noise texture, and animated highlight passes.
- Product UI appears in the first viewport instead of a pure marketing hero.

ClaimGuardAI adaptation:

- The first viewport is an operational claim cockpit: policy reserve, claim evidence, verdict, and payout controls.
- The earlier stats/marquee/score-path blocks were removed because they made the page feel like a thin landing page instead of an insurance workflow.
- The main call to action is now `Run claim demo`, and each workflow step has its own action button with demo-mode behavior before deployment.
- Visual language stays dark, glossy, and motion-rich, but content is specific to insurance claims and GenLayer consensus.
- The app avoids static mock positioning by wiring buttons to `genlayer-js`; demo fallback is only used before a contract address is configured.
