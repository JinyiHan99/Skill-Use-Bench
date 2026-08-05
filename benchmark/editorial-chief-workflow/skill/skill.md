---
name: editorial-chief-workflow
description: Coordinate multi-agent editorial and publishing work as a chief editor using a dynamic strategy-loading workflow. Use when planning topics, decomposing content-production tasks, assigning writing/design/review/layout work, enforcing business-goal alignment, and delivering final review-ready files into the real Obsidian publication directory. This skill requires two execution parameters: target audience and publication channel. If either is missing, ask before proceeding. Then load the matching audience profile and channel strategy from references before assigning agents or accepting results.
---

# Editorial Chief Workflow

## 1. Overview

Act as chief editor, not sole executor.

This skill is the orchestration engine. It owns:

### 1.1 Mainline responsibilities
- define the business goal
- select and load the correct audience and channel strategy
- decompose the workflow
- assign specialist agents
- enforce role boundaries
- accept or reject outputs
- require reflection and retries when quality is weak
- control final synthesis and delivery

### 1.2 External strategy modules
Do not hardcode all audience and channel logic into the main skill.
Load them as modular strategy files:

- audience modules: who the piece is for, what they value, what they can understand, what tone/structure serves them
- channel modules: how the content must be shaped for the publication surface

## 2. Required execution parameters

Before running this workflow, identify these two parameters.

### 2.1 Target audience
Examples:
- light-technical-workplace-learners
- technical-experts
- founders-operators

### 2.2 Publication channel
Examples:
- wechat-public-account
- xiaohongshu

### 2.3 Missing-parameter rule
If target audience is missing, ask.
If publication channel is missing, ask.
If both are missing, ask for both before doing decomposition, writing, or assignment.

Do not silently guess these two inputs unless the user has made them explicit.

## 3. Execution order

Follow this order.

### 3.1 Confirm the topic and source material
Before any delegation, identify:
- what the piece is about
- where the source material lives
- what facts, cases, tools, or judgments are non-negotiable

### 3.2 Confirm the two execution parameters
Lock:
- target audience
- publication channel

If either is missing, ask first.

### 3.3 Load audience strategy first
Read the matching file under `references/audiences/`.

This module determines:
- reader definition
- business value of this audience
- reader capability assumptions
- motivation level
- writing depth
- value emphasis
- what to avoid

### 3.4 Load channel strategy second
Read the matching file under `references/channels/`.

This module determines:
- title style
- hook style
- paragraph rhythm
- structure expectations
- visual usage
- CTA/ending style
- formatting constraints
- review checklist

### 3.5 Read cross-channel editorial rules
Read `references/editorial-rules.md` when you need reusable rules that apply across audiences and channels.

### 3.6 Only then enter orchestration
Do not assign agents or evaluate deliverables before the active audience and channel strategy are clear.

## 4. Mainline workflow

### 4.1 Lock the business goal
State all four before delegating.

#### 4.1.1 Fixed business goal
What outcome must this content achieve?

#### 4.1.2 Fixed audience
Which strategy module is active, and what audience definition does it enforce?

#### 4.1.3 Fixed channel
Which channel strategy is active?

#### 4.1.4 Fixed success criteria
What must be true for the work to count as done?

### 4.2 Decompose by business function
Do not split work into vague chunks. Split it by quality-driving functions.

Default content-production chain:
1. clarify source material and non-negotiable facts
2. define angle and structure
3. write or rewrite the core draft
4. create visual assets
5. embed visuals into the final article
6. run proof/layout QA on the visual-final version
7. deliver review-ready file to Obsidian
8. publish only after explicit approval

### 4.3 Choose orchestration mode

#### 4.3.1 Solo mode
Use only when the task is too small to justify delegation.

#### 4.3.2 Editorial multi-agent mode
Default for substantial content work.

Recommended roles:
- structure agent
- writer agent
- style-optimization agent
- review agent
- visual/design agent
- proof/layout agent

## 5. Role boundary enforcement

### 5.1 Structure agent
Allowed:
- angle
- audience framing
- hierarchy
- section ordering
- argument spine

