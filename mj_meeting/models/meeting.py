from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class HrMeeting(models.Model):
    _name = 'hr.meeting'
    _inherit = ['mail.thread']
    _description = 'Meeting Management'
    _order = 'meeting_date desc, id desc'

    name = fields.Char(
        string="Meeting ID", default="New", copy=False, readonly=True, tracking=True)
    title = fields.Char(string="Title", required=True, tracking=True)
    agenda = fields.Html(string="Agenda")
    meeting_minutes = fields.Html(string="Meeting Minutes")
    meeting_date = fields.Date(
        string="Date", default=fields.Date.context_today, tracking=True)
    employee_id = fields.Many2many(
        comodel_name='hr.employee', string="Attendees", required=True, tracking=True)
    task_ids = fields.One2many(
        comodel_name='project.task', inverse_name='meeting_id', string="Tasks")
    task_count = fields.Integer(string="Tasks", compute='_compute_task_count')

    @api.depends('task_ids')
    def _compute_task_count(self):
        for rec in self:
            rec.task_count = len(rec.task_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                today = fields.Date.context_today(self)
                sequence = self.env['ir.sequence'].next_by_code(
                    'hr.meeting', sequence_date=today) or '0000'
                vals['name'] = f"Meet/{today.strftime('%Y')}/{today.strftime('%m')}/{sequence}"
        return super().create(vals_list)

    def action_view_tasks(self):
        self.ensure_one()
        return {
            'name': self.env._("Tasks"),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('mj_meeting.view_meeting_task_list').id, 'list'),
                (False, 'form'),
            ],
            'domain': [('meeting_id', '=', self.id)],
            'context': {
                'default_meeting_id': self.id,
            },
        }

    def action_send_meeting_email(self):
        template = self.env.ref(
            'mj_meeting.mail_template_hr_meeting', raise_if_not_found=False)
        if not template:
            raise UserError(self.env._(
                "The meeting notification email template is missing. "
                "Please upgrade the Meeting module."
            ))
        for meeting in self:
            if not meeting.employee_id:
                raise UserError(self.env._(
                    "No attendees found on %(meeting)s.",
                    meeting=meeting.display_name,
                ))
            emails = [email for email in meeting.employee_id.mapped('work_email') if email]
            if not emails:
                raise UserError(self.env._(
                    "None of the attendees of %(meeting)s have a work email.",
                    meeting=meeting.display_name,
                ))

            email_values = {'email_to': ",".join(emails)}
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', meeting._name),
                ('res_id', '=', meeting.id),
            ])
            if attachments:
                email_values['attachment_ids'] = [Command.set(attachments.ids)]

            template.send_mail(
                meeting.id, force_send=True, email_values=email_values)
        return True
