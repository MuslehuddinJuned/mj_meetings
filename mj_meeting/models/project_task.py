from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError

SMART_STATUS = [
    ('done', 'Done'),
    ('done_delayed', 'Done Delayed'),
    ('in_progress', 'In Progress'),
    ('not_started', 'Not Started'),
    ('delayed', 'Delayed'),
    ('canceled', 'Canceled'),
]

# Lower sorts first: what needs attention rises to the top.
SMART_STATUS_ORDER = {
    'delayed': 1,
    'in_progress': 2,
    'not_started': 3,
    'done': 4,
    'done_delayed': 5,
    'canceled': 6,
}

# project.task states that mean the task is finished, from project/models/project_task.py
DONE_STATE = '1_done'
CANCELED_STATE = '1_canceled'
CLOSED_STATES = (DONE_STATE, CANCELED_STATE)
# States that mean work has actually started.
ACTIVE_STATES = ('01_in_progress', '02_changes_requested', '03_approved')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    meeting_id = fields.Many2one(
        comodel_name='hr.meeting',
        string="Meeting",
        tracking=True,
        index='btree_not_null',
        ondelete='set null',
        help="Meeting where this task was discussed or assigned.",
    )
    # hr.employee is readable only by HR officers in Odoo 19, so this field is
    # group-restricted as core's hr module documents. Regular project users keep
    # using the native Assignees (user_ids), which is kept in sync below.
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Assigned Employee",
        tracking=True,
        index='btree_not_null',
        groups="hr.group_hr_user",
    )
    remarks = fields.Html(string="Remarks")
    is_routine_work = fields.Boolean(string="Routine Work", default=False)
    progress_percent = fields.Float(
        string="Progress (%)",
        default=0.0,
        tracking=True,
        aggregator=False,
        help="Manually reported completion, between 0 and 100.",
    )
    completion_date = fields.Date(
        string="Completion Date",
        compute='_compute_completion_date',
        store=True,
        readonly=False,
        copy=False,
        help="Set automatically when the task closes. You can override it.",
    )
    smart_status = fields.Selection(
        selection=SMART_STATUS,
        string="Smart Status",
        compute='_compute_smart_status',
        store=True,
        group_expand='_group_expand_smart_status',
    )
    smart_status_order = fields.Integer(
        string="Smart Status Order",
        compute='_compute_smart_status',
        store=True,
    )

    def _deadline_date(self):
        """date_deadline is a Datetime in Odoo 19; compare it in the user's timezone."""
        self.ensure_one()
        if not self.date_deadline:
            return False
        return fields.Datetime.context_timestamp(self, self.date_deadline).date()

    @api.depends('state', 'date_end', 'is_routine_work')
    def _compute_completion_date(self):
        for task in self:
            if task.is_routine_work:
                # Routine work is never "completed": it just keeps running.
                task.completion_date = False
            elif task.state in CLOSED_STATES:
                if not task.completion_date:
                    closed_on = task.date_end or fields.Datetime.now()
                    task.completion_date = fields.Datetime.context_timestamp(
                        task, closed_on).date()
            else:
                task.completion_date = False

    @api.depends('state', 'date_deadline', 'completion_date', 'is_routine_work')
    def _compute_smart_status(self):
        today = fields.Date.context_today(self)
        for task in self:
            deadline = task._deadline_date()
            overdue = bool(deadline and deadline < today)
            if task.is_routine_work:
                # Routine work has no deadline to miss and no end: it is
                # always considered In Progress, whatever the state says.
                status = 'in_progress'
            elif task.state == CANCELED_STATE:
                status = 'canceled'
            elif task.state == DONE_STATE:
                late = bool(
                    task.completion_date and deadline
                    and task.completion_date > deadline
                )
                status = 'done_delayed' if late else 'done'
            elif task.state in ACTIVE_STATES:
                status = 'delayed' if overdue else 'in_progress'
            else:
                status = 'delayed' if overdue else 'not_started'
            task.smart_status = status
            task.smart_status_order = SMART_STATUS_ORDER[status]

    @api.model
    def _group_expand_smart_status(self, values, domain):
        # Odoo 19 group_expand takes (values, domain) -- the `order` argument
        # of Odoo 17 was removed.
        return [key for key, _label in SMART_STATUS]

    @api.constrains('progress_percent')
    def _check_progress_percent(self):
        for task in self:
            if not 0.0 <= task.progress_percent <= 100.0:
                raise ValidationError(self.env._(
                    "Progress must be between 0 and 100 (got %(value)s on %(task)s).",
                    value=task.progress_percent,
                    task=task.display_name,
                ))

    @api.onchange('is_routine_work')
    def _onchange_is_routine_work(self):
        """Routine work tracks no progress and no completion date."""
        for task in self:
            if task.is_routine_work:
                task.progress_percent = 0.0

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Mirror the employee onto the native Assignees so core project keeps working."""
        for task in self:
            user = task.employee_id.user_id
            if user and user not in task.user_ids:
                task.user_ids = [Command.link(user.id)]

    @api.model
    def _cron_recompute_smart_status(self):
        """A stored compute cannot notice that 'today' moved on, so refresh open tasks daily."""
        open_tasks = self.search([('state', 'not in', CLOSED_STATES)])
        open_tasks.modified(['state'])
        open_tasks.flush_recordset(['smart_status', 'smart_status_order'])
