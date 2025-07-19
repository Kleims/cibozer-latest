"""
PDF Generation Module for Cibozer Meal Plans
Generates professional PDF documents from meal plan data
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
import os


class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#007bff'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#343a40'),
            spaceAfter=12,
            spaceBefore=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='MealTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#007bff'),
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6c757d')
        ))
    
    def generate_meal_plan_pdf(self, meal_plan, filename):
        """Generate PDF for meal plan"""
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Cibozer Meal Plan", self.styles['MainTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Generation info
        date_str = datetime.now().strftime("%B %d, %Y")
        info_text = f"Generated on {date_str}"
        story.append(Paragraph(info_text, self.styles['InfoText']))
        story.append(Spacer(1, 0.3*inch))
        
        # Check if weekly or single day
        if meal_plan.get('is_weekly'):
            self._add_weekly_plan(story, meal_plan)
        else:
            self._add_single_day_plan(story, meal_plan)
        
        # Build PDF
        doc.build(story)
        return filename
    
    def _add_single_day_plan(self, story, meal_plan):
        """Add single day meal plan to story"""
        # Preferences summary
        prefs = meal_plan.get('preferences', {})
        story.append(Paragraph("Plan Details", self.styles['SectionTitle']))
        
        details_data = [
            ['Diet Type:', prefs.get('diet', 'Standard').title()],
            ['Daily Calories:', str(prefs.get('calories', 2000))],
            ['Meal Pattern:', prefs.get('pattern', 'Standard').title()],
            ['Restrictions:', ', '.join(prefs.get('restrictions', [])) or 'None']
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Daily totals
        totals = meal_plan.get('totals', {})
        story.append(Paragraph("Daily Nutrition Summary", self.styles['SectionTitle']))
        
        nutrition_data = [
            ['Calories', 'Protein', 'Carbs', 'Fat', 'Fiber'],
            [
                str(totals.get('calories', 0)),
                f"{totals.get('protein', 0)}g",
                f"{totals.get('carbs', 0)}g",
                f"{totals.get('fat', 0)}g",
                f"{totals.get('fiber', 0)}g"
            ]
        ]
        
        nutrition_table = Table(nutrition_data, colWidths=[1.2*inch]*5)
        nutrition_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ]))
        story.append(nutrition_table)
        story.append(Spacer(1, 0.4*inch))
        
        # Meals
        story.append(Paragraph("Meals", self.styles['SectionTitle']))
        meals = meal_plan.get('meals', {})
        
        for meal_name, meal_data in meals.items():
            self._add_meal_section(story, meal_name, meal_data)
    
    def _add_weekly_plan(self, story, meal_plan):
        """Add weekly meal plan to story"""
        # Week summary
        summary = meal_plan.get('week_summary', {})
        story.append(Paragraph(f"{summary.get('total_days', 7)}-Day Meal Plan", self.styles['SectionTitle']))
        
        summary_data = [
            ['Average Daily Calories:', str(summary.get('avg_calories', 0))],
            ['Average Daily Protein:', f"{summary.get('avg_protein', 0)}g"],
            ['Average Daily Carbs:', f"{summary.get('avg_carbs', 0)}g"],
            ['Average Daily Fat:', f"{summary.get('avg_fat', 0)}g"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Days
        days = meal_plan.get('days', {})
        daily_totals = meal_plan.get('daily_totals', {})
        
        for day_name, day_meals in days.items():
            # Day header
            story.append(PageBreak())
            story.append(Paragraph(day_name, self.styles['MainTitle']))
            story.append(Spacer(1, 0.2*inch))
            
            # Day totals
            day_total = daily_totals.get(day_name, {})
            story.append(Paragraph("Daily Nutrition", self.styles['SectionTitle']))
            
            day_nutrition_data = [
                ['Calories', 'Protein', 'Carbs', 'Fat'],
                [
                    str(day_total.get('calories', 0)),
                    f"{day_total.get('protein', 0)}g",
                    f"{day_total.get('carbs', 0)}g",
                    f"{day_total.get('fat', 0)}g"
                ]
            ]
            
            day_nutrition_table = Table(day_nutrition_data, colWidths=[1.5*inch]*4)
            day_nutrition_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ]))
            story.append(day_nutrition_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Meals for this day
            for meal_name, meal_data in day_meals.items():
                self._add_meal_section(story, meal_name, meal_data, compact=True)
    
    def _add_meal_section(self, story, meal_name, meal_data, compact=False):
        """Add a meal section to the story"""
        # Meal title
        meal_title = meal_name.replace('_', ' ').title()
        story.append(Paragraph(meal_title, self.styles['MealTitle']))
        
        # Nutrition info
        nutrition_text = (
            f"Calories: {meal_data.get('calories', 0)} | "
            f"Protein: {meal_data.get('protein', 0)}g | "
            f"Carbs: {meal_data.get('carbs', 0)}g | "
            f"Fat: {meal_data.get('fat', 0)}g"
        )
        story.append(Paragraph(nutrition_text, self.styles['InfoText']))
        story.append(Spacer(1, 0.1*inch))
        
        # Ingredients
        ingredients = meal_data.get('ingredients', [])
        if ingredients:
            story.append(Paragraph("<b>Ingredients:</b>", self.styles['Normal']))
            
            ing_data = []
            for ing in ingredients:
                item_name = ing.get('item', '').replace('_', ' ').title()
                amount = ing.get('amount', 0)
                unit = ing.get('unit', '')
                ing_data.append([f"• {item_name}", f"{amount}{unit}"])
            
            ing_table = Table(ing_data, colWidths=[4*inch, 2*inch])
            ing_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(ing_table)
        
        if not compact:
            # Instructions
            instructions = meal_data.get('instructions', [])
            if instructions:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("<b>Instructions:</b>", self.styles['Normal']))
                
                for i, instruction in enumerate(instructions, 1):
                    inst_text = f"{i}. {instruction}"
                    story.append(Paragraph(inst_text, self.styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
        
        story.append(Spacer(1, 0.2*inch))
    
    def generate_grocery_list_pdf(self, grocery_list, filename, days=1):
        """Generate PDF for grocery list"""
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title
        title_text = f"Grocery List - {days} Day{'s' if days > 1 else ''}"
        story.append(Paragraph(title_text, self.styles['MainTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Date
        date_str = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"Generated on {date_str}", self.styles['InfoText']))
        story.append(Spacer(1, 0.3*inch))
        
        # Group by category (future enhancement)
        story.append(Paragraph("Shopping List", self.styles['SectionTitle']))
        
        # Create table data
        table_data = [['Item', 'Amount', '✓']]
        
        for item in grocery_list:
            item_name = item.get('item', '')
            amount = item.get('amount', 0)
            unit = item.get('unit', '')
            table_data.append([item_name, f"{amount} {unit}", '☐'])
        
        # Create table
        grocery_table = Table(table_data, colWidths=[3.5*inch, 2*inch, 0.5*inch])
        grocery_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ]))
        
        story.append(grocery_table)
        
        # Build PDF
        doc.build(story)
        return filename