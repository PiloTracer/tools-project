-- Shipped project templates.
-- A key is inserted only when absent.
-- Child rows are inserted only when that template still has no columns.
-- Basic stays a catalog row with no columns, types, or starter items.

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'basic', 'Basic', NULL, 'Today''s project. The current board and the current work types.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'basic');

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'bug-tracking', 'Bug tracking', 'Engineering', 'Capture a defect and move it through triage, a fix, and verification.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'bug-tracking');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('captured', 'Captured', 0, FALSE),
    ('triaged', 'Triaged', 1, FALSE),
    ('in-progress', 'In progress', 2, FALSE),
    ('verify', 'Verify', 3, FALSE),
    ('done', 'Done', 4, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'bug-tracking'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('bug', 'Bug', 'Something that is broken.', TRUE, 0),
    ('improvement', 'Improvement', 'A change that is not a defect.', FALSE, 1),
    ('investigation', 'Investigation', 'Work to understand a failure.', FALSE, 2)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'bug-tracking'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Login fails on an empty password', 'captured', 'bug', 0),
    ('Confirm severity and owner', 'triaged', 'bug', 1),
    ('Write the failing check', 'in-progress', 'investigation', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'bug-tracking'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'recruitment', 'Recruitment', 'HR', 'Track a candidate from application to offer.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'recruitment');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('applied', 'Applied', 0, FALSE),
    ('screening', 'Screening', 1, FALSE),
    ('interview', 'Interview', 2, FALSE),
    ('offer', 'Offer', 3, FALSE),
    ('hired', 'Hired', 4, TRUE),
    ('declined', 'Declined', 5, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'recruitment'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('candidate', 'Candidate', 'A person in the hiring pipeline.', TRUE, 0),
    ('interview', 'Interview', 'A conversation with a candidate.', FALSE, 1)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'recruitment'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('New application', 'applied', 'candidate', 0),
    ('Screen the application', 'screening', 'candidate', 1),
    ('Schedule the interview', 'interview', 'interview', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'recruitment'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'web-design', 'Web design', 'Design', 'Take a screen from brief to handoff.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'web-design');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('brief', 'Brief', 0, FALSE),
    ('explore', 'Explore', 1, FALSE),
    ('review', 'Review', 2, FALSE),
    ('ready', 'Ready', 3, FALSE),
    ('shipped', 'Shipped', 4, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'web-design'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('screen', 'Screen', 'A page or flow being designed.', TRUE, 0),
    ('asset', 'Asset', 'An image, icon, or file.', FALSE, 1),
    ('research', 'Research', 'Discovery before a design decision.', FALSE, 2)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'web-design'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Capture the brief', 'brief', 'screen', 0),
    ('Sketch the primary flow', 'explore', 'screen', 1),
    ('Prepare the handoff', 'ready', 'screen', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'web-design'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'contract-review', 'Contract review', 'Legal', 'Move a contract from request to a filed decision.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'contract-review');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('requested', 'Requested', 0, FALSE),
    ('review', 'Review', 1, FALSE),
    ('negotiation', 'Negotiation', 2, FALSE),
    ('approved', 'Approved', 3, TRUE),
    ('filed', 'Filed', 4, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'contract-review'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('contract', 'Contract', 'An agreement under review.', TRUE, 0),
    ('compliance', 'Compliance', 'A check against a rule.', FALSE, 1),
    ('policy', 'Policy', 'A written rule.', FALSE, 2)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'contract-review'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Open the request', 'requested', 'contract', 0),
    ('Review the draft', 'review', 'contract', 1),
    ('Record the decision', 'approved', 'contract', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'contract-review'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'month-end-close', 'Month-end close', 'Finance', 'Close a financial period from open items to a reviewed result.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'month-end-close');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('open', 'Open', 0, FALSE),
    ('in-progress', 'In progress', 1, FALSE),
    ('review', 'Review', 2, FALSE),
    ('closed', 'Closed', 3, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'month-end-close'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('close-task', 'Close task', 'A step in closing the period.', TRUE, 0),
    ('invoice', 'Invoice', 'A bill to collect or pay.', FALSE, 1),
    ('adjustment', 'Adjustment', 'A correction to the books.', FALSE, 2)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'month-end-close'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Open the period', 'open', 'close-task', 0),
    ('Collect open invoices', 'in-progress', 'invoice', 1),
    ('Review the adjustments', 'review', 'adjustment', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'month-end-close'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'service-requests', 'Service requests', 'IT', 'Take a request from arrival to a finished change.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'service-requests');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('new', 'New', 0, FALSE),
    ('accepted', 'Accepted', 1, FALSE),
    ('in-progress', 'In progress', 2, FALSE),
    ('waiting', 'Waiting', 3, FALSE),
    ('done', 'Done', 4, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'service-requests'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('request', 'Request', 'Something someone asked IT to do.', TRUE, 0),
    ('access', 'Access', 'A grant or removal of access.', FALSE, 1),
    ('incident', 'Incident', 'Something that is broken in production.', FALSE, 2)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'service-requests'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('New equipment request', 'new', 'request', 0),
    ('Grant repository access', 'accepted', 'access', 1),
    ('Confirm the service is up', 'in-progress', 'incident', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'service-requests'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'project-board', 'Project board', 'Project Management', 'Move planned work from the backlog to done.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'project-board');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('backlog', 'Backlog', 0, FALSE),
    ('ready', 'Ready', 1, FALSE),
    ('in-progress', 'In progress', 2, FALSE),
    ('blocked', 'Blocked', 3, FALSE),
    ('done', 'Done', 4, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'project-board'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('task', 'Task', 'A piece of delivery work.', TRUE, 0),
    ('risk', 'Risk', 'Something that could slip the plan.', FALSE, 1),
    ('decision', 'Decision', 'A choice the project needs.', FALSE, 2)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'project-board'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Confirm the goal', 'backlog', 'task', 0),
    ('Break the next slice down', 'ready', 'task', 1),
    ('Name the top risk', 'backlog', 'risk', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'project-board'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'sales-pipeline', 'Sales pipeline', 'Sales', 'Track a deal from new lead to a closed outcome.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'sales-pipeline');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('lead', 'Lead', 0, FALSE),
    ('qualified', 'Qualified', 1, FALSE),
    ('proposal', 'Proposal', 2, FALSE),
    ('negotiation', 'Negotiation', 3, FALSE),
    ('won', 'Won', 4, TRUE),
    ('lost', 'Lost', 5, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'sales-pipeline'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('deal', 'Deal', 'A sale moving through the pipeline.', TRUE, 0)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'sales-pipeline'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('New lead', 'lead', 'deal', 0),
    ('Qualify the account', 'qualified', 'deal', 1),
    ('Send the proposal', 'proposal', 'deal', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'sales-pipeline'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'campaign', 'Campaign', 'Marketing', 'Take a campaign from an idea to a reported result.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'campaign');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('idea', 'Idea', 0, FALSE),
    ('draft', 'Draft', 1, FALSE),
    ('review', 'Review', 2, FALSE),
    ('scheduled', 'Scheduled', 3, FALSE),
    ('live', 'Live', 4, FALSE),
    ('reported', 'Reported', 5, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'campaign'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('campaign', 'Campaign', 'The effort being launched.', TRUE, 0),
    ('content', 'Content', 'Words or a page in the campaign.', FALSE, 1),
    ('asset', 'Asset', 'A visual used by the campaign.', FALSE, 2)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'campaign'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Name the audience', 'idea', 'campaign', 0),
    ('Draft the piece', 'draft', 'content', 1),
    ('Schedule the publish date', 'scheduled', 'campaign', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'campaign'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'procurement', 'Procurement', 'Operations', 'Track a purchase from request to receipt.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'procurement');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('requested', 'Requested', 0, FALSE),
    ('approved', 'Approved', 1, FALSE),
    ('ordered', 'Ordered', 2, FALSE),
    ('received', 'Received', 3, FALSE),
    ('closed', 'Closed', 4, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'procurement'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('purchase', 'Purchase', 'Something the team is buying.', TRUE, 0),
    ('vendor', 'Vendor', 'The supplier for a purchase.', FALSE, 1)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'procurement'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Request the purchase', 'requested', 'purchase', 0),
    ('Approve the vendor', 'approved', 'vendor', 1),
    ('Confirm receipt', 'received', 'purchase', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'procurement'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

-- Blueprint workflow slices that fit the existing template catalog.
-- customer-onboarding is the project created when a prospect is won.
-- engineering-delivery is Discovery → Architecture → Development → QA → Deployed.

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'customer-onboarding', 'Customer onboarding', 'Operations',
       'Start a won customer: kickoff, paperwork, setup, and the first plan.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'customer-onboarding');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('kickoff', 'Kickoff', 0, FALSE),
    ('paperwork', 'Paperwork', 1, FALSE),
    ('setup', 'Setup', 2, FALSE),
    ('plan', 'Plan', 3, FALSE),
    ('live', 'Live', 4, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'customer-onboarding'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('onboarding', 'Onboarding', 'A step that brings a new customer live.', TRUE, 0),
    ('admin', 'Admin', 'Paperwork or payment for the new customer.', FALSE, 1)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'customer-onboarding'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Welcome and introduction call', 'kickoff', 'onboarding', 0),
    ('Stakeholder introductions', 'kickoff', 'onboarding', 1),
    ('Contract and paperwork', 'paperwork', 'admin', 2),
    ('Deposit or initial payment', 'paperwork', 'admin', 3),
    ('Repository and tooling setup', 'setup', 'onboarding', 4),
    ('Communication channel setup', 'setup', 'onboarding', 5),
    ('First milestone planning', 'plan', 'onboarding', 6)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'customer-onboarding'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'engineering-delivery', 'Engineering delivery', 'Engineering',
       'Move a slice from discovery through architecture, build, QA, and deploy.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'engineering-delivery');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('discovery', 'Discovery', 0, FALSE),
    ('architecture', 'Architecture', 1, FALSE),
    ('development', 'Development', 2, FALSE),
    ('qa', 'QA', 3, FALSE),
    ('deployed', 'Deployed', 4, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'engineering-delivery'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id
  );

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('story', 'Story', 'A slice of product work.', TRUE, 0),
    ('spike', 'Spike', 'Time-boxed investigation.', FALSE, 1)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'engineering-delivery'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id
  );

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Capture the problem', 'discovery', 'story', 0),
    ('Sketch the design', 'architecture', 'spike', 1),
    ('Build the first slice', 'development', 'story', 2),
    ('Verify the release', 'qa', 'story', 3)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'engineering-delivery'
  AND NOT EXISTS (
    SELECT 1 FROM project_template_items c WHERE c.template_id = t.id
  );

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'support-queue', 'Support queue', 'Operations',
       'Take a customer issue from intake to a confirmed fix.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'support-queue');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('intake', 'Intake', 0, FALSE),
    ('working', 'Working', 1, FALSE),
    ('waiting', 'Waiting', 2, FALSE),
    ('resolved', 'Resolved', 3, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'support-queue'
  AND NOT EXISTS (SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id);

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('issue', 'Issue', 'Something a customer reported.', TRUE, 0),
    ('question', 'Question', 'A question that needs an answer.', FALSE, 1)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'support-queue'
  AND NOT EXISTS (SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id);

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Confirm the report', 'intake', 'issue', 0),
    ('Reproduce the issue', 'working', 'issue', 1),
    ('Tell the customer the outcome', 'waiting', 'question', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'support-queue'
  AND NOT EXISTS (SELECT 1 FROM project_template_items c WHERE c.template_id = t.id);

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'implementation', 'Implementation', 'Project Management',
       'Deliver a scoped change from kickoff to handover.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'implementation');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('kickoff', 'Kickoff', 0, FALSE),
    ('build', 'Build', 1, FALSE),
    ('verify', 'Verify', 2, FALSE),
    ('handover', 'Handover', 3, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'implementation'
  AND NOT EXISTS (SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id);

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('deliverable', 'Deliverable', 'A piece of the implementation.', TRUE, 0),
    ('decision', 'Decision', 'A choice the team must record.', FALSE, 1)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'implementation'
  AND NOT EXISTS (SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id);

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Confirm scope', 'kickoff', 'decision', 0),
    ('Build the first slice', 'build', 'deliverable', 1),
    ('Hand over to the customer', 'verify', 'deliverable', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'implementation'
  AND NOT EXISTS (SELECT 1 FROM project_template_items c WHERE c.template_id = t.id);

INSERT INTO project_templates (key, name, team, description, is_builtin)
SELECT 'renewal', 'Renewal', 'Sales',
       'Track a renewal from outreach to a signed term.', TRUE
WHERE NOT EXISTS (SELECT 1 FROM project_templates WHERE key = 'renewal');

INSERT INTO project_template_columns (template_id, key, label, sort_order, is_finished)
SELECT t.id, v.key, v.label, v.sort_order, v.is_finished
FROM project_templates t
JOIN (VALUES
    ('upcoming', 'Upcoming', 0, FALSE),
    ('conversation', 'Conversation', 1, FALSE),
    ('proposal', 'Proposal', 2, FALSE),
    ('renewed', 'Renewed', 3, TRUE),
    ('churned', 'Churned', 4, TRUE)
) AS v(key, label, sort_order, is_finished) ON TRUE
WHERE t.key = 'renewal'
  AND NOT EXISTS (SELECT 1 FROM project_template_columns c WHERE c.template_id = t.id);

INSERT INTO project_template_work_types (template_id, key, name, description, is_default, sort_order)
SELECT t.id, v.key, v.name, v.description, v.is_default, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('renewal', 'Renewal', 'A term that is coming due.', TRUE, 0),
    ('risk', 'Risk', 'A reason the renewal might fail.', FALSE, 1)
) AS v(key, name, description, is_default, sort_order) ON TRUE
WHERE t.key = 'renewal'
  AND NOT EXISTS (SELECT 1 FROM project_template_work_types c WHERE c.template_id = t.id);

INSERT INTO project_template_items (template_id, title, column_key, work_type_key, sort_order)
SELECT t.id, v.title, v.column_key, v.work_type_key, v.sort_order
FROM project_templates t
JOIN (VALUES
    ('Note the renewal date', 'upcoming', 'renewal', 0),
    ('Talk with the customer', 'conversation', 'renewal', 1),
    ('Send the renewal proposal', 'proposal', 'renewal', 2)
) AS v(title, column_key, work_type_key, sort_order) ON TRUE
WHERE t.key = 'renewal'
  AND NOT EXISTS (SELECT 1 FROM project_template_items c WHERE c.template_id = t.id);
