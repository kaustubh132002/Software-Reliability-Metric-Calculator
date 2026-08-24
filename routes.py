"""
Application routes and controller layer for Software Reliability Metric Calculator (SEQA).
Handles authentication, calculation APIs, dashboard, history CRUD, CSV and PDF reports.
"""

import io
import csv
from datetime import datetime
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file, make_response
)

import models

# ReportLab imports for professional PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

main_bp = Blueprint('main', __name__)


# -----------------------------------------------------------------------------
# Authentication Decorators
# -----------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('main.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('main.login'))
        if session.get('user_role') != 'admin':
            flash("Access denied. Admin privileges are required.", "danger")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# Context Processor for Global Template Variables
# -----------------------------------------------------------------------------

@main_bp.app_context_processor
def inject_global_vars():
    user = None
    if 'user_id' in session:
        user = models.get_user_by_id(session['user_id'])
    return {
        'current_user': user,
        'current_year': datetime.now().year,
        'app_name': "Software Reliability Metric Calculator",
        'subject_code': "SEQA - CS601"
    }


# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember')

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template('login.html', email=email)

        user = models.verify_user(email, password)
        if user:
            session.permanent = bool(remember)
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']

            flash(f"Welcome back, {user['name']}!", "success")
            next_url = request.args.get('next')
            return redirect(next_url or url_for('main.dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            return render_template('login.html', email=email)

    return render_template('login.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html', name=name, email=email)

        if len(name) < 2:
            flash("Name must be at least 2 characters long.", "danger")
            return render_template('register.html', name=name, email=email)

        if '@' not in email or '.' not in email:
            flash("Please enter a valid email address.", "danger")
            return render_template('register.html', name=name, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html', name=name, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html', name=name, email=email)

        existing_user = models.get_user_by_email(email)
        if existing_user:
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for('main.login', email=email))

        user_id = models.create_user(name, email, password, role='user')
        if user_id:
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('main.login', email=email))
        else:
            flash("Registration failed due to a server error. Please try again.", "danger")

    return render_template('register.html')


@main_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('main.login'))


@main_bp.route('/profile')
@login_required
def profile():
    user = models.get_user_by_id(session['user_id'])
    stats = models.get_summary_stats(session['user_id'])
    recent_records = models.get_records(user_id=session['user_id'], limit=5)
    return render_template('profile.html', user=user, stats=stats, recent_records=recent_records)


# -----------------------------------------------------------------------------
# Core Application Views
# -----------------------------------------------------------------------------

@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'

    # Filter by user unless admin wants overview
    stats_user_id = None if is_admin else user_id
    stats = models.get_summary_stats(stats_user_id)
    recent_records = models.get_records(user_id=stats_user_id, limit=6)
    charts_data = models.get_charts_data(user_id=stats_user_id, limit=10)

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_records=recent_records,
        charts_data=charts_data,
        is_admin=is_admin
    )


@main_bp.route('/calculator', methods=['GET', 'POST'])
@login_required
def calculator():
    if request.method == 'POST':
        system_name = request.form.get('system_name', '').strip()
        category = request.form.get('category', 'Web Application').strip()
        operating_time = request.form.get('operating_time')
        failures = request.form.get('failures')
        repair_time = request.form.get('repair_time')
        notes = request.form.get('notes', '').strip()

        # Validation
        if not system_name:
            flash("Please provide a Software/System Name.", "danger")
            return render_template('calculator.html')

        try:
            op_val = float(operating_time)
            fail_val = int(failures)
            rep_val = float(repair_time)
            if op_val < 0 or fail_val < 0 or rep_val < 0:
                raise ValueError("Values cannot be negative.")
        except (ValueError, TypeError) as e:
            flash(f"Invalid input: Please enter valid positive numbers. {str(e)}", "danger")
            return render_template('calculator.html')

        record_id = models.create_record(
            user_id=session['user_id'],
            system_name=system_name,
            operating_time=op_val,
            failures=fail_val,
            repair_time=rep_val,
            notes=notes,
            category=category
        )

        flash(f"Reliability metrics for '{system_name}' calculated and saved successfully!", "success")
        return redirect(url_for('main.history', highlight=record_id))

    return render_template('calculator.html')


