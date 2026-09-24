==========================================
Meeting Management (mj_meeting)
==========================================

This module records your meetings and turns the points raised in them into work
that somebody owns. Every meeting keeps its own reference, agenda, minutes and
list of attendees, and the follow-up points become tasks linked back to the
meeting they came from.

Those follow-up tasks are ordinary ``project.task`` records. They show up in the
Project app with its kanban, calendar, deadline and timesheet features, which
means there is no second task model to maintain and no data locked inside a
custom screen.

The minutes can be emailed to every attendee in one click, with the files
attached to the meeting included in the message.

====================================
Features
====================================

- Meeting register with an automatic reference such as ``Meet/2026/09/0001``.
- Rich text Agenda and Meeting Minutes on every meeting.
- Attendees picked from your employees, shown with the employee avatar widget.
- One click email of the agenda and the minutes to the work email of every
  attendee, with the meeting attachments included.
- The email body is a standard ``mail.template``, so it can be restyled from the
  interface without touching code.
- Follow-up tasks created from the meeting, on Odoo's own ``project.task`` model.
- Tasks open in a popup, both when adding a line and when editing an existing one.
- Smart Status that tells a task finished on time apart from one finished late.
- Overdue work sorts to the top of the list.
- A daily scheduled action keeps the Smart Status correct as dates pass.
- Meeting, employee and Smart Status filters and group by options added to the
  Project search view.
- Full chatter on meetings, with change tracking on the title, date and attendees.
- Depends only on core Odoo apps. No configuration needed.

====================================
Smart Status
====================================

The stage of a task tells you what somebody set. Smart Status tells you what
actually happened, by reading the deadline and the completion date together with
the state of the task.

============== ================================================================
Smart Status   Meaning
============== ================================================================
Delayed        Still open and the deadline has passed.
In Progress    Work has started and the deadline is still ahead.
Not Started    Nobody has picked it up yet and the deadline is still ahead.
Done           Closed on or before the deadline.
Done Delayed   Closed, but after the deadline.
Cancelled      Dropped.
============== ================================================================

A stored field cannot notice that today has moved on by itself, so a scheduled
action named **Meeting: Refresh Task Smart Status** recomputes the open tasks
once a day.

====================================
Fields Added To Tasks
====================================

Nothing is removed from the task form. These fields are added, mostly on a
**Follow-up** tab, and in the list view they arrive as optional columns.

- **Meeting** - the meeting this task came out of.
- **Assigned Employee** - the employee who owns it. Setting it fills Odoo's own
  Assignees field as well.
- **Remarks** - a rich text field for notes, blockers and what was tried.
- **Routine Work** - marks recurring housekeeping so it can be filtered out.
- **Progress** - a reported percentage from 0 to 100.
- **Completion Date** - filled in when the task closes, and still editable.
- **Smart Status** - computed, as described above.

Assigned Employee is limited to the HR Officer group, because Odoo 19 restricts
employee records to HR. Every other user keeps working with Odoo's standard
Assignees field, which this module keeps in step.

====================================
Installation
====================================

1. Place the module in your custom addons directory
2. Update apps list
3. Install **Meeting Management (mj_meeting)** module from the Apps menu.

The dependencies ``mail``, ``hr`` and ``project`` are installed automatically if
they are not present yet.

====================================
Usage
====================================

Nothing to configure.

1. Open the **Meeting** app and create a meeting. Set the title and the date and
   pick the attendees. The reference is generated on save.
2. Write the agenda before the meeting and the minutes during it.
3. In the **Tasks** tab, use *Add a line* to record each follow-up point with its
   owner and its deadline.
4. Press **Send Email** to mail the agenda and the minutes to the attendees.
5. Use **Meeting > Tasks** to review every open point, grouped by Smart Status.

To change the meeting numbering, edit the **Meeting Sequence** record under
Settings > Technical > Sequences.

To restyle the notification email, edit the **Meeting: Notification** template
under Settings > Technical > Email Templates.

====================================
Security
====================================

- **HR Officer** (``hr.group_hr_user``): read, write, create and delete meetings.
- Every other internal user (``base.group_user``): read only on meetings, so the
  Meeting field on a task is readable from the Project app.

Access to the follow-up tasks themselves is governed by the standard Project
groups and record rules.

====================================
Author
====================================

Developed by Musleh Uddin Juned

====================================
License
====================================

LGPL-3
