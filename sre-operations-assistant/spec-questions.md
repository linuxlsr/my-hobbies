# SRE Operations Assistant - Specification Questions

## 3. EC2 Environment Details ✓
**3.1** How many EC2 instances? **1-10 instances**
**3.2** What instance types? **Web servers, databases**
**3.3** What operating systems? **Amazon Linux, RedHat, Rocky Linux, Ubuntu**
**3.4** Already using Inspector v2 or need to enable it? **Already Inspector capable**
**3.5** Single AWS account or multi-account setup? **Single account for this iteration**

## 4. Vulnerability Management Priorities ✓
**4.1** Real-time alerting on critical findings? **Near real-time, 24 hour lag acceptable**
**4.2** Automated patch compliance reporting? **Yes, with patches during off hours/low load (GenAI analysis)**
**4.3** Risk scoring and prioritization? **On-demand by criticality, future auto-patch for criticals**
**4.4** Integration with existing ticketing systems? **Not at this time**
**4.5** Vulnerability trend analysis over time? **Not at this time**

## 5. Telemetry Focus ✓
**5.1** Performance metrics? (CPU, memory, network) **Yes**
**5.2** Security events? (login attempts, privilege escalation) **Yes**
**5.3** Configuration changes? (security group modifications) **Yes**
**5.4** All of the above with smart filtering? **Yes**
**5.5** Custom CloudWatch alarms already configured? **No**

## 6. Remediation Scope ✓
**6.1** Read-only analysis and recommendations? **Yes**
**6.2** Automated patching for non-critical systems? **Yes**
**6.3** Workflow triggers for manual approval? **Yes**
**6.4** Full automation with rollback capabilities? **Yes**
**6.5** Integration with change management processes? **Not at this time**

## 7. MCP Integration Method ✓
**7.1** Direct MCP client connection? **Yes**
**7.2** Integration with existing tools (Claude Desktop, etc.)? **No**
**7.3** Custom dashboard/interface? **No**
**7.4** CLI tool for SRE team? **MCP-powered CLI**
**7.5** Slack/Teams integration for alerts? **Yes (Slack + Teams bots)**

## 8. Security & Access Requirements ✓
**8.1** Read-only monitoring access? **Yes**
**8.2** Limited write access (scaling, restarts)? **Yes**
**8.3** Patch management permissions? **Yes**
**8.4** Cross-account access needed? **Yes**
**8.5** Existing IAM policies to follow? **No, implement with Terraform**

## 9. Deployment Preferences ✓
**9.1** AWS CDK (Python/TypeScript)? **Python**
**9.2** Terraform? **Yes**
**9.3** CloudFormation? **Only where Terraform won't work**
**9.4** Serverless Framework? **Yes**
**9.5** Container-based deployment (ECS/EKS)? **ECS as needed**

## 10. Budget & Timeline ✓
**10.1** Monthly budget range? **Under $100 to start, scalable later**
**10.2** Timeline for deployment? **1 week prototyping/testing**
**10.3** Pilot phase with limited instances first? **Yes**
**10.4** Production rollout timeline? **2 weeks**
**10.5** Maintenance and support expectations? **Managed service approach**