@main_bp.route('/history')
@login_required
def history():
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'
    
    # Query parameters
    search = request.args.get('search', '').strip()
    category = request.args.get('category', 'All').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'DESC')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 8, type=int)

    # Restrict to user unless admin
    query_user_id = None if (is_admin and request.args.get('view_all') == '1') else user_id

    total_records = models.count_records(user_id=query_user_id, search=search, category=category)
    total_pages = max(1, (total_records + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    records = models.get_records(
        user_id=query_user_id,
        search=search,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=per_page,
        offset=offset
    )

    return render_template(
        'history.html',
        records=records,
        total_records=total_records,
        current_page=page,
        total_pages=total_pages,
        per_page=per_page,
        search=search,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
        is_admin=is_admin,
        view_all=request.args.get('view_all', '0')
    )


@main_bp.route('/admin')
@admin_required
def admin_panel():
    users = models.list_all_users()
    stats = models.get_summary_stats()
    total_records = models.count_records()
    recent_records = models.get_records(limit=10)
    return render_template(
        'admin.html',
        users=users,
        stats=stats,
        total_records=total_records,
        recent_records=recent_records
    )


# -----------------------------------------------------------------------------
# REST API Endpoints (AJAX & Client Interactivity)
# -----------------------------------------------------------------------------

@main_bp.route('/api/calculate', methods=['POST'])
def api_calculate():
    """
    Live real-time calculation API endpoint for frontend calculator.
    """
    data = request.get_json() or {}
    try:
        op_time = float(data.get('operating_time', 0))
        failures = int(data.get('failures', 0))
        repair_time = float(data.get('repair_time', 0))

        if op_time < 0 or failures < 0 or repair_time < 0:
            return jsonify({'success': False, 'error': 'All numeric inputs must be positive.'}), 400

        metrics = models.calculate_metrics(op_time, failures, repair_time)
        return jsonify({'success': True, 'metrics': metrics})
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid numeric data: {str(e)}'}), 400


@main_bp.route('/api/records', methods=['GET', 'POST'])
@login_required
def api_records():
    user_id = session['user_id']
    if request.method == 'POST':
        data = request.get_json() or {}
        system_name = data.get('system_name', '').strip()
        category = data.get('category', 'General Software').strip()
        operating_time = data.get('operating_time')
        failures = data.get('failures')
        repair_time = data.get('repair_time')
        notes = data.get('notes', '').strip()

        if not system_name:
            return jsonify({'success': False, 'error': 'System Name is required.'}), 400

        try:
            op_val = float(operating_time)
            fail_val = int(failures)
            rep_val = float(repair_time)
            if op_val < 0 or fail_val < 0 or rep_val < 0:
                return jsonify({'success': False, 'error': 'Values cannot be negative.'}), 400
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'error': f'Invalid input: {str(e)}'}), 400

        record_id = models.create_record(
            user_id=user_id,
            system_name=system_name,
            operating_time=op_val,
            failures=fail_val,
            repair_time=rep_val,
            notes=notes,
            category=category
        )
        return jsonify({'success': True, 'record_id': record_id, 'message': 'Record saved successfully.'})

    records = [dict(r) for r in models.get_records(user_id=user_id, limit=50)]
    return jsonify({'success': True, 'records': records})


