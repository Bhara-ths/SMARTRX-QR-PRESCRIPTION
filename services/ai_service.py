import os
from openai import OpenAI
from flask import current_app

class AIService:
    @staticmethod
    def get_client():
        api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            return None # Use mock if no API key
        return OpenAI(api_key=api_key)

    @staticmethod
    def _get_mock_response(system_prompt, user_question=""):
        # A simple rule-based mock for demonstration purposes
        if "side effect" in user_question.lower():
            return "Based on your prescription, common side effects may include mild nausea, dizziness, or drowsiness. If you experience severe allergic reactions, stop taking the medication and consult your doctor immediately.\n\n*This information is for educational purposes only. Consult your doctor or pharmacist before making medical decisions.*"
        elif "miss" in user_question.lower() or "forgot" in user_question.lower():
            return "If you miss a dose, take it as soon as you remember. However, if it is almost time for your next scheduled dose, skip the missed dose and resume your regular schedule. Do not double the dose.\n\n*This information is for educational purposes only. Consult your doctor or pharmacist before making medical decisions.*"
        elif user_question:
            return "I am your SmartRx AI Assistant. I can help explain your medication purpose, dosage, and side effects based on your prescription. (Note: Running in mock mode because API key is missing).\n\n*This information is for educational purposes only. Consult your doctor or pharmacist before making medical decisions.*"
        
        # Default full explanation mock
        return """### Prescription Overview
Based on the provided prescription context, here is a breakdown:

**Purpose:** The prescribed medications are intended to treat your diagnosed condition and manage symptoms.
**Dosage & Frequency:** Please strictly follow the dosage instructions (e.g., morning/night, after meals) as indicated on your prescription.
**Precautions:** Avoid alcohol while on this medication. Store in a cool, dry place.
**Side Effects:** Watch out for common side effects like dizziness. 

*This information is for educational purposes only. Consult your doctor or pharmacist before making medical decisions.*"""

    @staticmethod
    def get_assistant_response(patient_name, prescription_context, user_question):
        """
        Retrieves a response from the AI assistant restricted to the prescription context.
        """
        try:
            client = AIService.get_client()
            
            system_prompt = f"""
            You are a helpful and professional Medical AI Assistant for a patient named {patient_name}. 
            Your SOLE purpose is to explain the medicines, dosages, side effects, precautions, and next appointments based ONLY on the provided prescription context below.
            
            PRESCRIPTION CONTEXT:
            {prescription_context}
            
            STRICT RULES:
            1. NEVER diagnose diseases or modify treatment.
            2. If the user asks a medical question that cannot be answered using ONLY the prescription context, you MUST politely advise them to consult their doctor.
            3. Keep your answers concise, reassuring, and easy to understand.
            4. ALWAYS end your response with: "This information is for educational purposes only. Consult your doctor or pharmacist before making medical decisions."
            """

            if not client:
                return AIService._get_mock_response(system_prompt, user_question)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                temperature=0.3, # Keep it deterministic and strict
                max_tokens=250
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I'm sorry, I am currently unable to process your request due to an error: {str(e)}"

    @staticmethod
    def get_prescription_explanation(prescription_context):
        """
        Generates a structured comprehensive explanation for a specific prescription.
        Used by Doctor and Pharmacist dashboards.
        """
        try:
            client = AIService.get_client()
            
            system_prompt = f"""
            You are an AI Medical Assistant generating a concise summary for a healthcare professional or patient dashboard.
            Analyze the following prescription context and provide a structured explanation.
            
            PRESCRIPTION CONTEXT:
            {prescription_context}
            
            Format your response exactly as follows using Markdown:
            
            **Medicine Purpose:** [Brief explanation of what the medicines are for]
            **Dosage Instructions:** [Summary of how and when to take them]
            **Common Side Effects:** [List 2-3 common side effects]
            **Serious Side Effects:** [List warning signs to look out for]
            **Interactions & Precautions:** [Any food/drug interactions or general advice]
            
            ALWAYS end your response with: "This information is for educational purposes only. Consult your doctor or pharmacist before making medical decisions."
            """

            if not client:
                return AIService._get_mock_response(system_prompt, "")

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Please generate the structured explanation."}
                ],
                temperature=0.2, 
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Unable to generate AI explanation: {str(e)}"
