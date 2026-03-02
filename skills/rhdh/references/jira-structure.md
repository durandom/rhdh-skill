# Reference: RHDH Jira Structure

Reference for RHDH Jira projects, the issue types available in each project,
and rules for which project to file issues in.

## Jira Projects

- **RHIDP** — Core Engineering: Main project for tracking engineering work of the Core RHDH Team
- **RHDHPLAN** — Program Planning: High-level planning, Outcomes, Features, and Feature Requests for RHDH program planning
- **RHDHBUGS** — Bug Tracking: Tracking bugs and other defects in RHDH
- **RHDHSUPP** — Customer Support: Communication between customer support team to track customer reported issues and support requests
- **RHDHPAI** — Dev AI Engineering: Main project for tracking engineering work of the Dev AI RHDH Team

## Issue Types by Project

### RHIDP — Core Engineering

- **Epic** — Large feature groupings
- **Story** — User-facing feature work
- **Task** — General engineering work items
- **Sub-task** — Breakdown of parent issues
- **Vulnerability** — CVE tracking and security advisories
- **Weakness** — Security assessment findings (e.g., SAR findings)

### RHDHPLAN — Program Planning

- **Feature** — Product-driven work planned by Product Managers or the development team
- **Feature Request** — Customer or field-driven request, typically filed via support tickets or by Solution Architects
- **Outcome** — High-level program outcomes
- **Sub-task** — Feature breakdown

### RHDHBUGS — Bug Tracking

- **Bug** — Defect reports
- **Sub-task** — Bug sub-tasks

### RHDHSUPP — Customer Support

- **Bug** — Customer-reported issues

Single type only — no Sub-task, Task, or Story types.

### RHDHPAI — Dev AI Engineering

No issues found. Project appears to be newly created or empty.

## Where Each Issue Type Lives

- **Epic, Story, Task** — RHIDP only
- **Sub-task** — RHIDP, RHDHPLAN, RHDHBUGS
- **Feature, Feature Request, Outcome** — RHDHPLAN only
- **Bug** — RHDHBUGS (internal), RHDHSUPP (customer-reported)
- **Vulnerability, Weakness** — RHIDP only

## Key Rules

- Bugs are **never** filed in RHIDP — they go to RHDHBUGS (internal) or RHDHSUPP (customer-reported)
- RHIDP has security-specific types: Vulnerability for CVE tracking, Weakness for security audit findings
- RHDHPLAN is product-level only — no engineering types, just Feature/Feature Request/Outcome
- Features in RHDHPLAN link down to Epics in RHIDP