@main_bp.route('/api/records/<int:record_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_single_record(record_id):
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'
    auth_user_id = None if is_admin else user_id

    record = models.get_record_by_id(record_id, auth_user_id)
    if not record:
        return jsonify({'success': False, 'error': 'Record not found or access unauthorized.'}), 404

    if request.method == 'GET':
        return jsonify({'success': True, 'record': dict(record)})

    elif request.method == 'PUT':
        data = request.get_json() or {}
        system_name = data.get('system_name', '').strip()
        category = data.get('category', 'General Software').strip()
        operating_time = data.get('operating_time')
        failures = data.get('failures')
        repair_time = data.get('repair_time')
        notes = data.get('notes', '').strip()

        if not system_name:
            return jsonify({'success': False, 'error': 'System Name is required.'}), 400

        try:
            op_val = float(operating_time)
            fail_val = int(failures)
            rep_val = float(repair_time)
            if op_val < 0 or fail_val < 0 or rep_val < 0:
                return jsonify({'success': False, 'error': 'Values cannot be negative.'}), 400
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'error': f'Invalid numbers: {str(e)}'}), 400

        updated = models.update_record(
            record_id=record_id,
            user_id=auth_user_id,
            system_name=system_name,
            operating_time=op_val,
            failures=fail_val,
            repair_time=rep_val,
            notes=notes,
            category=category
        )
        if updated:
            return jsonify({'success': True, 'message': 'Record updated successfully.'})
        return jsonify({'success': False, 'error': 'Failed to update record.'}), 500

    elif request.method == 'DELETE':
        deleted = models.delete_record(record_id, auth_user_id)
        if deleted:
            return jsonify({'success': True, 'message': 'Record deleted successfully.'})
        return jsonify({'success': False, 'error': 'Failed to delete record.'}), 500


@main_bp.route('/api/charts-data')
@login_required
def api_charts_data():
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'
    target_user_id = None if (is_admin and request.args.get('all') == '1') else user_id
    limit = request.args.get('limit', 12, type=int)

    data = models.get_charts_data(user_id=target_user_id, limit=limit)
    return jsonify({'success': True, 'data': data})


# -----------------------------------------------------------------------------
# Report Generation: CSV & PDF Export
# -----------------------------------------------------------------------------

@main_bp.route('/export/csv')
@login_required
def export_csv():
    """
    Exports reliability calculation records to CSV format.
    """
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'
    target_user_id = None if (is_admin and request.args.get('all') == '1') else user_id

    records = models.get_records(user_id=target_user_id, limit=1000)

    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        'Record ID', 'System Name', 'Category', 'Operating Time (hrs)',
        'Failures', 'Repair Time (hrs)', 'MTBF (hrs)', 'MTTR (hrs)',
        'Failure Rate (failures/hr)', 'Availability (%)', 'Notes', 'Created At', 'Author'
    ])

    for r in records:
        writer.writerow([
            r['id'],
            r['system_name'],
            r['category'],
            r['operating_time'],
            r['failures'],
            r['repair_time'],
            r['mtbf'],
            r['mttr'],
            f"{r['failure_rate']:.6f}",
            f"{r['availability']:.3f}%",
            r['notes'] or '',
            r['created_at'],
            r['author_name']
        ])

    csv_data = output.getvalue()
    output.close()

    response = make_response(csv_data)
    filename = f"seqa_reliability_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response