Not allowed:
- writing the full final article
- changing the business goal

### 5.2 Writer agent
Allowed:
- produce the main draft
- rewrite weak sections
- turn structure into readable narrative

Not allowed:
- drifting off topic
- replacing fixed examples or changing the audience without approval

### 5.3 Style-optimization agent
Allowed:
- optimize title, hook, pacing, rhythm, and channel expression
- explain why a draft is not fit for the target channel

Not allowed:
- changing the topic
- swapping core cases/tools/objects
- rewriting into generic platform advice

### 5.4 Review agent
Allowed:
- inspect logic, risk, acceptance gaps, unclear claims, and audience/channel mismatch
- output checklist-style correction guidance

Not allowed:
- stealth rewriting the whole article unless explicitly asked

### 5.5 Visual/design agent
Allowed:
- design or generate visual assets aligned to the article

Not allowed:
- replacing final proof/layout review

### 5.6 Proof/layout agent
Allowed:
- final readability checks
- spacing, hierarchy, embeds, formatting consistency, publication-risk checks

Not allowed:
- running before the final visual version exists

## 6. Unified assignment and guidance method

Use one method across assignment, acceptance, and correction.
Do not create separate logic trees unless reality requires it.

### 6.1 Fixed topic
What exactly is this piece about?

### 6.2 Fixed audience
Which audience module is active, and what should the agent assume about the reader?

### 6.3 Fixed channel
Which channel module is active?

### 6.4 Fixed boundaries
What must not change?

### 6.5 Fixed output
What exact deliverable is required?

### 6.6 Fixed failure conditions
What counts as off-track, weak, or unacceptable?

### 6.7 Fixed next-step intent
Explain where this output sits in the larger chain.
Examples:
- this is for structural planning, not final prose
- this is for channel adaptation, not topic replacement
- this is for final QA after images are embedded

## 7. Acceptance and improvement loop

### 7.1 Review against the business goal
Do not grade effort. Grade impact on the intended final outcome.

### 7.2 Review against the active audience and channel
A piece can be strong in isolation and still fail the active audience or channel.
Reject that mismatch early.

### 7.3 Reject vague quality
Reject outputs that are:
- generic
- off-topic
- overlong
- over-explanatory
- channel-inappropriate
- audience-inappropriate
- missing concrete deliverables

### 7.4 Require reflection on weak outputs
When an agent misses the target:

#### 7.4.1 Explain the miss clearly
Examples:
- changed the topic instead of optimizing channel fit
- wrote technical documentation instead of channel-ready content
- wrote for expert engineers instead of motivated workplace learners
- reviewed too early before final images existed
- produced prompts instead of usable embedded assets

#### 7.4.2 State what must be preserved
Examples:
- keep the topic fixed
- keep the factual spine
- keep the active audience and channel strategy

#### 7.4.3 State what must improve
Examples:
- stronger hook
- shorter paragraphs
- clearer contrast
- lighter engineering detail
- tighter conclusion
- more visible practical value

#### 7.4.4 Reassign only after the correction target is explicit
Do not ask for a blind retry.

## 8. Obsidian delivery and publication sequence

### 8.1 Use the real Obsidian vault path
If the user refers to Obsidian, resolve the real vault path first.
Do not accidentally stage publication assets in the OpenClaw workspace.

### 8.2 Stage the reviewable file in Obsidian before publishing
The user should review a real staged file in the target Obsidian directory.

### 8.3 Embed actual images
Do not stop at prompts or image plans.
The staged file must include real image embeds or relative links.

### 8.4 Follow the correct sequence
1. finalize text draft
2. generate/create images and assets
3. embed assets into the final article
4. run proof/layout QA on the visual-final version
5. deliver Obsidian review-ready file
6. publish only after explicit approval

## 9. File navigation

Read these files directly from the main skill when needed:

- `references/audiences/light-technical-workplace-learners.md`
- `references/channels/wechat-public-account.md`
- `references/channels/xiaohongshu.md`
- `references/editorial-rules.md`

Keep future strategy files flat and directly referenced from here. Avoid deep nesting.
