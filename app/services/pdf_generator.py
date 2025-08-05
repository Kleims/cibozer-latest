"""PDF generation service for meal plans."""
import os
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from flask import current_app


class PDFGenerator:
    """Service for generating PDF documents from meal plans."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for the PDF."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#7F8C8D'),
            spaceAfter=10
        ))
    
    def generate_meal_plan_pdf(self, meal_plan, title="My Meal Plan"):
        """
        Generate a PDF document from a meal plan.
        
        Args:
            meal_plan: Dictionary containing meal plan data
            title: Title for the PDF document
            
        Returns:
            Path to the generated PDF file
        """
        try:
            # Create temporary file
            pdf_file = tempfile.NamedTemporaryFile(
                suffix='.pdf',
                prefix='meal_plan_',
                dir=current_app.config.get('PDF_OUTPUT_DIR', 'static/pdfs'),
                delete=False
            )
            pdf_path = pdf_file.name
            pdf_file.close()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Add title
            story.append(Paragraph(title, self.styles['CustomTitle']))
            story.append(Spacer(1, 0.2*inch))
            
            # Add summary
            if 'summary' in meal_plan:
                story.extend(self._add_summary(meal_plan['summary']))
            
            # Add meal plan days
            for day_data in meal_plan.get('days', []):
                story.extend(self._add_day(day_data))
                story.append(PageBreak())
            
            # Add grocery list if available
            if 'grocery_list' in meal_plan:
                story.extend(self._add_grocery_list(meal_plan['grocery_list']))
            
            # Build PDF
            doc.build(story)
            
            current_app.logger.info(f"PDF generated successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            current_app.logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    def _add_summary(self, summary):
        """Add summary section to PDF."""
        elements = []
        
        elements.append(Paragraph("Meal Plan Summary", self.styles['CustomHeading']))
        
        # Summary table
        data = [
            ['Total Days:', str(summary.get('total_days', 0))],
            ['Total Meals:', str(summary.get('total_meals', 0))],
            ['Average Daily Calories:', str(summary.get('average_daily_calories', 0))],
        ]
        
        # Add macros if available
        if 'average_daily_macros' in summary:
            macros = summary['average_daily_macros']
            data.extend([
                ['Average Protein:', f"{macros.get('protein', 0)}g"],
                ['Average Carbs:', f"{macros.get('carbs', 0)}g"],
                ['Average Fat:', f"{macros.get('fat', 0)}g"],
            ])
        
        table = Table(data, colWidths=[2.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*inch))
        
        return elements
    
    def _add_day(self, day_data):
        """Add a single day to the PDF."""
        elements = []
        
        # Day header
        day_num = day_data.get('day', 1)
        elements.append(Paragraph(f"Day {day_num}", self.styles['CustomHeading']))
        
        # Day stats
        total_calories = day_data.get('total_calories', 0)
        macros = day_data.get('macros', {})
        
        stats_text = f"Total Calories: {total_calories} | "
        stats_text += f"Protein: {macros.get('protein', 0)}g | "
        stats_text += f"Carbs: {macros.get('carbs', 0)}g | "
        stats_text += f"Fat: {macros.get('fat', 0)}g"
        
        elements.append(Paragraph(stats_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Meals
        for meal in day_data.get('meals', []):
            elements.extend(self._add_meal(meal))
        
        return elements
    
    def _add_meal(self, meal_data):
        """Add a single meal to the PDF."""
        elements = []
        
        # Meal header
        meal_name = meal_data.get('name', 'Unnamed Meal')
        meal_type = meal_data.get('type', '').title()
        calories = meal_data.get('calories', 0)
        
        header_text = f"{meal_type}: {meal_name} ({calories} cal)"
        elements.append(Paragraph(header_text, self.styles['CustomSubheading']))
        
        # Ingredients
        ingredients = meal_data.get('ingredients', [])
        if ingredients:
            elements.append(Paragraph("<b>Ingredients:</b>", self.styles['Normal']))
            for ingredient in ingredients:
                elements.append(Paragraph(f"• {ingredient}", self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        # Instructions
        instructions = meal_data.get('instructions', [])
        if instructions:
            elements.append(Paragraph("<b>Instructions:</b>", self.styles['Normal']))
            for i, instruction in enumerate(instructions, 1):
                elements.append(Paragraph(f"{i}. {instruction}", self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        # Nutrition info
        macros = meal_data.get('macros', {})
        if macros:
            nutrition_text = f"<b>Nutrition:</b> "
            nutrition_text += f"Protein: {macros.get('protein', 0)}g | "
            nutrition_text += f"Carbs: {macros.get('carbs', 0)}g | "
            nutrition_text += f"Fat: {macros.get('fat', 0)}g"
            elements.append(Paragraph(nutrition_text, self.styles['Normal']))
        
        # Prep/Cook time
        prep_time = meal_data.get('prep_time')
        cook_time = meal_data.get('cook_time')
        if prep_time or cook_time:
            time_text = "<b>Time:</b> "
            if prep_time:
                time_text += f"Prep: {prep_time} min "
            if cook_time:
                time_text += f"Cook: {cook_time} min"
            elements.append(Paragraph(time_text, self.styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _add_grocery_list(self, grocery_list):
        """Add grocery list section to PDF."""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Grocery List", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        for category, items in grocery_list.items():
            if items:
                elements.append(Paragraph(f"<b>{category.title()}</b>", self.styles['Normal']))
                for item in items:
                    elements.append(Paragraph(f"□ {item}", self.styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def generate_recipe_pdf(self, recipe, title=None):
        """Generate a PDF for a single recipe."""
        # Implementation for single recipe PDF
        pass
    
    def generate_shopping_list_pdf(self, shopping_list):
        """Generate a PDF shopping list."""
        # Implementation for shopping list PDF
        pass