@main_bp.route('/export/pdf/<int:record_id>')
@login_required
def export_single_pdf(record_id):
    """
    Generates a structured PDF report for a single system reliability calculation.
    """
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'
    target_user_id = None if is_admin else user_id

    record = models.get_record_by_id(record_id, target_user_id)
    if not record:
        flash("Record not found or access denied.", "danger")
        return redirect(url_for('main.history'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor('#0f2b5c')
    secondary_color = colors.HexColor('#1e40af')
    accent_color = colors.HexColor('#0284c7')
    bg_light = colors.HexColor('#f8fafc')
    text_dark = colors.HexColor('#0f172a')
    border_color = colors.HexColor('#cbd5e1')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=15
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=text_dark
    )

    bold_label = ParagraphStyle(
        'BoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=14,
        textColor=primary_color
    )

    formula_style = ParagraphStyle(
        'FormulaText',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=9,
        leading=13,
        textColor=secondary_color
    )

    story = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>SEQA Software Reliability Audit Report</b>", title_style),
            Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/><b>Audit ID:</b> #{record['id']:05d}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[340, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceBefore=4, spaceAfter=14))

    # 2. System Profile Table
    story.append(Paragraph("1. System Profile & Input Parameters", h2_style))
    profile_data = [
        [Paragraph("System / Software Name:", bold_label), Paragraph(record['system_name'], body_style),
         Paragraph("Category / Domain:", bold_label), Paragraph(record['category'], body_style)],
        [Paragraph("Total Operating Time (T):", bold_label), Paragraph(f"{record['operating_time']} hours", body_style),
         Paragraph("Number of Failures (F):", bold_label), Paragraph(f"{record['failures']} occurrences", body_style)],
        [Paragraph("Total Repair Time (R):", bold_label), Paragraph(f"{record['repair_time']} hours", body_style),
         Paragraph("Evaluation Date:", bold_label), Paragraph(str(record['created_at']), body_style)]
    ]
    profile_table = Table(profile_data, colWidths=[140, 120, 130, 130])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 12))

    # 3. Calculated SEQA Metrics Summary
    story.append(Paragraph("2. Calculated Reliability & Quality Metrics", h2_style))
    metrics_data = [
        [
            Paragraph("Metric Name", bold_label),
            Paragraph("Formula Applied", bold_label),
            Paragraph("Computed Result", bold_label),
            Paragraph("Interpretation", bold_label)
        ],
        [
            Paragraph("<b>MTBF</b><br/>(Mean Time Between Failures)", body_style),
            Paragraph("MTBF = T / F", formula_style),
            Paragraph(f"<b>{record['mtbf']} hours</b>", body_style),
            Paragraph("Average operational uptime between consecutive failures.", body_style)
        ],
        [
            Paragraph("<b>MTTR</b><br/>(Mean Time To Repair)", body_style),
            Paragraph("MTTR = R / F", formula_style),
            Paragraph(f"<b>{record['mttr']} hours</b>", body_style),
            Paragraph("Average duration required to diagnose and restore service.", body_style)
        ],
        [
            Paragraph("<b>Failure Rate (λ)</b>", body_style),
            Paragraph("λ = F / T", formula_style),
            Paragraph(f"<b>{record['failure_rate']:.6f} / hr</b>", body_style),
            Paragraph("Frequency with which system failure events occur per hour.", body_style)
        ],
        [
            Paragraph("<b>System Availability (A)</b>", bold_label),
            Paragraph("A = [MTBF / (MTBF + MTTR)] × 100", formula_style),
            Paragraph(f"<font color='#0284c7' size='11'><b>{record['availability']:.3f}%</b></font>", body_style),
            Paragraph(f"Probability system remains fully operational and accessible.", body_style)
        ]
    ]
    metrics_table = Table(metrics_data, colWidths=[130, 140, 110, 140])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light])
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 14))

    # 4. Detailed Step-by-Step Mathematical Derivation
    story.append(Paragraph("3. Step-by-Step Derivation & SEQA Quality Assessment", h2_style))
    op = record['operating_time']
    fl = record['failures']
    rp = record['repair_time']
    
    derivation_text = f"""
    <b>Step 1: MTBF Calculation</b><br/>
    &bull; MTBF = Operating Time / Failures = {op} hrs / {fl} = <b>{record['mtbf']} hours</b><br/><br/>
    <b>Step 2: MTTR Calculation</b><br/>
    &bull; MTTR = Repair Time / Failures = {rp} hrs / {fl} = <b>{record['mttr']} hours</b><br/><br/>
    <b>Step 3: Failure Rate (&lambda;) Calculation</b><br/>
    &bull; &lambda; = Failures / Operating Time = {fl} / {op} hrs = <b>{record['failure_rate']:.6f} failures/hr</b><br/><br/>
    <b>Step 4: Operational Availability Percentage</b><br/>
    &bull; Availability = [{record['mtbf']} / ({record['mtbf']} + {record['mttr']})] &times; 100 = <b>{record['availability']:.3f}%</b>
    """
    story.append(Paragraph(derivation_text, body_style))
    story.append(Spacer(1, 10))

    if record['notes']:
        story.append(Paragraph("<b>Engineer Notes & Observations:</b>", bold_label))
        story.append(Paragraph(record['notes'], body_style))
        story.append(Spacer(1, 10))

    # 5. Footer & Sign-off
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=14, spaceAfter=8))
    footer_text = Paragraph(
        "<i>Generated by Software Reliability Metric Calculator | SEQA Academic & Industrial Suite &copy; 2026</i>",
        subtitle_style
    )
    story.append(footer_text)

    doc.build(story)
    buffer.seek(0)

    filename = f"reliability_report_{record['system_name'].replace(' ', '_').lower()}_{record['id']}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )


