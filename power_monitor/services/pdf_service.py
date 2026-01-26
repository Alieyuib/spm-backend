# power_monitor/services/pdf_service.py
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PDFReportService:
    """
    PDF generation service for energy reports
    
    Features:
    - Professional PDF layout
    - Charts and tables
    - Brand styling
    - Multiple page support
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
    
    def generate_report_pdf(self, report):
        """Generate PDF for energy report"""
        try:
            buffer = BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Add header
            elements.extend(self._create_header(report))
            
            # Add report info
            elements.extend(self._create_report_info(report))
            
            # Add consumption summary
            elements.extend(self._create_consumption_summary(report))
            
            # Add performance metrics
            elements.extend(self._create_performance_metrics(report))
            
            # Add alert summary
            elements.extend(self._create_alert_summary(report))
            
            # Add cost analysis
            elements.extend(self._create_cost_analysis(report))
            
            # Add device details if multiple devices
            if report.report_data.get('devices'):
                elements.extend(self._create_device_details(report))
            
            # Add footer info
            elements.extend(self._create_footer(report))
            
            # Build PDF
            doc.build(elements, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
            
            buffer.seek(0)
            logger.info(f"PDF generated for report {report.id}")
            return buffer
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}")
            return None
    
    def _create_header(self, report):
        """Create PDF header"""
        elements = []
        
        # Title
        title = Paragraph(
            "⚡ ENERGY REPORT",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Report type and period
        report_info = Paragraph(
            f"<b>{report.report_type.upper()} REPORT</b><br/>"
            f"Period: {report.start_date} to {report.end_date}",
            self.styles['Normal']
        )
        elements.append(report_info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Client info
        client_info = Paragraph(
            f"<b>Client:</b> {report.client.name}<br/>"
            f"<b>Generated:</b> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['Normal']
        )
        elements.append(client_info)
        elements.append(Spacer(1, 0.4*inch))
        
        return elements
    
    def _create_report_info(self, report):
        """Create report information section"""
        elements = []
        
        # Device info
        if report.device:
            device_text = f"<b>Device:</b> {report.device.device_name} ({report.device.device_id})"
        else:
            device_count = len(report.report_data.get('devices', []))
            device_text = f"<b>Devices:</b> {device_count} device(s) monitored"
        
        elements.append(Paragraph(device_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_consumption_summary(self, report):
        """Create consumption summary table"""
        elements = []
        
        # Section heading
        elements.append(Paragraph("📊 CONSUMPTION SUMMARY", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Create table data
        data = [
            ['Metric', 'Value'],
            ['Total Consumption', f'{report.total_consumption_kwh:.2f} kWh'],
            ['Daily Average', f'{report.avg_daily_consumption:.2f} kWh'],
            ['Total Cost', f'₦{report.total_cost:,.2f}'],
            ['Report Period', f'{(report.end_date - report.start_date).days + 1} days'],
        ]
        
        # Create table
        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_performance_metrics(self, report):
        """Create performance metrics table"""
        elements = []
        
        # Section heading
        elements.append(Paragraph("⚡ PERFORMANCE METRICS", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Create table data
        data = [
            ['Metric', 'Value'],
            ['Peak Power', f'{report.peak_power:.0f} W'],
            ['Average Power Factor', f'{report.avg_power_factor:.3f}'],
            ['System Uptime', f'{report.uptime_hours:.1f} hours'],
        ]
        
        # Create table
        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#48bb78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_alert_summary(self, report):
        """Create alert summary section"""
        elements = []
        
        # Section heading
        elements.append(Paragraph("⚠️ ALERT SUMMARY", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Alert status
        if report.total_alerts == 0:
            alert_text = Paragraph(
                "✅ <b>No alerts during this period.</b> All systems operating normally.",
                self.styles['Normal']
            )
            elements.append(alert_text)
        else:
            # Create table
            data = [
                ['Alert Type', 'Count'],
                ['Total Alerts', str(report.total_alerts)],
                ['Critical Alerts', str(report.critical_alerts)],
                ['Warning Alerts', str(report.total_alerts - report.critical_alerts)],
            ]
            
            table = Table(data, colWidths=[3*inch, 3*inch])
            
            # Color code based on severity
            bg_color = colors.HexColor('#fed7d7') if report.critical_alerts > 0 else colors.HexColor('#fef5e7')
            
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f56565')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), bg_color),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(table)
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_cost_analysis(self, report):
        """Create cost analysis section"""
        elements = []
        
        # Section heading
        elements.append(Paragraph("💰 COST ANALYSIS", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Calculate projections
        days_in_period = (report.end_date - report.start_date).days + 1
        daily_cost = report.total_cost / days_in_period if days_in_period > 0 else 0
        monthly_projection = daily_cost * 30
        yearly_projection = daily_cost * 365
        
        # Create table
        data = [
            ['Period', 'Cost'],
            [f'{report.report_type.title()} Cost', f'₦{report.total_cost:,.2f}'],
            ['Daily Average', f'₦{daily_cost:,.2f}'],
            ['Monthly Projection', f'₦{monthly_projection:,.2f}'],
            ['Yearly Projection', f'₦{yearly_projection:,.2f}'],
        ]
        
        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9f7aea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e9d8fd')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_device_details(self, report):
        """Create device details section for multi-device reports"""
        elements = []
        
        devices_data = report.report_data.get('devices', [])
        if not devices_data:
            return elements
        
        # Section heading
        elements.append(PageBreak())
        elements.append(Paragraph("🔌 DEVICE BREAKDOWN", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Create table for each device
        for device_info in devices_data:
            # Device header
            device_header = Paragraph(
                f"<b>{device_info['device_name']}</b> ({device_info['device_id']})",
                self.styles['CustomSubHeading']
            )
            elements.append(device_header)
            elements.append(Spacer(1, 0.1*inch))
            
            # Device stats table
            data = [
                ['Metric', 'Value'],
                ['Consumption', f"{device_info['consumption']:.2f} kWh"],
                ['Cost', f"₦{device_info['cost']:,.2f}"],
                ['Peak Power', f"{device_info['peak_power']:.0f} W"],
                ['Uptime', f"{device_info['uptime']:.1f} hours"],
                ['Alerts', f"{device_info['alerts']} ({device_info['critical_alerts']} critical)"],
            ]
            
            table = Table(data, colWidths=[2.5*inch, 3.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4299e1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#bee3f8')),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_footer(self, report):
        """Create footer section"""
        elements = []
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Footer text
        footer_text = Paragraph(
            "<i>This report was automatically generated by Smart Monitoring System.<br/>"
            f"Report ID: {report.id} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            self.styles['Normal']
        )
        elements.append(footer_text)
        
        return elements
    
    def _add_page_number(self, canvas, doc):
        """Add page number to each page"""
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(
            doc.pagesize[0] - 72,
            0.5 * inch,
            text
        )
        canvas.restoreState()