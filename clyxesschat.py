import time
import os
import re
from fpdf import FPDF
from datetime import datetime
import base64

class ClyxessSchoolMode:
    def __init__(self, logo_path=None):
        self.age_groups = {
            "1-3 Yrs": {
                "focus": "Early Brain Development & Sensory Logic",
                "task_type": "Visual Tap, Sound Matching & Color Sorting",
                "anti_youtube_goal": "Replace passive video watching with active sensory touch.",
                "hint_style": "Masti wala"
            },
            "4-6 Yrs": {
                "focus": "Curiosity & Basic Logic",
                "task_type": "Interactive Story-Building & Shape Puzzles",
                "anti_youtube_goal": "Turn cartoon viewing into interactive storytelling.",
                "hint_style": "Kahani wala"
            },
            "7-10 Yrs": {
                "focus": "Maker & Practical Science",
                "task_type": "Step-by-step DIY Projects & Logic Challenges",
                "anti_youtube_goal": "Shift focus from gaming videos to building virtual models.",
                "hint_style": "Jugaad wala"
            },
            "11-17 Yrs": {
                "focus": "Future Tech, AI & App Prototyping",
                "task_type": "Coding Logic, App Wireframing & Problem Solving",
                "anti_youtube_goal": "Channel social media energy into tech innovation.",
                "hint_style": "Innovator wala"
            }
        }
        self.cert_folder = "Clyxess_Certificates"
        if not os.path.exists(self.cert_folder):
            os.makedirs(self.cert_folder)
        self.logo_path = logo_path

    def select_age_group(self, choice):
        data = self.age_groups.get(choice)
        if data:
            print(f"\n[Mode Activated] {choice}")
            print(f"Goal: {data['focus']}")
            print(f"Strategy: {data['anti_youtube_goal']}\n")
            return data
        return "Invalid selection! Bhai 1-3, 4-6, 7-10, 11-17 me se chun."

    def give_ai_hint_or_task(self, age_group, child_query):
        print(f"--- Clyxess AI Lab (Age: {age_group}) ---")
        print(f"Input: '{child_query}'")
        print("AI Soch raha hai... (Socratic Engine)")
        time.sleep(0.5)

        # CHATPATA HINT SYSTEM
        if age_group == "1-3 Yrs":
            response = "💡 Arre wah! Dekho laal gubbara chamak raha hai. Uspe tap karo toh kya awaz aayegi? Dhundho aur ek laal cheej!"
        elif age_group == "4-6 Yrs":
            response = "🦁 Kahani Time! Sher jungle me kho gaya. Pehle ped par jaye ya nadi par? Tum batao kya hoga aage?"
        elif age_group == "7-10 Yrs":
            response = "🛠️ Jugaad Sawal: Rocket banana hai? Socho pehle hawa kaha se niklegi? Bottle ko ulta kare toh? Try karo!"
        else:
            response = "🚀 Innovator Challenge: Is bade problem ko 2 chote tukdo me todo. Pehle wireframe banao, code baad me. Tu kar lega!"

        print(f"AI Response: {response}\n")
        return response

    def generate_pdf_certificate(self, child_name, module_name, age_group):
        print(f"[PDF Generator] Certificate ban raha hai...")

        # Safe filename
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', child_name)
        safe_module = re.sub(r'[^a-zA-Z0-9_]', '_', module_name)

        pdf = FPDF()
        pdf.add_page()
        
        # Logo if exists
        if self.logo_path and os.path.exists(self.logo_path):
            pdf.image(self.logo_path, x=85, y=10, w=40)
            pdf.ln(35)
        
        # Header
        pdf.set_font("Arial", "B", 20)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(0, 10, "CLYXESS AI SCHOOL", 0, 1, "C")
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(100,100,100)
        pdf.cell(0, 5, "Future Innovators Program - Anti-Youtube Creative Lab", 0, 1, "C")
        pdf.ln(8)

        # Title
        pdf.set_font("Arial", "B", 22)
        pdf.set_text_color(20,20,20)
        pdf.cell(0, 15, "CERTIFICATE OF ACHIEVEMENT", 0, 1, "C")
        pdf.ln(5)
        
        pdf.set_draw_color(0,102,204)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(10)

        # Body
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, "This is proudly presented to", 0, 1, "C")
        pdf.set_font("Arial", "B", 20)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(0, 12, f"{child_name}", 0, 1, "C")
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(0,0,0)
        pdf.cell(0, 10, f"for mastering the practical module:", 0, 1, "C")
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"'{module_name}'", 0, 1, "C")
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 7, f"Age Group: {age_group} | Focus: {self.age_groups[age_group]['focus']}", 0, 1, "C")
        pdf.cell(0, 7, f"Date: {datetime.now().strftime('%d-%b-%Y %I:%M %p')}", 0, 1, "C")
        pdf.ln(15)

        # Footer - Verification
        verify_id = f"CXL-{int(time.time())}"
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Verified by ClyxessChat AI Secure Ledger | ID: {verify_id}", 0, 1, "C")
        pdf.cell(0, 5, "Share this PDF on WhatsApp / Telegram / Email", 0, 1, "C")

        filename = f"{self.cert_folder}/{safe_name}_{safe_module}_{verify_id}.pdf"
        pdf.output(filename)

        print(f"Success! File: {filename}")
        print(f" -> Ab is file ko WhatsApp par share kar sakte ho\n")
        return filename

# --- TESTING ---
if __name__ == "__main__":
    # logo ka path de de yaha: logo.png
    app = ClyxessSchoolMode(logo_path="logo.png")

    current_age_group = "7-10 Yrs"
    app.select_age_group(current_age_group)
    app.give_ai_hint_or_task(current_age_group, "How do I make a water rocket?")
    app.generate_pdf_certificate("Aarav", "Junior Maker & Physics Basics", current_age_group)