@main_bp.route('/export/pdf/summary')
@login_required
def export_summary_pdf():
    """
    Generates a full multi-system reliability portfolio summary report.
    """
    user_id = session['user_id']
    is_admin = session.get('user_role') == 'admin'
    target_user_id = None if (is_admin and request.args.get('all') == '1') else user_id

    records = models.get_records(user_id=target_user_id, limit=50)
    stats = models.get_summary_stats(user_id=target_user_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#0f2b5c')
    bg_light = colors.HexColor('#f8fafc')
    border_color = colors.HexColor('#cbd5e1')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=primary_color,
        spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=6
    )
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
    cell_header = ParagraphStyle('CellHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=primary_color)

    story = []

    # Title
    story.append(Paragraph("<b>SEQA Software Reliability Portfolio Summary Report</b>", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | User: {session.get('user_name', 'Student')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceBefore=2, spaceAfter=10))

    # Executive KPI Summary
    story.append(Paragraph("Executive Reliability Summary", h2_style))
    kpi_data = [
        [
            Paragraph(f"<b>Total Systems:</b> {stats['total_systems']}", cell_style),
            Paragraph(f"<b>Total Failures:</b> {stats['total_failures']}", cell_style),
            Paragraph(f"<b>Avg MTBF:</b> {stats['avg_mtbf']} hrs", cell_style),
        ],
        [
            Paragraph(f"<b>Avg MTTR:</b> {stats['avg_mttr']} hrs", cell_style),
            Paragraph(f"<b>Overall Availability:</b> {stats['system_wide_availability']}%", cell_style),
            Paragraph(f"<b>Avg Failure Rate:</b> {stats['avg_failure_rate']:.6f}/hr", cell_style)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[180, 180, 180])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_light),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # Records Table
    story.append(Paragraph(f"Reliability Evaluation Records ({len(records)} entries)", h2_style))
    table_data = [
        [
            Paragraph("#", cell_header),
            Paragraph("System Name", cell_header),
            Paragraph("Category", cell_header),
            Paragraph("Op Time (h)", cell_header),
            Paragraph("Fails", cell_header),
            Paragraph("Rep Time (h)", cell_header),
            Paragraph("MTBF (h)", cell_header),
            Paragraph("MTTR (h)", cell_header),
            Paragraph("Fail Rate (λ)", cell_header),
            Paragraph("Availability", cell_header),
        ]
    ]

    for idx, r in enumerate(records, 1):
        table_data.append([
            Paragraph(str(idx), cell_style),
            Paragraph(r['system_name'][:20], cell_style),
            Paragraph(r['category'][:15], cell_style),
            Paragraph(str(r['operating_time']), cell_style),
            Paragraph(str(r['failures']), cell_style),
            Paragraph(str(r['repair_time']), cell_style),
            Paragraph(str(r['mtbf']), cell_style),
            Paragraph(str(r['mttr']), cell_style),
            Paragraph(f"{r['failure_rate']:.5f}", cell_style),
            Paragraph(f"<b>{r['availability']:.2f}%</b>", cell_style),
        ])

    rec_table = Table(table_data, colWidths=[20, 95, 65, 45, 30, 45, 48, 45, 60, 55])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light])
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 12))

    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=8, spaceAfter=6))
    story.append(Paragraph("<i>Software Engineering & Quality Assurance (SEQA) Metric Suite</i>", sub_style))

    doc.build(story)
    buffer.seek(0)

    filename = f"seqa_reliability_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )
