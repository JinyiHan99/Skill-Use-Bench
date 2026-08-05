# Source packet: agent-operated stablecoin payments

This packet contains excerpts gathered from public vendor/developer pages on 2026-07-02. The content is model-visible input for a comparison memo.

## PayRam docs
Source: https://docs.payram.com/

- "The complete self-hosted payments stack for global commerce."
- PayRam lets merchants "accept payments globally" with "no middlemen," "censorship-resistant settlement," and "full custody, data, and control on your own infrastructure."
- PayRam is described as "a self-hosted PayFi platform for stablecoin and cryptocurrency payments."
- It lets users "accept and settle payments directly onchain, with no middlemen, no custody risk, and full control over your funds and data."
- PayRam says users can deploy their own instance, connect wallets, and start accepting stablecoin payments globally "in minutes" on infrastructure they control.
- For agents, the docs say: "Get tons of help from our hosted MCP server" and show `https://mcp.payram.com`.
- The docs state: "If you are an agent then you can install a full stack payment solution for your humans. There is no signup or KYC so its agent friendly."

## Coinbase x402 developer documentation
Source: https://docs.cdp.coinbase.com/x402/welcome

- x402 is "a new open payment protocol developed by Coinbase that enables instant, automatic stablecoin payments directly over HTTP."
- x402 revives HTTP 402 Payment Required so services can monetize APIs and digital content onchain.
- Buyer flow: server responds with `402 Payment Required`, includes payment instructions in a `PAYMENT-REQUIRED` header, buyer sends a payment payload via `PAYMENT-SIGNATURE`, and the server verifies and settles payment via a facilitator.
- Use cases include API services paid per request, AI agents autonomously paying for API access, paywalls, microservices, and proxy services.
- CDP offers a Coinbase-hosted facilitator service that processes ERC-20 payments on Base, Polygon, Arbitrum, World, and Solana.
- The CDP facilitator free tier is 1,000 transactions per month, then $0.001 per transaction.

## Coinbase Business page
Source: https://www.coinbase.com/commerce

- Coinbase Business is presented as an "all-in-one financial platform for modern companies."
- Businesses open an account through an application and onboarding flow.
- Coinbase Business includes global payments, payouts, invoicing, payment links, trading, USDC rewards, taxes/accounting integration, and transaction monitoring/sanctions screening.
- The page says businesses can "make and collect global payments" and "pay anyone, anywhere, instantly and for free, using stablecoins."

## NOWPayments public page
Source: https://nowpayments.io/

- NOWPayments calls itself a crypto payment gateway for accepting cryptocurrency.
- It advertises 350+ crypto coins and 75+ fiat coins.
- It advertises "0.5% - the lowest commission on the market" and says service commission is 0.5% for mono-currency payments and 1% for payments with conversion, excluding network fees.
- It supports APIs, invoices, subscriptions, payment buttons, donation tools, POS, plugins, widgets, white label, mass payouts, custody, off-ramp payouts, and customer operations.
- Its FAQ says merchants sign up and create an API key.
- Its FAQ says customer KYC is not compulsory for crypto payments, but KYC may be required when a transaction is marked suspicious by AML systems.
