import { dashboardUrl } from "../config.js";
import { media } from "../components/visuals/media.js";
import HeroSection from "../components/sections/HeroSection.jsx";
import PricingCards from "../components/sections/PricingCards.jsx";
import ComparisonTable from "../components/sections/ComparisonTable.jsx";
import FAQAccordion from "../components/sections/FAQAccordion.jsx";
import SplitFeature from "../components/sections/SplitFeature.jsx";
import TestimonialRow from "../components/sections/TestimonialRow.jsx";
import CTABand from "../components/sections/CTABand.jsx";

const plans = [
  { name: "Free", price: "$0", features: ["30 meeting-minutes / month", "2 deck uploads / month", "1 meeting at a time", "Full presenter experience"], cta: "Start free" },
  { name: "Team", price: "$99", period: "/mo", features: ["10 meeting-hours / month", "25 deck uploads / month", "3 meetings at a time", "Overage at $12 / hour", "Email support"], cta: "Get Team", plan: "team", featured: true },
  { name: "Business", price: "$399", period: "/mo", features: ["50 meeting-hours / month", "200 deck uploads / month", "10 meetings at a time", "Overage at $10 / hour", "Priority support"], cta: "Get Business", plan: "business" },
];

const compareRows = [
  { feature: "Meeting-hours / month", values: ["0.5", "10", "50"] },
  { feature: "Deck uploads / month", values: ["2", "25", "200"] },
  { feature: "Concurrent meetings", values: ["1", "3", "10"] },
  { feature: "Max length per meeting", values: ["20 min", "90 min", "3 hr"] },
  { feature: "Overage beyond allowance", values: ["—", "$12 / hr", "$10 / hr"] },
  { feature: "Agent prompt studio", values: ["✓", "✓", "✓"] },
  { feature: "Support", values: ["Community", "Email", "Priority"] },
];

const faq = [
  { q: "What exactly is metered?", a: "Meeting-minutes — the time the bot actually spends in a call, measured from when it joins to when it leaves. Launching a bot that never makes it into the meeting costs you nothing, and partial minutes round up to the next full minute." },
  { q: "What happens when I run out of minutes?", a: "On Team and Business, extra time simply bills at the overage rate shown above and your meetings keep running. On Free, launches pause until the next billing period or until you upgrade." },
  { q: "Why is there a maximum meeting length?", a: "Every plan auto-leaves at its ceiling so a forgotten bot can't sit in an empty call burning your allowance. The bot also leaves on its own when everyone else has left, when nobody joins, or after a long silence." },
  { q: "What counts as a deck upload?", a: "Each new PPTX or PDF you upload to your workspace counts as one upload, regardless of slide count. Re-indexing a deck you already uploaded is free." },
  { q: "Can I upgrade mid-month?", a: "Yes. Upgrade from the billing page and the new allowance applies immediately. Paddle prorates the charge." },
  { q: "Is there a contract or lock-in?", a: "No. Cancel anytime from the Paddle customer portal. Your workspace data remains until you delete it." },
];

export default function PricingPage() {
  return (
    <>
      <HeroSection
        badge="Pricing"
        title="Simple plans that grow with your demo volume"
        subtitle="Start free. Pay for the meeting time you actually use. No sales call required."
        primaryCta="Start free trial"
        primaryHref={`${dashboardUrl}/signup`}
        composition="ledger"
        compositionImages={[media.heroPricing]}
        imageAlt="Usage bars and plan pill"
      />

      <PricingCards plans={plans} />

      <ComparisonTable rows={compareRows} />

      <FAQAccordion title="Pricing questions" items={faq} />

      <SplitFeature
        eyebrow="Trust"
        title="Secure billing through Paddle"
        body="Payments are handled by Paddle, our merchant of record. Manage your subscription, invoices, and payment methods from the dashboard billing page. We never store card details on our servers."
        bullets={["Paddle Checkout for upgrades", "Customer portal for plan changes", "Meeting-minute meters reset monthly"]}
        tone="dark"
        reverse
      />

      <TestimonialRow
        title="Teams upgrading when demo volume picks up"
        items={[
          { quote: "We used the free allowance in week one. Team paid for itself on the first onboarding session we didn't have to staff.", name: "Sam T.", role: "Sales Ops, Series B", avatar: media.avatar4 },
          { quote: "Business tier covers our weekly customer walkthroughs without anyone watching the meter.", name: "Morgan L.", role: "CEO, Seed startup", avatar: media.avatar5 },
        ]}
      />

      <CTABand
        title="Start presenting for free today"
        subtitle="30 meeting-minutes and 2 uploads included — no credit card on signup."
        primaryLabel="Create free account"
        primaryHref={`${dashboardUrl}/signup`}
        secondaryLabel="See use cases"
        secondaryHref="/use-cases"
      />
    </>
  );
}
